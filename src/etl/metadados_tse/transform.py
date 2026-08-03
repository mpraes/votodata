from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from config import TSE_BASE_URL
from extract_api import extras_as_dict
from models import (
    DatasetCore,
    DatasetRecord,
    MetaNegocio,
    MetaOperacional,
    MetaReferencia,
    MetaTecnico,
    Recurso,
    RecursoColuna,
)

# label normalizado -> (secao, campo)
# Por quê: de/para explícito; o que sobrar vira extras_nao_mapeados
CAMPO_MAP: dict[str, tuple[str, str]] = {
    "contato para duvidas/sugestoes": ("negocio", "contato"),
    "escopo geopolitico": ("negocio", "escopo_geopolitico"),
    "area gestora": ("negocio", "area_gestora"),
    "extracao dos dados": ("operacional", "extracao_dados"),
    "frequencia de atualizacao": ("operacional", "frequencia_atualizacao"),
    "criado": ("operacional", "criado_em"),  # HTML; na API usamos metadata_created
}


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize_label(label: str) -> str:
    return " ".join(_strip_accents(label).casefold().split())


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    # CKAN: 2026-07-22T16:34:34.019655
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _map_extras(extras: dict[str, str]) -> tuple[dict[str, str], dict[str, str], dict[str, Any]]:
    negocio: dict[str, str] = {}
    operacional: dict[str, str] = {}
    nao_mapeados: dict[str, Any] = {}
    for key, value in extras.items():
        target = CAMPO_MAP.get(normalize_label(key))
        if not target:
            nao_mapeados[key] = value
            continue
        secao, campo = target
        if secao == "negocio":
            negocio[campo] = value
        else:
            operacional[campo] = value
    return negocio, operacional, nao_mapeados


def _parse_recursos(package: dict[str, Any]) -> list[Recurso]:
    recursos: list[Recurso] = []
    for r in package.get("resources") or []:
        if not r.get("id") or not r.get("url"):
            continue
        colunas: list[RecursoColuna] = []
        schema = r.get("schema") or {}
        fields = schema.get("fields") if isinstance(schema, dict) else None
        if fields:
            for i, f in enumerate(fields):
                colunas.append(
                    RecursoColuna(
                        nome_coluna=str(f.get("name") or f.get("id") or f"col_{i}"),
                        tipo_dado_declarado=f.get("type"),
                        descricao=f.get("info", {}).get("label") if isinstance(f.get("info"), dict) else None,
                        ordem=i,
                    )
                )
        recursos.append(
            Recurso(
                id=UUID(str(r["id"])),
                nome=r.get("name"),
                formato=r.get("format"),
                mimetype=r.get("mimetype"),
                url=r["url"],
                tamanho_bytes=r.get("size"),
                posicao=r.get("position"),
                hash_conteudo=(r.get("hash") or None) or None,
                status_link="active",
                created_at_origem=parse_dt(r.get("created")),
                last_modified_origem=parse_dt(r.get("last_modified") or r.get("metadata_modified")),
                colunas=colunas,
            )
        )
    return recursos


def compute_metadata_hash(record: DatasetRecord) -> str:
    """
    SHA-256 canônico excluindo campos voláteis.
    Por quê: re-extract no mesmo conteúdo do portal => mesmo hash => load no-op.
    """
    payload = record.model_dump(mode="json")
    payload.get("dataset", {}).pop("metadata_hash", None)
    payload.pop("dq", None)
    if "operacional" in payload:
        payload["operacional"].pop("coletado_em", None)
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def transform_package(
    package: dict[str, Any],
    *,
    html_fields: dict[str, str] | None = None,
) -> DatasetRecord:
    """Converte package_show (+ opcional HTML) em DatasetRecord."""
    name = package["name"]
    extras = extras_as_dict(package)
    if html_fields:
        # HTML preenche só o que a API não trouxe
        for k, v in html_fields.items():
            if k not in extras or not extras[k]:
                extras[k] = v

    neg, ope, nao_mapeados = _map_extras(extras)
    org = package.get("organization") or {}
    html_used = bool(html_fields)
    now = datetime.now(timezone.utc)

    record = DatasetRecord(
        dataset=DatasetCore(
            id=UUID(str(package["id"])),
            name=name,
            titulo=package.get("title") or name,
            estado=package.get("state"),
            num_resources=package.get("num_resources"),
        ),
        negocio=MetaNegocio(
            descricao=package.get("notes"),
            area_gestora=neg.get("area_gestora"),
            escopo_geopolitico=neg.get("escopo_geopolitico"),
            contato=neg.get("contato"),
            extras_nao_mapeados=nao_mapeados,
        ),
        tecnico=MetaTecnico(
            url_portal=f"{TSE_BASE_URL}/dataset/{name}",
            url_api_package=f"{TSE_BASE_URL}/api/3/action/package_show?id={name}",
            origem_sistemas=package.get("url") or None,
            license_id=package.get("license_id"),
            license_title=package.get("license_title"),
            fonte_extracao="api+html" if html_used else "api",
            html_fallback_usado=html_used,
        ),
        operacional=MetaOperacional(
            criado_em=parse_dt(package.get("metadata_created")) or parse_dt(ope.get("criado_em")),
            modificado_em=parse_dt(package.get("metadata_modified")),
            extracao_dados=ope.get("extracao_dados"),
            frequencia_atualizacao=ope.get("frequencia_atualizacao"),
            coletado_em=now,
        ),
        referencia=MetaReferencia(
            organizacao=org.get("title"),
            org_name=org.get("name"),
            groups=[g.get("name") for g in (package.get("groups") or []) if g.get("name")],
            tags=[t.get("name") for t in (package.get("tags") or []) if t.get("name")],
        ),
        recursos=_parse_recursos(package),
    )
    record.dataset.metadata_hash = compute_metadata_hash(record)
    return record