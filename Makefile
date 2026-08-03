.PHONY: help smoke-models ddl check-conn smoke-api smoke-transform smoke-validate smoke-persist extract-meta load-meta

PYTHON := uv run python
PIPE   := src/etl/metadados_tse

help:
	@echo "smoke-models  - valida import dos models Pydantic"
	@echo "ddl           - aplica DDL dados_tse no Postgres"
	@echo "extract-meta  - extrai metadados TSE (use ARGS='--limit 5')"
	@echo "load-meta     - carrega out/ no Postgres"
	@echo "smoke-api     - valida API real com 1 dataset sem montar o ETL inteiro"
	@echo "smoke-transform - valida transformação de dados"
	@echo "smoke-validate  - valida validação de dados"
	@echo "smoke-persist   - valida persistência de dados"
	@echo "smoke-html      - valida extração de informações adicionais"
	@echo "extract-meta    - extrai metadados TSE (use ARGS='--limit 5')"
	@echo "load-meta       - carrega out/ no Postgres"

check-conn:
	@set -a && . ./.env && set +a && \
	$(PYTHON) -c "import os, psycopg; \
url=os.environ['DATABASE_URL']; \
conn=psycopg.connect(url); \
cur=conn.execute('select current_database(), current_user, count(*) from information_schema.schemata where schema_name=%s', ('dados_tse',)); \
print('postgres:', cur.fetchone()); conn.close()" && \
	$(PYTHON) -c "import os, requests; \
base=os.environ.get('TSE_BASE_URL','https://dadosabertos.tse.jus.br').rstrip('/'); \
r=requests.get(base+'/api/3/action/status_show', timeout=20); \
r.raise_for_status(); print('tse api:', r.json().get('success'))"

# Por quê: garante que models.py e deps estão ok sem rodar o ETL inteiro
smoke-models:
	cd $(PIPE) && uv run --project ../.. python -c "from models import DatasetRecord; print('ok')"

# Por quê: aplica schema sem decorar o DATABASE_URL na mão
ddl:
	psql "$$DATABASE_URL" -f $(PIPE)/sql/001_dados_tse_metadados.sql

# Placeholders — preenchidos quando cli.py existir
extract-meta:
	cd $(PIPE) && uv run --project ../.. python cli.py extract $(ARGS)

load-meta:
	set -a && . ./.env && set +a && cd $(PIPE) && uv run --project ../.. python cli.py load $(ARGS)

# Por quê: valida API real com 1 dataset sem montar o ETL inteiro
smoke-api:
	cd $(PIPE) && uv run --project ../.. python -c "from extract_api import package_show, extras_as_dict; p=package_show('candidatos-2026'); e=extras_as_dict(p); print(p['name'], p['title']); print('extras:', sorted(e.keys()))"

smoke-transform:
	cd $(PIPE) && uv run --project ../.. python -c "from extract_api import package_show; from transform import transform_package; r=transform_package(package_show('candidatos-2026')); print(r.dataset.name, r.negocio.area_gestora, r.operacional.frequencia_atualizacao); print('hash', r.dataset.metadata_hash); print('recursos', len(r.recursos)); print('extras', r.negocio.extras_nao_mapeados)"

smoke-validate:
	cd $(PIPE) && uv run --project ../.. python -c "from extract_api import package_show; from transform import transform_package; from validate import apply_validation; r=transform_package(package_show('candidatos-2026')); v=apply_validation(r); print(v.ok_to_persist, v.dq.status, v.dq.warnings, v.dq.errors)"

smoke-persist:
	cd $(PIPE) && uv run --project ../.. python -c "from extract_api import package_show; from transform import transform_package; from validate import apply_validation; from persist_local import save_dataset, load_dataset; r=transform_package(package_show('candidatos-2026')); apply_validation(r); p=save_dataset(r); print(p); print(load_dataset('candidatos-2026').dataset.metadata_hash)"

smoke-html:
	cd $(PIPE) && uv run --project ../.. python -c "from extract_html import scrape_informacoes_adicionais; d=scrape_informacoes_adicionais('candidatos-2026'); print(sorted(d.keys())); print(d.get('Área Gestora'), d.get('Escopo Geopolítico'))"