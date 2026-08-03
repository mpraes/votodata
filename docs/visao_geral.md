# 1. Visão Geral e Objetivos do Projeto

O VotoData é uma plataforma de engenharia de dados orientada ao domínio político-eleitoral brasileiro, desenvolvida para servir como um ecossistema "vivente" (Living Data Platform) focado nas Eleições de 2026.

O projeto simula um ambiente de produção corporativo utilizando hardware pessoal (Homelab), viabilizando pipelines de alta frequencia (scraping de notícias), cargas diárias e operacionais (APIs governamentais e gastos parlamentares) e processamento em lote de alto volume (dados históricos do TSE).

## Objetivos do Ecossistema

- **Fonte Única da Verdade (Single Source of Truth):** Preservar a integridade e rastreabilidade histórica de dados abertos oficiais do TSE, Portal da Transparência e Compras.gov.br.
- **Benchmarking e Otimização de Recursos:** Testar de forma lado a lado engines modernas de processamento de dados (Polars, DuckDB e Pandas) sob restrição rígida de hardware.
- **Prontidão para Machine Learning (ML-Ready):** Estruturar a camada Gold e preparar pipelines de NLP para categorização de notícias, análise de sentimento e extração de entidades eleitorais em futuros modelos preditivos.
- **Segurança e Baixo Consumo Operacional:** Operar um ambiente isolado com acesso seguro via Tailscale / Ngrok (com autenticação) e orquestração leve via Prefect.

# 1. Visão Geral dos Processos

O VotoData opera sob o conceito de Living Data Platform (Plataforma Viva de Dados). A sustentação do projeto baseia-se na execução diária e sistemática de quatro macroprocessos:

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Coleta e    │ ──► │  2. Validação   │ ──► │ 3. Governança e │ ──► │ 4. Servimento e │
│   Ingestão      │     │  e Qualidade    │     │    Linhagem     │     │  Disponib.      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Coleta e Ingestão de Dados:** Captura automatizada de dados oficiais, institucionais e notícias.
- **Validação e Qualidade (Data Quality):** Avaliação de consistência antes da liberação para consumo.
- **Governança, Metadados e Linhagem:** Catalogação do dado e registro do seu histórico de transformação.
- **Servimento e Disponibilização:** Organização dos dados para consultas e dashboards.
