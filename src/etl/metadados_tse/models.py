from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RecursoColuna(BaseModel):
    nome_coluna: str
    tipo_dado_declarado: str | None = None
    descricao: str | None = None
    ordem: int = 0


class Recurso(BaseModel):
    id: UUID
    nome: str | None = None
    formato: str | None = None
    mimetype: str | None = None
    url: str
    tamanho_bytes: int | None = None
    posicao: int | None = None
    hash_conteudo: str | None = None
    status_link: str = "active"
    created_at_origem: datetime | None = None
    last_modified_origem: datetime | None = None
    colunas: list[RecursoColuna] = Field(default_factory=list)


class DatasetCore(BaseModel):
    id: UUID
    name: str
    titulo: str
    estado: str | None = None
    num_resources: int | None = None
    metadata_hash: str | None = None


class MetaNegocio(BaseModel):
    descricao: str | None = None
    area_gestora: str | None = None
    escopo_geopolitico: str | None = None
    contato: str | None = None
    extras_nao_mapeados: dict[str, Any] = Field(default_factory=dict)


class MetaTecnico(BaseModel):
    url_portal: str
    url_api_package: str
    origem_sistemas: str | None = None
    license_id: str | None = None
    license_title: str | None = None
    fonte_extracao: Literal["api", "api+html"]
    html_fallback_usado: bool = False


class MetaOperacional(BaseModel):
    criado_em: datetime | None = None
    modificado_em: datetime | None = None
    extracao_dados: str | None = None
    frequencia_atualizacao: str | None = None
    coletado_em: datetime


class MetaReferencia(BaseModel):
    organizacao: str | None = None
    org_name: str | None = None
    groups: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class DqInfo(BaseModel):
    status: Literal["ok", "warn", "error"] = "ok"
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DatasetRecord(BaseModel):
    dataset: DatasetCore
    negocio: MetaNegocio
    tecnico: MetaTecnico
    operacional: MetaOperacional
    referencia: MetaReferencia
    recursos: list[Recurso] = Field(default_factory=list)
    dq: DqInfo = Field(default_factory=DqInfo)


class ValidationResult(BaseModel):
    ok_to_persist: bool
    dq: DqInfo