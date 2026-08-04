from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import requests
import psycopg

from config import DATABASE_URL, PROBE_SLEEP_SECONDS


def _conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definido")
    return psycopg.connect(DATABASE_URL)


def _status_from_code(code: int) -> str:
    if code in (200, 206):
        return "active"
    if code == 404:
        return "not_found"
    if 400 <= code < 600:
        return "broken"
    return "unknown"


def _probe_one(session: requests.Session, url: str) -> tuple[str, int | None, str | None, str]:
    """Retorna (status_link, tamanho_bytes, etag, detail)."""
    try:
        resp = session.head(url, timeout=30, allow_redirects=True)
        # Alguns CDNs não gostam de HEAD
        if resp.status_code in (405, 501) or (resp.status_code == 403 and not resp.headers.get("Content-Length")):
            resp = session.get(url, timeout=30, stream=True, allow_redirects=True)
            resp.close()
        status = _status_from_code(resp.status_code)
        length = resp.headers.get("Content-Length")
        tamanho = int(length) if length and length.isdigit() else None
        etag = resp.headers.get("ETag")
        if etag:
            etag = etag.strip()
        return status, tamanho, etag, f"http {resp.status_code}"
    except requests.RequestException as exc:
        return "unknown", None, None, str(exc)

def _normalize_url(url: str) -> str:
    u = (url or "").strip()
    if u.lower().startswith("url:"):
        u = u.split(":", 1)[1].strip()
    return u

def probe_resources(*, dataset_name: str | None = None, limit: int | None = None) -> dict:
    run_id = uuid.uuid4()
    started = datetime.now(timezone.utc)
    ok = fail = skipped = 0
    session = requests.Session()
    session.headers.update({"User-Agent": "votodata-metadados-tse/0.1"})

    sql = """
        SELECT r.id, r.url, d.name
        FROM dados_tse.recurso r
        JOIN dados_tse.dataset d ON d.id = r.dataset_id
    """
    params: list = []
    if dataset_name:
        sql += " WHERE d.name = %s"
        params.append(dataset_name)
    sql += " ORDER BY d.name, r.posicao NULLS LAST, r.id"
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dados_tse.pipeline_run (run_id, stage, started_at, status)
                VALUES (%s, 'probe', %s, 'running')
                """,
                (str(run_id), started),
            )
            cur.execute(sql, params)
            rows = cur.fetchall()

            for recurso_id, url, name in rows:
                status, tamanho, etag, detail = _probe_one(session, url)
                try:
                    cur.execute(
                        """
                        UPDATE dados_tse.recurso
                        SET status_link = %s,
                            tamanho_bytes = COALESCE(%s, tamanho_bytes),
                            etag = COALESCE(%s, etag),
                            last_probed_at = now()
                        WHERE id = %s
                        """,
                        (status, tamanho, etag, str(recurso_id)),
                    )
                    level = "INFO" if status == "active" else "WARN"
                    cur.execute(
                        """
                        INSERT INTO dados_tse.pipeline_log (run_id, level, dataset_name, message)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (str(run_id), level, name, f"{recurso_id} {status} {detail}"),
                    )
                    if status == "active":
                        ok += 1
                    else:
                        fail += 1
                except Exception as exc:  # noqa: BLE001
                    fail += 1
                    cur.execute(
                        """
                        INSERT INTO dados_tse.pipeline_log (run_id, level, dataset_name, message)
                        VALUES (%s, 'ERROR', %s, %s)
                        """,
                        (str(run_id), name, str(exc)),
                    )
                time.sleep(PROBE_SLEEP_SECONDS)

            status_run = "success" if fail == 0 else ("partial" if ok else "failed")
            cur.execute(
                """
                UPDATE dados_tse.pipeline_run
                SET finished_at = %s, status = %s,
                    datasets_ok = %s, datasets_fail = %s, datasets_skipped = %s
                WHERE run_id = %s
                """,
                (datetime.now(timezone.utc), status_run, ok, fail, skipped, str(run_id)),
            )
        conn.commit()

    return {"run_id": str(run_id), "ok": ok, "fail": fail, "skipped": skipped, "status": status_run}