CREATE SCHEMA IF NOT EXISTS dados_tse;

CREATE TABLE IF NOT EXISTS dados_tse.dataset (
  id              UUID PRIMARY KEY,              -- CKAN package id
  name            TEXT NOT NULL UNIQUE,          -- slug
  titulo          TEXT NOT NULL,
  estado          TEXT,                          -- active, etc.
  num_resources   INTEGER,
  metadata_hash   TEXT,                          -- SHA-256 do payload canônico
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 1. Negócio
CREATE TABLE IF NOT EXISTS dados_tse.meta_negocio (
  dataset_id           UUID PRIMARY KEY REFERENCES dados_tse.dataset(id) ON DELETE CASCADE,
  descricao            TEXT,
  area_gestora         TEXT,
  escopo_geopolitico   TEXT,
  contato              TEXT,
  extras_nao_mapeados  JSONB NOT NULL DEFAULT '{}'::jsonb  -- resiliência a novos atributos TSE
);

-- 2. Técnico (estrutura/origem do dataset — NÃO é log do pipeline)
CREATE TABLE IF NOT EXISTS dados_tse.meta_tecnico (
  dataset_id           UUID PRIMARY KEY REFERENCES dados_tse.dataset(id) ON DELETE CASCADE,
  url_portal           TEXT NOT NULL,
  url_api_package      TEXT NOT NULL,
  origem_sistemas      TEXT,
  license_id           TEXT,
  license_title        TEXT,
  fonte_extracao       TEXT NOT NULL,            -- 'api' | 'api+html'
  html_fallback_usado  BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dados_tse.recurso (
  id                   UUID PRIMARY KEY,         -- CKAN resource id
  dataset_id           UUID NOT NULL REFERENCES dados_tse.dataset(id) ON DELETE CASCADE,
  nome                 TEXT,
  formato              TEXT,
  mimetype             TEXT,
  url                  TEXT NOT NULL,
  tamanho_bytes        BIGINT,
  posicao              INTEGER,
  hash_conteudo        TEXT,                     -- MD5/SHA256/ETag do CKAN (rastreio de download futuro)
  status_link          TEXT NOT NULL DEFAULT 'active',  -- active|broken|not_found|unknown
  created_at_origem    TIMESTAMPTZ,
  last_modified_origem TIMESTAMPTZ
);

-- Dicionário de dados (esquema das colunas do arquivo) — prepara ingestão futura de CSVs
CREATE TABLE IF NOT EXISTS dados_tse.recurso_coluna (
  id                   BIGSERIAL PRIMARY KEY,
  recurso_id           UUID NOT NULL REFERENCES dados_tse.recurso(id) ON DELETE CASCADE,
  nome_coluna          TEXT NOT NULL,
  tipo_dado_declarado  TEXT,
  descricao            TEXT,
  ordem                INTEGER NOT NULL DEFAULT 0,
  UNIQUE (recurso_id, nome_coluna)
);

-- 3. Operacional (cadência/datas do TSE no portal)
CREATE TABLE IF NOT EXISTS dados_tse.meta_operacional (
  dataset_id              UUID PRIMARY KEY REFERENCES dados_tse.dataset(id) ON DELETE CASCADE,
  criado_em               TIMESTAMPTZ,           -- metadata_created / "Criado"
  modificado_em           TIMESTAMPTZ,           -- metadata_modified
  extracao_dados          TEXT,                  -- texto do portal
  frequencia_atualizacao  TEXT,
  coletado_em             TIMESTAMPTZ NOT NULL   -- quando o ETL capturou este registro
);

-- 4. Referência (taxonomias TSE)
CREATE TABLE IF NOT EXISTS dados_tse.meta_referencia (
  dataset_id     UUID PRIMARY KEY REFERENCES dados_tse.dataset(id) ON DELETE CASCADE,
  organizacao    TEXT,
  org_name       TEXT,
  groups         TEXT[] NOT NULL DEFAULT '{}',
  tags           TEXT[] NOT NULL DEFAULT '{}'
);

-- Auditoria do ETL (runs/logs — separados dos metadados técnicos do dataset)
CREATE TABLE IF NOT EXISTS dados_tse.pipeline_run (
  run_id         UUID PRIMARY KEY,
  pipeline_name  TEXT NOT NULL DEFAULT 'metadados_tse',
  stage          TEXT NOT NULL,                  -- 'extract' | 'load'
  started_at     TIMESTAMPTZ NOT NULL,
  finished_at    TIMESTAMPTZ,
  status         TEXT NOT NULL,                  -- running|success|failed|partial
  datasets_ok    INTEGER NOT NULL DEFAULT 0,
  datasets_fail  INTEGER NOT NULL DEFAULT 0,
  datasets_skipped INTEGER NOT NULL DEFAULT 0,  -- load no-op por hash igual
  message        TEXT
);

CREATE TABLE IF NOT EXISTS dados_tse.pipeline_log (
  id             BIGSERIAL PRIMARY KEY,
  run_id         UUID NOT NULL REFERENCES dados_tse.pipeline_run(run_id) ON DELETE CASCADE,
  logged_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  level          TEXT NOT NULL DEFAULT 'INFO',   -- INFO|WARN|ERROR
  dataset_name   TEXT,
  message        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_recurso_dataset ON dados_tse.recurso(dataset_id);
CREATE INDEX IF NOT EXISTS ix_recurso_coluna_recurso ON dados_tse.recurso_coluna(recurso_id);
CREATE INDEX IF NOT EXISTS ix_pipeline_log_run ON dados_tse.pipeline_log(run_id);
CREATE INDEX IF NOT EXISTS ix_meta_negocio_extras_gin
  ON dados_tse.meta_negocio USING GIN (extras_nao_mapeados);