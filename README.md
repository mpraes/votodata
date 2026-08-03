# VotoData

Plataforma de engenharia de dados para o domínio político-eleitoral brasileiro (foco Eleições 2026), operando em homelab com pipelines de metadados, ingestão de fontes oficiais e, no futuro, camada analítica e BI.

Visão de produto e macroprocessos: [docs/visao_geral.md](docs/visao_geral.md)  
Arquitetura-alvo (Prefect, MinIO, PostgreSQL, Metabase): [docs/arquitetura.md](docs/arquitetura.md)

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [Visão geral](docs/visao_geral.md) | Objetivos, Living Data Platform, macroprocessos |
| [Arquitetura](docs/arquitetura.md) | Fluxo bronze/silver/gold, orquestração e serving |
| [Catálogo de fontes](docs/catalogo_fontes_dados.md) | TSE, Transparência, APIs e notícias (prioridades) |
| [Operações / cadência](docs/operacoes_pipelines.md) | Tempo real, diário, semanal, batch |
| [Governança e linhagem](docs/governanca_linhagem_qualidade.md) | DQ, quarentena, atributos de auditoria |
| [Segurança](docs/seguranca_e_gerenciamento.md) | Acesso, secrets, gestão do ambiente |
| [Hardware / homelab](docs/hardware_homelab.md) | Capacidade e restrições do lab |
| [Links úteis](docs/links.md) | Portal Dados Abertos do TSE |

## O que já foi feito

### Pipeline de metadados do TSE (`src/etl/metadados_tse/`)

Primeiro ETL entregue: catalogação dos **~172 datasets** do [Dados Abertos do TSE](https://dadosabertos.tse.jus.br/dataset/) no schema PostgreSQL `dados_tse`.

Fluxo:

```text
inventário local → API CKAN (package_show)
                 → HTML fallback (Informações Adicionais, se faltar campo)
                 → transform (4 categorias de metadados)
                 → validate (DQ: WARN vs isolamento de ERROR)
                 → out/{slug}.json
                 → load Postgres (UPSERT; no-op se metadata_hash igual)
```

| Peça | Papel |
| --- | --- |
| `extract_api.py` / `extract_html.py` | Extração híbrida |
| `transform.py` | Negócio, técnico, operacional, referência + `extras_nao_mapeados` |
| `validate.py` | Qualidade antes de persistir |
| `persist_local.py` | Snapshot em `out/` (gitignored) |
| `load_pg.py` | Carga idempotente + `pipeline_run` / `pipeline_log` |
| `sql/001_dados_tse_metadados.sql` | DDL (`dataset`, metas 1:1, `recurso`, `recurso_coluna`, auditoria) |
| `Makefile` | Atalhos (`check-conn`, `extract-meta`, `load-meta`, smokes) |

Validação operacional já executada: extract `ok=172 fail=0`; load `ok=171 skipped=1` (hash no-op no dataset piloto).

Alinha com [governança/linhagem](docs/governanca_linhagem_qualidade.md) (origem, run_id, datas) e com a fonte primária do [catálogo](docs/catalogo_fontes_dados.md).

### Tooling e governança de repo

- Python com **uv** na raiz (`pyproject.toml` / `uv.lock`)
- `.env` local (não versionado); template em `.env.example`
- Branch `main` protegida por ruleset GitHub (merge via pull request)

## Setup rápido

Requisitos: Python 3.12+, [uv](https://github.com/astral-sh/uv), Postgres acessível (homelab), `make`, `psql` (opcional para DDL manual).

```bash
git clone git@github.com:mpraes/votodata.git
cd votodata
uv sync
cp .env.example .env   # preencha DATABASE_URL apontando ao Postgres do lab
```

Aplique o schema (se ainda não aplicado):

```bash
set -a && source .env && set +a
make ddl
# ou: psql "$DATABASE_URL" -f src/etl/metadados_tse/sql/001_dados_tse_metadados.sql
```

Sanidade:

```bash
make check-conn      # Postgres + API TSE
make smoke-models
make extract-meta ARGS="--name candidatos-2026"
make load-meta ARGS="--name candidatos-2026"
```

Catálogo completo:

```bash
make extract-meta    # gera JSON em src/etl/metadados_tse/out/
make load-meta       # upsert em dados_tse
```

## Estrutura relevante

```text
votodata/
├── docs/                          # documentação de produto e operação
├── src/etl/metadados_tse/         # ETL de metadados TSE (entregue)
│   ├── sql/001_dados_tse_metadados.sql
│   ├── tse_datasets_inventory.json
│   ├── tse_download_manifest.jsonl
│   └── out/                       # artefatos gerados (ignorados no git)
├── Makefile
├── pyproject.toml
└── .env.example
```

## O que falta (próximos passos)

Ordenado do mais próximo ao roadmap da [arquitetura](docs/arquitetura.md):

1. **Download dos recursos TSE** — baixar ZIPs/CSVs do manifest; preencher `recurso.hash_conteudo` e `status_link` (HEAD/ETag/404).
2. **Dicionário de colunas** — popular `recurso_coluna` a partir de schema CKAN ou amostra dos CSVs (hoje a tabela existe; na maioria dos datasets a API não envia schema).
3. **Camada bronze (MinIO)** — ingestão bruta dos arquivos no data lake, conforme [arquitetura](docs/arquitetura.md).
4. **Silver / DQ de conteúdo** — Polars/DuckDB, regras de completude/unicidade, quarentena ([governança](docs/governanca_linhagem_qualidade.md)).
5. **Gold + Metabase** — modelos analíticos e dashboards.
6. **Orquestração Prefect** — agendar `extract`/`load` e futuros pipes ([operações](docs/operacoes_pipelines.md)).
7. **Outras fontes** — Transparência, Compras.gov, APIs legislativas, notícias ([catálogo](docs/catalogo_fontes_dados.md)).
8. **Acesso remoto** — Tailscale/Ngrok e hardening ([segurança](docs/seguranca_e_gerenciamento.md)).

Fora do escopo do MVP de metadados (e ainda não iniciado): frontend embutível, NLP/ML sobre notícias.

## Fluxo de contribuição

`main` só recebe mudanças via PR. Exemplo:

```bash
git checkout -b feat/nome-curto
# ... commits ...
git push -u origin HEAD
gh pr create --base main --fill
```
