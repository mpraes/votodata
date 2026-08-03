from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from config import DATABASE_URL, OUT_DIR
from models import DatasetRecord
from persist_local import load_dataset


def _conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definido")
    return psycopg.connect(DATABASE_URL)


def _log(cur, run_id: uuid.UUID, level: str, message: str, dataset_name: str | None = None) -> None:
    cur.execute(
        """
        INSERT INTO dados_tse.pipeline_log (run_id, level, dataset_name, message)
        VALUES (%s, %s, %s, %s)
        """,
        (str(run_id), level, dataset_name, message),
    )


def _get_hash(cur, dataset_id: uuid.UUID) -> str | None:
    cur.execute("SELECT metadata_hash FROM dados_tse.dataset WHERE id = %s", (str(dataset_id),))
    row = cur.fetchone()
    return row[0] if row else None


def upsert_dataset(cur, record: DatasetRecord) -> None:
    d = record.dataset
    cur.execute(
        """
        INSERT INTO dados_tse.dataset (id, name, titulo, estado, num_resources, metadata_hash, ingested_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, now(), now())
        ON CONFLICT (id) DO UPDATE SET
          name = EXCLUDED.name,
          titulo = EXCLUDED.titulo,
          estado = EXCLUDED.estado,
          num_resources = EXCLUDED.num_resources,
          metadata_hash = EXCLUDED.metadata_hash,
          updated_at = now()
        """,
        (str(d.id), d.name, d.titulo, d.estado, d.num_resources, d.metadata_hash),
    )

    n = record.negocio
    cur.execute(
        """
        INSERT INTO dados_tse.meta_negocio
          (dataset_id, descricao, area_gestora, escopo_geopolitico, contato, extras_nao_mapeados)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (dataset_id) DO UPDATE SET
          descricao = EXCLUDED.descricao,
          area_gestora = EXCLUDED.area_gestora,
          escopo_geopolitico = EXCLUDED.escopo_geopolitico,
          contato = EXCLUDED.contato,
          extras_nao_mapeados = EXCLUDED.extras_nao_mapeados
        """,
        (str(d.id), n.descricao, n.area_gestora, n.escopo_geopolitico, n.contato, Jsonb(n.extras_nao_mapeados)),
    )

    t = record.tecnico
    cur.execute(
        """
        INSERT INTO dados_tse.meta_tecnico
          (dataset_id, url_portal, url_api_package, origem_sistemas, license_id, license_title,
           fonte_extracao, html_fallback_usado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (dataset_id) DO UPDATE SET
          url_portal = EXCLUDED.url_portal,
          url_api_package = EXCLUDED.url_api_package,
          origem_sistemas = EXCLUDED.origem_sistemas,
          license_id = EXCLUDED.license_id,
          license_title = EXCLUDED.license_title,
          fonte_extracao = EXCLUDED.fonte_extracao,
          html_fallback_usado = EXCLUDED.html_fallback_usado
        """,
        (
            str(d.id), t.url_portal, t.url_api_package, t.origem_sistemas,
            t.license_id, t.license_title, t.fonte_extracao, t.html_fallback_usado,
        ),
    )

    o = record.operacional
    cur.execute(
        """
        INSERT INTO dados_tse.meta_operacional
          (dataset_id, criado_em, modificado_em, extracao_dados, frequencia_atualizacao, coletado_em)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (dataset_id) DO UPDATE SET
          criado_em = EXCLUDED.criado_em,
          modificado_em = EXCLUDED.modificado_em,
          extracao_dados = EXCLUDED.extracao_dados,
          frequencia_atualizacao = EXCLUDED.frequencia_atualizacao,
          coletado_em = EXCLUDED.coletado_em
        """,
        (str(d.id), o.criado_em, o.modificado_em, o.extracao_dados, o.frequencia_atualizacao, o.coletado_em),
    )

    r = record.referencia
    cur.execute(
        """
        INSERT INTO dados_tse.meta_referencia (dataset_id, organizacao, org_name, groups, tags)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (dataset_id) DO UPDATE SET
          organizacao = EXCLUDED.organizacao,
          org_name = EXCLUDED.org_name,
          groups = EXCLUDED.groups,
          tags = EXCLUDED.tags
        """,
        (str(d.id), r.organizacao, r.org_name, r.groups, r.tags),
    )

    # snapshot: apaga recursos (cascade limpa colunas) e reinsere
    cur.execute("DELETE FROM dados_tse.recurso WHERE dataset_id = %s", (str(d.id),))
    for rec in record.recursos:
        cur.execute(
            """
            INSERT INTO dados_tse.recurso
              (id, dataset_id, nome, formato, mimetype, url, tamanho_bytes, posicao,
               hash_conteudo, status_link, created_at_origem, last_modified_origem)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(rec.id), str(d.id), rec.nome, rec.formato, rec.mimetype, rec.url,
                rec.tamanho_bytes, rec.posicao, rec.hash_conteudo, rec.status_link,
                rec.created_at_origem, rec.last_modified_origem,
            ),
        )
        for col in rec.colunas:
            cur.execute(
                """
                INSERT INTO dados_tse.recurso_coluna
                  (recurso_id, nome_coluna, tipo_dado_declarado, descricao, ordem)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (recurso_id, nome_coluna) DO UPDATE SET
                  tipo_dado_declarado = EXCLUDED.tipo_dado_declarado,
                  descricao = EXCLUDED.descricao,
                  ordem = EXCLUDED.ordem
                """,
                (str(rec.id), col.nome_coluna, col.tipo_dado_declarado, col.descricao, col.ordem),
            )


def load_from_out(*, name: str | None = None) -> dict:
    """Carrega JSON(s) de out/ no Postgres. Retorna contadores."""
    run_id = uuid.uuid4()
    started = datetime.now(timezone.utc)
    ok = fail = skipped = 0

    files: list[Path]
    if name:
        files = [OUT_DIR / f"{name}.json"]
    else:
        files = sorted(OUT_DIR.glob("*.json"))

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dados_tse.pipeline_run
                  (run_id, stage, started_at, status)
                VALUES (%s, 'load', %s, 'running')
                """,
                (str(run_id), started),
            )

            for path in files:
                if not path.exists():
                    fail += 1
                    _log(cur, run_id, "ERROR", f"arquivo ausente: {path}", name)
                    continue
                try:
                    record = DatasetRecord.model_validate_json(path.read_text(encoding="utf-8"))
                    current = _get_hash(cur, record.dataset.id)
                    if current and current == record.dataset.metadata_hash:
                        skipped += 1
                        _log(cur, run_id, "INFO", "skipped unchanged", record.dataset.name)
                        continue
                    upsert_dataset(cur, record)
                    ok += 1
                    _log(cur, run_id, "INFO", "upserted", record.dataset.name)
                except Exception as exc:  # noqa: BLE001
                    fail += 1
                    _log(cur, run_id, "ERROR", str(exc), path.stem)

            status = "success" if fail == 0 else ("partial" if ok or skipped else "failed")
            cur.execute(
                """
                UPDATE dados_tse.pipeline_run
                SET finished_at = %s, status = %s,
                    datasets_ok = %s, datasets_fail = %s, datasets_skipped = %s
                WHERE run_id = %s
                """,
                (datetime.now(timezone.utc), status, ok, fail, skipped, str(run_id)),
            )
        conn.commit()

    return {"run_id": str(run_id), "ok": ok, "fail": fail, "skipped": skipped, "status": status}