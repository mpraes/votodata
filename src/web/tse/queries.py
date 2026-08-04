from __future__ import annotations

from db import fetch_all, fetch_one
from config import PRIORITY_DATASETS


def get_summary() -> dict:
    counts = fetch_one(
        """
        SELECT
          (SELECT count(*)::int FROM dados_tse.dataset) AS datasets,
          (SELECT count(*)::int FROM dados_tse.recurso) AS resources,
          (SELECT count(*)::int FROM dados_tse.recurso_coluna) AS columns,
          (SELECT count(*)::int FROM dados_tse.recurso
           WHERE hash_conteudo LIKE 'sha256:%%') AS resources_with_sha
        """
    ) or {}

    frequencies = fetch_all(
        """
        SELECT coalesce(frequencia_atualizacao, '(não informado)') AS label,
               count(*)::int AS count
        FROM dados_tse.meta_operacional
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )
    areas = fetch_all(
        """
        SELECT coalesce(area_gestora, '(não informado)') AS label,
               count(*)::int AS count
        FROM dados_tse.meta_negocio
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )
    status_links = fetch_all(
        """
        SELECT status_link AS label, count(*)::int AS count
        FROM dados_tse.recurso
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )
    last_runs = fetch_all(
        """
        SELECT run_id::text, stage, status, started_at, finished_at,
               datasets_ok, datasets_fail, datasets_skipped
        FROM dados_tse.pipeline_run
        ORDER BY started_at DESC
        LIMIT 5
        """
    )
    priorities = fetch_all(
        """
        SELECT d.name, d.titulo,
               d.num_resources,
               (SELECT count(*)::int FROM dados_tse.recurso r
                WHERE r.dataset_id = d.id AND r.hash_conteudo LIKE 'sha256:%%') AS with_sha
        FROM dados_tse.dataset d
        WHERE d.name = ANY(%s)
        ORDER BY d.name
        """,
        (list(PRIORITY_DATASETS),),
    )
    return {
        "counts": counts,
        "frequencies": frequencies,
        "areas": areas,
        "status_links": status_links,
        "last_runs": last_runs,
        "priorities": priorities,
    }


def list_groups() -> list[dict]:
    return fetch_all(
        """
        SELECT g AS slug, count(*)::int AS dataset_count
        FROM dados_tse.meta_referencia, unnest(groups) AS g
        GROUP BY g
        ORDER BY dataset_count DESC, g
        """
    )


def list_datasets(
    *,
    group: str | None = None,
    q: str | None = None,
    frequency: str | None = None,
) -> list[dict]:
    clauses: list[str] = ["TRUE"]
    params: list = []

    if group:
        clauses.append("%s = ANY(r.groups)")
        params.append(group)
    if q:
        clauses.append("(d.name ILIKE %s OR d.titulo ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    if frequency:
        clauses.append("o.frequencia_atualizacao = %s")
        params.append(frequency)

    where = " AND ".join(clauses)
    return fetch_all(
        f"""
        SELECT d.name, d.titulo, d.num_resources, d.estado,
               o.frequencia_atualizacao,
               n.area_gestora,
               r.groups,
               (SELECT count(*)::int FROM dados_tse.recurso res
                WHERE res.dataset_id = d.id AND res.status_link = 'active') AS active_resources,
               (SELECT count(*)::int FROM dados_tse.recurso res
                WHERE res.dataset_id = d.id AND res.hash_conteudo LIKE 'sha256:%%') AS with_sha
        FROM dados_tse.dataset d
        JOIN dados_tse.meta_negocio n ON n.dataset_id = d.id
        JOIN dados_tse.meta_operacional o ON o.dataset_id = d.id
        JOIN dados_tse.meta_referencia r ON r.dataset_id = d.id
        WHERE {where}
        ORDER BY d.name
        """,
        params,
    )


def get_dataset(name: str) -> dict | None:
    return fetch_one(
        """
        SELECT d.id::text, d.name, d.titulo, d.estado, d.num_resources,
               d.metadata_hash, d.ingested_at, d.updated_at,
               n.descricao, n.area_gestora, n.escopo_geopolitico, n.contato,
               n.extras_nao_mapeados,
               t.url_portal, t.url_api_package, t.origem_sistemas,
               t.license_id, t.license_title, t.fonte_extracao, t.html_fallback_usado,
               o.criado_em, o.modificado_em, o.extracao_dados,
               o.frequencia_atualizacao, o.coletado_em,
               r.organizacao, r.org_name, r.groups, r.tags
        FROM dados_tse.dataset d
        JOIN dados_tse.meta_negocio n ON n.dataset_id = d.id
        JOIN dados_tse.meta_tecnico t ON t.dataset_id = d.id
        JOIN dados_tse.meta_operacional o ON o.dataset_id = d.id
        JOIN dados_tse.meta_referencia r ON r.dataset_id = d.id
        WHERE d.name = %s
        """,
        (name,),
    )


def list_resources(dataset_name: str) -> list[dict]:
    return fetch_all(
        """
        SELECT r.id::text, r.nome, r.formato, r.mimetype, r.url,
               r.tamanho_bytes, r.posicao, r.hash_conteudo, r.status_link,
               r.etag, r.last_probed_at, r.last_enriched_at,
               (SELECT count(*)::int FROM dados_tse.recurso_coluna c
                WHERE c.recurso_id = r.id) AS column_count
        FROM dados_tse.recurso r
        JOIN dados_tse.dataset d ON d.id = r.dataset_id
        WHERE d.name = %s
        ORDER BY r.posicao NULLS LAST, r.nome
        """,
        (dataset_name,),
    )


def get_resource(resource_id: str) -> dict | None:
    return fetch_one(
        """
        SELECT r.id::text, r.nome, r.formato, r.mimetype, r.url,
               r.tamanho_bytes, r.posicao, r.hash_conteudo, r.status_link,
               r.etag, r.local_path, r.last_probed_at, r.last_enriched_at,
               r.created_at_origem, r.last_modified_origem,
               d.name AS dataset_name, d.titulo AS dataset_titulo
        FROM dados_tse.recurso r
        JOIN dados_tse.dataset d ON d.id = r.dataset_id
        WHERE r.id = %s::uuid
        """,
        (resource_id,),
    )


def list_columns(resource_id: str) -> list[dict]:
    return fetch_all(
        """
        SELECT ordem, nome_coluna, tipo_dado_declarado, descricao
        FROM dados_tse.recurso_coluna
        WHERE recurso_id = %s::uuid
        ORDER BY ordem, nome_coluna
        """,
        (resource_id,),
    )


def get_health() -> dict:
    status_links = fetch_all(
        """
        SELECT status_link AS label, count(*)::int AS count
        FROM dados_tse.recurso
        GROUP BY 1
        ORDER BY 2 DESC
        """
    )
    problems = fetch_all(
        """
        SELECT d.name AS dataset_name, r.nome AS resource_name,
               r.status_link, r.url, r.id::text AS resource_id
        FROM dados_tse.recurso r
        JOIN dados_tse.dataset d ON d.id = r.dataset_id
        WHERE r.status_link <> 'active'
        ORDER BY r.status_link, d.name, r.nome
        LIMIT 50
        """
    )
    priorities = fetch_all(
        """
        SELECT d.name, d.titulo,
               count(r.*)::int AS resources,
               count(*) FILTER (WHERE r.hash_conteudo LIKE 'sha256:%%')::int AS with_sha
        FROM dados_tse.dataset d
        LEFT JOIN dados_tse.recurso r ON r.dataset_id = d.id
        WHERE d.name = ANY(%s)
        GROUP BY d.id, d.name, d.titulo
        ORDER BY d.name
        """,
        (list(PRIORITY_DATASETS),),
    )
    last_runs = fetch_all(
        """
        SELECT run_id::text, stage, status, started_at, finished_at,
               datasets_ok, datasets_fail, datasets_skipped, message
        FROM dados_tse.pipeline_run
        ORDER BY started_at DESC
        LIMIT 15
        """
    )
    return {
        "status_links": status_links,
        "problems": problems,
        "priorities": priorities,
        "last_runs": last_runs,
    }


def list_frequencies() -> list[str]:
    rows = fetch_all(
        """
        SELECT DISTINCT frequencia_atualizacao AS label
        FROM dados_tse.meta_operacional
        WHERE frequencia_atualizacao IS NOT NULL
        ORDER BY 1
        """
    )
    return [r["label"] for r in rows]
