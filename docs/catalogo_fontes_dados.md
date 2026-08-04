# 5. Matriz de Fontes de Dados e Prioridades Operacionais

Os dados alimentados no VotoData são organizados em três camadas operacionais de prioridade:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. FONTE PRIMÁRIA (Criticidade Alta / Base Oficial)                   │
│    • TSE — portal Dados Abertos (metadados catalogados; dados brutos  │
│      pendentes de download)                                           │
│    • Portal da Transparência e Compras.gov.br                         │
├────────────────────────────────────────────────────────────────────────┤
│ 2. FONTE SECUNDÁRIA (Criticidade Média / Enriquecimento)             │
│    • APIs de Câmaras, Senado e Dados Abertos Governamentais            │
│    • Indicadores Públicos (IBGE, MDHC)                                 │
├────────────────────────────────────────────────────────────────────────┤
│ 3. CAMADA DE CONTEXTO (Criticidade Contínua / Monitoramento)           │
│    • Portais de Notícias (G1, Folha, Poder360, CNN, Estadão, etc.)     │
└────────────────────────────────────────────────────────────────────────┘
```

## Detalhamento dos Grupos de Dados

- **Fontes Primárias (TSE e Governo Federal):** Constituem o repositório oficial. A prioridade de reprocessamento é alta e as falhas exigem intervenção imediata.
- **Fontes Secundárias (Atividade Legislativa e Indicadores):** Enriquecem o perfil dos políticos com atuação parlamentar e histórico de votações.
- **Camada de Contexto (Notícias e Imprensa):** Fornecem contexto qualitativo sobre os candidatos e partidos, servindo como base para análises de presença na mídia.

---

## TSE — estado da catalogação de metadados

### Check: o que já foi trazido

Pipeline: [`src/etl/metadados_tse/`](../src/etl/metadados_tse/) → schema PostgreSQL `dados_tse`.

Catálogo explorável (read-only): [`src/web/`](../src/web/) — `make web` → [http://127.0.0.1:8000/tse](http://127.0.0.1:8000/tse).

| Indicador | Valor (última carga completa) | Onde está |
| --- | --- | --- |
| Datasets no inventário CKAN | **172** | `tse_datasets_inventory.json` |
| Datasets com JSON local | **172** (`fail=0`) | `out/*.json` (gitignored) |
| Linhas de recursos no manifest | **~5.289** | `tse_download_manifest.jsonl` |
| Recursos nos metadados tipados | **~5.205** | `dados_tse.recurso` / JSON |
| Escopo geopolítico | **Brasil** (172/172) | `meta_negocio` |
| Extração | API pura **160**; API+HTML **12** | `meta_tecnico.fonte_extracao` |

**Conclusão do check:** os metadados de **todos** os datasets publicados no catálogo CKAN do portal foram raspados e modelados. O que o documento antigo listava à mão (só 2026 + algumas páginas institucionais) era uma amostra — não o catálogo completo.

Ainda **não** estão neste pipeline (e não devem ser confundidos com “metadados faltando”):

- Conteúdo binário dos ZIPs/CSVs no data lake (bronze/MinIO futuro); cache local do enrich cobre só prioritários.
- Páginas institucionais fora do CKAN (`tse.jus.br/eleicoes/...`, estatísticas HTML).
- API comunitária de divulgação de candidaturas (`meucandidato.github.io`).
- Descrições de colunas a partir de `leia-me.pdf` (schema CSV dos prioritários já entra via enrich).

Já cobertos por `probe` / `enrich-files`: `status_link` (HEAD na CDN), `hash_conteudo` e `recurso_coluna` nos datasets prioritários 2026.
### Campos de metadados capturados por dataset

| Categoria | Campos |
| --- | --- |
| Núcleo | `id` (CKAN), `name` (slug), `titulo`, `estado`, `num_resources`, `metadata_hash` |
| Negócio | `descricao`, `area_gestora`, `escopo_geopolitico`, `contato`, `extras_nao_mapeados` |
| Técnico | `url_portal`, `url_api_package`, `origem_sistemas`, licença, `fonte_extracao`, `html_fallback_usado` |
| Operacional | `criado_em`, `modificado_em`, `extracao_dados`, `frequencia_atualizacao`, `coletado_em` |
| Referência | `organizacao`, `org_name`, `groups[]`, `tags[]` |
| Recursos (1:N) | `id`, `nome`, `formato`, `mimetype`, `url`, `tamanho_bytes`, `hash_conteudo`, `status_link`, datas de origem |
| Auditoria ETL | `pipeline_run` / `pipeline_log` (`run_id`, status, skipped por hash) |

Lacunas leves na fonte (não no modelo): ~10 datasets sem `contato`; ~5 sem texto de `extracao_dados`; labels variantes do portal (`Fonte`, typos em “Contatos…”) caem em `extras_nao_mapeados`.

### Cobertura por grupo temático (CKAN)

| Grupo (`meta_referencia.groups`) | Datasets | Papel |
| --- | ---: | --- |
| `resultados` | 61 | Totalização, BU, correspondências, logs de urna, suplementares |
| `candidatos` | 36 | Candidaturas, bens, coligações, vagas, redes (séries históricas + 2026) |
| `eleitorado` | 20 | Perfis de eleitorado, transferência, eleitorado atual |
| `prestacao-de-contas-partidarias` | 13 | Contas anuais/partidárias |
| `prestacao-de-contas-eleitorais` | 12 | Contas de campanha |
| `pesquisas-eleitorais` | 8 | Pesquisas registradas (incl. 2026) |
| `comparecimento-e-abstencao` | 7 | Comparecimento / abstenção |
| `mesarios` | 5 | Convocação e dados de mesários |
| `processual` | 4 | Processos eleitorais |
| `dados-de-apoio` | 3 | Códigos UF/município, frequência de atualização, apoio |
| `partidos` | 1 | Delegados partidários |
| (sem grupo) | 2 | Ex.: logs GEDAI 2024, suplementares 2022 |

Portal de grupos: <https://dadosabertos.tse.jus.br/group/>

### Área gestora e organização (metadado de negócio / referência)

| Área gestora | Datasets | Org CKAN |
| --- | ---: | --- |
| Assessoria de Gestão Eleitoral - AGEL | 117 | TSE/AGEL (119) |
| ASEPA | 25 | TSE/ASEPA |
| Secretaria Judiciária - SJD | ~13 | TSE/SJD |
| Corregedoria-Geral Eleitoral - CGE | ~7–9 | TSE/CGE |
| Secretaria de Gestão de Pessoas - SGP | 5 | TSE/SGP |
| SMG / STI | ≤3 | TSE/SMG, TSE/STI |

### Frequência de atualização declarada no portal

| Frequência | Datasets |
| --- | ---: |
| Sob demanda/necessidade | 102 |
| Eleição | 26 |
| Semanal | 22 |
| Diária / Diário | 10 |
| A cada eleição | ~7 |
| Mensal | 4 |
| Eleições suplementares / outros | 1+ |

### Formatos nos recursos catalogados

Aprox. entre os ~5,2k recursos tipados: CSV (~2,0k), formato vazio/`?` (~1,5k), TXT (~0,7k), JPEG (~0,3k), ZIP (~0,3k), PDF (~0,3k). Muitos “CSV” no portal apontam na prática para `.zip` na CDN (`mimetype` frequentemente `application/zip`).

---

## Catálogo TSE — pontos de entrada e datasets prioritários

### Pontos de entrada (portal / API)

| Nome | Tipo | URL | Frequência | Metadados no VotoData? | Notas |
| --- | --- | --- | --- | --- | --- |
| Portal Dados Abertos TSE | Portal | https://dadosabertos.tse.jus.br | Contínua | Sim (via API CKAN) | Fonte primária do ETL |
| Catálogo de datasets | Índice | https://dadosabertos.tse.jus.br/dataset/ | Contínua | **172/172** em `dados_tse` | Seed: `tse_datasets_inventory.json` |
| API CKAN `package_show` | REST/JSON | `/api/3/action/package_show?id=<slug>` | Contínua | Sim | Fonte principal do extract |
| Grupos temáticos | HTML | https://dadosabertos.tse.jus.br/group/ | Contínua | Sim (`groups[]`) | Taxonomia de referência |
| Sobre o portal | HTML | https://dadosabertos.tse.jus.br/about | Rara | Não (doc institucional) | Política de dados abertos |
| CDN de arquivos | Binário | `cdn.tse.jus.br/estatistica/...` | Por dataset | URL em `recurso`; arquivo ainda não baixado | Próximo passo: download |

### Datasets prioritários (Eleições 2026 e bases vivas)

Metadados abaixo refletem a captura do ETL (negócio + operacional + referência).

| Slug | Título | Grupo | Área gestora | Frequência | Recursos (n) | URL |
| --- | --- | --- | --- | --- | ---: | --- |
| `candidatos-2026` | Candidatos - 2026 | candidatos | AGEL | Diária | 7 | [dataset](https://dadosabertos.tse.jus.br/dataset/candidatos-2026) |
| `pesquisas-eleitorais-2026` | Pesquisas Eleitorais - 2026 | pesquisas-eleitorais | AGEL | Diária | 6 | [dataset](https://dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026) |
| `eleitorado-2026` | Eleitorado - 2026 | eleitorado | AGEL | Sob demanda/necessidade | 32 | [dataset](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026) |
| `eleitorado-atual` | Eleitorado Atual | eleitorado | AGEL | Mensal | 30 | [dataset](https://dadosabertos.tse.jus.br/dataset/eleitorado-atual) |
| `prestacao-de-contas-partidarias-2026` | Prestação de Contas Partidárias - 2026 | prestacao-de-contas-partidarias | ASEPA | Semanal | 2 | [dataset](https://dadosabertos.tse.jus.br/dataset/prestacao-de-contas-partidarias-2026) |
| `delegados-partidarios` | Partidos | partidos | — (ver JSON) | Semanal | 3 | [dataset](https://dadosabertos.tse.jus.br/dataset/delegados-partidarios) |
| `transferencia-do-eleitorado` | Transferência do eleitorado | eleitorado | AGEL | (ver `meta_operacional`) | 18 | [dataset](https://dadosabertos.tse.jus.br/dataset/transferencia-do-eleitorado) |

Séries históricas já catalogadas (não só 2026): **candidatos** (1933→), **resultados**, **eleitorado**, **prestação de contas**, **pesquisas**, **comparecimento**, **mesários**, **processual**, **dados de apoio**. Lista completa: inventário local ou `SELECT name, titulo FROM dados_tse.dataset ORDER BY name`.

### Fontes TSE auxiliares (fora do CKAN — metadados ainda não ingeridos neste ETL)

| Nome | URL | Formato | Frequência | Relação com o VotoData |
| --- | --- | --- | --- | --- |
| Resultados (site institucional) | https://www.tse.jus.br/eleicoes/resultados-eleicoes | HTML / links | Por pleito | Complementar; dados abertos equivalentes estão no grupo `resultados` do CKAN |
| Estatísticas eleitorais | https://www.tse.jus.br/eleicoes/estatisticas/estatisticas-eleitorais | HTML, CSV | Variável | Fora do schema `dados_tse` por enquanto |
| Prestação de contas 2026 (orientação) | https://www.tse.jus.br/eleicoes/eleicoes-2026-content/prestacao-de-contas | HTML | Por demanda | Documentação; arquivos oficiais no CKAN ASEPA/AGEL |
| API Divulgação de Candidaturas (comunidade) | https://meucandidato.github.io/tse-apidoc/ | REST/JSON | Tempo real | Fonte secundária / enriquecimento — não é o portal CKAN |

---

## Catálogo de fontes não-TSE (ainda não ingeridas neste repo)

| Nome da Fonte / Entidade | Categoria | URL Direta / Endpoint | Formato do Dado | Frequência de Atualização | Resumo do Conteúdo |
| --- | --- | --- | --- | --- | --- |
| Portal da Transparência Federal | Gastos Públicos | portaldatransparencia.gov.br | HTML, CSV, API | Diária | Gastos, contratos, convênios, servidores, viagens e despesas. |
| Download Portal da Transparência | Gastos Públicos | portaldatransparencia.gov.br/download-de-dados | CSV | Diária | Bases públicas para download em formato aberto. |
| API Portal da Transparência | Gastos Públicos | portaldatransparencia.gov.br/api-de-dados | REST API, JSON | Diária | Endpoints para consumo automatizado da base federal. |
| Dados Abertos CGU / Transparência | Gastos Públicos | gov.br/conecta/catalogo/apis/portal-da-transparencia-do-governo-federal | REST API | Por Demanda | Catálogo governamental de APIs e integrações de transparência. |
| Compras.gov.br API | Gastos Públicos | compras.dados.gov.br/docs/home.html | REST, XML, JSON | Diária | Licitações, contratos, fornecedores e compras públicas. |
| Métodos da API Compras | Gastos Públicos | compras.dados.gov.br/docs/lista-metodos.html | REST API | Por Demanda | Referência técnica dos métodos da API de compras públicas. |
| Portal Brasileiro de Dados Abertos | Indicadores | dados.gov.br | HTML, CSV, JSON | Semanal | Catálogo central de dados abertos do governo federal. |
| Dados Abertos do MDHC | Indicadores | gov.br/mdh/pt-br/acesso-a-informacao/dados-abertos | HTML, CSV | Semanal | Política federal de dados abertos e acesso a bases públicas. |
| G1 Política | Notícias/Scraping | [g1.globo.com/politica/](https://g1.globo.com/politica/) | HTML, RSS | Tempo Real | Cobertura de governo, Congresso, STF e bastidores de Brasília. |
| Folha Poder | Notícias/Scraping | www1.folha.uol.com.br/poder/ | HTML, RSS | Tempo Real | Notícias de política nacional e estadual. |
| Poder360 | Notícias/Scraping | poder360.com.br | HTML, RSS | Tempo Real | Cobertura de poder, Congresso e análise institucional. |
| CNN Brasil Política | Notícias/Scraping | cnnbrasil.com.br/politica/ | HTML, RSS | Tempo Real | Atualização contínua sobre governo, Congresso e STF. |
| Gazeta do Povo República | Notícias/Scraping | gazetadopovo.com.br/republica/ | HTML, RSS | Tempo Real | Cobertura de política, governo e economia nacional. |
| Brasil de Fato | Notícias/Scraping | brasildefato.com.br | HTML, RSS | Tempo Real | Cobertura política com foco social e de movimentos. |
| Times Brasil Política | Notícias/Scraping | timesbrasil.com.br/brasil/politica/ | HTML, RSS | Tempo Real | Notícias políticas em cobertura contínua. |
| PlatôBR | Notícias/Scraping | platobr.com.br | HTML, RSS | Tempo Real | Conteúdo de Brasília com foco em poder e bastidores. |
| Terra Política | Notícias/Scraping | terra.com.br/noticias/brasil/politica/ | HTML, RSS | Tempo Real | Política nacional, governo, Congresso e investigações. |
| Meus Políticos | Notícias/Scraping | meuspoliticos.com.br | HTML | Semanal | Transparência política com dados públicos e contexto para eleitores. |
| ChecaAI | Indicadores | checa.ai | HTML | Semanal | Consolidação de votos, despesas e comportamento parlamentar. |
| Brazil Visible - Justiça Eleitoral | Indicadores | brazilvisible.org/docs/apis/justica-eleitoral-tse/ | HTML, Catálogos | Por Demanda | Catálogo técnico com fontes do TSE e justiça eleitoral. |

---

## Como atualizar estes números

```bash
make extract-meta
make load-meta
```

Consultas úteis:

```sql
SELECT unnest(groups) AS grupo, count(*) 
FROM dados_tse.meta_referencia GROUP BY 1 ORDER BY 2 DESC;

SELECT frequencia_atualizacao, count(*) 
FROM dados_tse.meta_operacional GROUP BY 1 ORDER BY 2 DESC;

SELECT area_gestora, count(*) 
FROM dados_tse.meta_negocio GROUP BY 1 ORDER BY 2 DESC;
```

Ver também: [README](../README.md), [arquitetura](arquitetura.md), [governança](governanca_linhagem_qualidade.md), [operações](operacoes_pipelines.md), [links](links.md).
