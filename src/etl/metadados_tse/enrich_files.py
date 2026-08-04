from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import psycopg
import requests

from config import CACHE_DIR, DATABASE_URL, PRIORITY_DATASETS, PROBE_SLEEP_SECONDS
from schema_csv import extract_columns_from_file


def _connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(DATABASE_URL)


def _is_enrichable(formato: str | None, mimetype: str | None, url: str) -> bool:
    fmt = (formato or "").upper()
    path = urlparse(url).path.lower()
    if fmt in {"JPEG", "JPG", "PNG", "PDF", "HTML"}:
        return False
    if any(path.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".pdf", ".html")):
        return False
    return True


def _download(session: requests.Session, url: str, destination: Path, *, retries: int = 3) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            with session.get(url, timeout=(30, 600), stream=True) as response:
                # (30s connect, 600s read) — arquivos grandes do eleitorado
                response.raise_for_status()
                expected = response.headers.get("Content-Length")
                expected_size = int(expected) if expected and expected.isdigit() else None

                tmp = destination.with_suffix(destination.suffix + ".part")
                written = 0
                with tmp.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
                            written += len(chunk)

                if expected_size is not None and written != expected_size:
                    tmp.unlink(missing_ok=True)
                    raise IOError(f"incomplete download: got {written}, expected {expected_size}")

                tmp.replace(destination)
                return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            destination.unlink(missing_ok=True)
            destination.with_suffix(destination.suffix + ".part").unlink(missing_ok=True)
            if attempt < retries:
                time.sleep(2 * attempt)

    raise RuntimeError(f"download failed after {retries} attempts: {last_error}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _normalize_url(url: str) -> str:
    u = (url or "").strip()
    if u.lower().startswith("url:"):
        u = u.split(":", 1)[1].strip()
    return u


def _fetch_resources(cur, dataset_name: str) -> list[tuple]:
    cur.execute(
        """
        SELECT r.id, r.url, r.formato, r.mimetype, r.nome
        FROM dados_tse.recurso r
        JOIN dados_tse.dataset d ON d.id = r.dataset_id
        WHERE d.name = %s
        ORDER BY r.posicao NULLS LAST, r.id
        """,
        (dataset_name,),
    )
    return cur.fetchall()


def _start_run(cur, run_id: uuid.UUID, started_at: datetime) -> None:
    cur.execute(
        """
        INSERT INTO dados_tse.pipeline_run (run_id, stage, started_at, status)
        VALUES (%s, 'enrich_files', %s, 'running')
        """,
        (str(run_id), started_at),
    )


def _finish_run(
    cur,
    run_id: uuid.UUID,
    *,
    status: str,
    ok: int,
    fail: int,
    skipped: int,
) -> None:
    cur.execute(
        """
        UPDATE dados_tse.pipeline_run
        SET finished_at = %s, status = %s,
            datasets_ok = %s, datasets_fail = %s, datasets_skipped = %s
        WHERE run_id = %s
        """,
        (datetime.now(timezone.utc), status, ok, fail, skipped, str(run_id)),
    )


def _log(cur, run_id: uuid.UUID, level: str, dataset_name: str, message: str) -> None:
    cur.execute(
        """
        INSERT INTO dados_tse.pipeline_log (run_id, level, dataset_name, message)
        VALUES (%s, %s, %s, %s)
        """,
        (str(run_id), level, dataset_name, message),
    )


def _persist_enrichment(
    cur,
    *,
    resource_id,
    content_hash: str,
    size_bytes: int,
    local_path: str,
    columns: list,
) -> None:
    cur.execute(
        """
        UPDATE dados_tse.recurso
        SET hash_conteudo = %s,
            tamanho_bytes = %s,
            status_link = 'active',
            local_path = %s,
            url = COALESCE(url, url),  -- replace: set url = %s if you also pass cleaned url
            last_enriched_at = now()
        WHERE id = %s
        """,
        (content_hash, size_bytes, local_path, str(resource_id)),
    )
    # Better UPDATE including cleaned url:
    # SET url = %s, hash_conteudo = %s, ... WHERE id = %s


def _replace_columns(cur, resource_id, columns: list) -> None:
    cur.execute(
        "DELETE FROM dados_tse.recurso_coluna WHERE recurso_id = %s",
        (str(resource_id),),
    )
    for column in columns:
        cur.execute(
            """
            INSERT INTO dados_tse.recurso_coluna
              (recurso_id, nome_coluna, tipo_dado_declarado, descricao, ordem)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(resource_id),
                column.nome_coluna,
                column.tipo_dado_declarado,
                column.descricao,
                column.ordem,
            ),
        )


def _enrich_one_resource(
    cur,
    session: requests.Session,
    *,
    run_id: uuid.UUID,
    dataset_name: str,
    resource_id,
    url: str,
    formato: str | None,
    mimetype: str | None,
    resource_name: str,
) -> str:
    """Returns 'ok' | 'skip' | 'fail'."""
    if not _is_enrichable(formato, mimetype, url):
        return "skip"

    url = _normalize_url(url)
    try:
        destination = CACHE_DIR / dataset_name / f"{resource_id}.bin"
        _download(session, url, destination)
        content_hash = _sha256(destination)
        size_bytes = destination.stat().st_size
        columns = extract_columns_from_file(destination)

        cur.execute(
            """
            UPDATE dados_tse.recurso
            SET url = %s,
                hash_conteudo = %s,
                tamanho_bytes = %s,
                status_link = 'active',
                local_path = %s,
                last_enriched_at = now()
            WHERE id = %s
            """,
            (url, content_hash, size_bytes, str(destination), str(resource_id)),
        )
        _replace_columns(cur, resource_id, columns)
        _log(
            cur,
            run_id,
            "INFO",
            dataset_name,
            f"{resource_name}: sha ok, cols={len(columns)}, size={size_bytes}",
        )
        return "ok"
    except Exception as exc:  # noqa: BLE001
        _log(cur, run_id, "ERROR", dataset_name, f"{resource_name}: {exc}")
        return "fail"


def enrich_files(*, dataset_name: str | None = None) -> dict:
    run_id = uuid.uuid4()
    started_at = datetime.now(timezone.utc)
    ok = fail = skipped = 0
    names = [dataset_name] if dataset_name else list(PRIORITY_DATASETS)

    session = requests.Session()
    session.headers.update({"User-Agent": "votodata-metadata-tse/0.1"})

    with _connect() as conn:
        with conn.cursor() as cur:
            _start_run(cur, run_id, started_at)

            for name in names:
                resources = _fetch_resources(cur, name)
                if not resources:
                    fail += 1
                    _log(cur, run_id, "ERROR", name, "dataset/resources not found in Postgres")
                    continue

                for resource_id, url, formato, mimetype, resource_name in resources:
                    result = _enrich_one_resource(
                        cur,
                        session,
                        run_id=run_id,
                        dataset_name=name,
                        resource_id=resource_id,
                        url=url,
                        formato=formato,
                        mimetype=mimetype,
                        resource_name=resource_name,
                    )
                    if result == "ok":
                        ok += 1
                    elif result == "skip":
                        skipped += 1
                    else:
                        fail += 1
                    time.sleep(PROBE_SLEEP_SECONDS)

            run_status = "success" if fail == 0 else ("partial" if ok else "failed")
            _finish_run(cur, run_id, status=run_status, ok=ok, fail=fail, skipped=skipped)
        conn.commit()

    return {
        "run_id": str(run_id),
        "ok": ok,
        "fail": fail,
        "skipped": skipped,
        "status": run_status,
    }