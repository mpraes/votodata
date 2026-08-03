# 5. Matriz de Fontes de Dados e Prioridades Operacionais

Os dados alimentados no VotoData são organizados em três camadas operacionais de prioridade:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. FONTE PRIMÁRIA (Criticidade Alta / Base Oficial)                   │
│    • TSE (Candidatos, Pesquisas, Resultados, Prestação de Contas)      │
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

## Catálogo de Fontes

| Nome da Fonte / Entidade | Categoria | URL Direta / Endpoint | Formato do Dado | Frequência de Atualização | Resumo do Conteúdo |
| --- | --- | --- | --- | --- | --- |
| Portal de Dados Abertos do TSE | Dados Eleitorais | dadosabertos.tse.jus.br | CSV, Zip | Por Demanda | Portal central com bases eleitorais, candidaturas, eleitorado, resultados e contas. |
| Conjunto de Dados do TSE | Dados Eleitorais | dadosabertos.tse.jus.br/dataset/ | CSV, Zip | Por Demanda | Catálogo completo dos datasets do TSE e acesso à API. |
| Grupos do Portal do TSE | Dados Eleitorais | dadosabertos.tse.jus.br/group/ | HTML | Por Demanda | Navegação por temas como eleitorado, candidaturas e contas. |
| Sobre o Portal do TSE | Dados Eleitorais | dadosabertos.tse.jus.br/about | HTML | Por Demanda | Política de dados abertos do TSE e histórico desde 1933. |
| Candidatos - 2026 | Dados Eleitorais | dadosabertos.tse.jus.br/dataset/candidatos-2026 | CSV | Diária | Registros de candidatura, bens declarados, coligações e propostas. |
| Pesquisas Eleitorais - 2026 | Dados Eleitorais | dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026 | CSV, PDF | Semanal | Pesquisas, questionários, notas fiscais e detalhamento por UF/município. |
| Resultados Eleitorais do TSE | Dados Eleitorais | tse.jus.br/eleicoes/resultados-eleicoes | CSV | Diária | Totalização e votação por município, zona e seção eleitoral. |
| Estatísticas Eleitorais do TSE | Dados Eleitorais | tse.jus.br/eleicoes/estatisticas/estatisticas-eleitorais | HTML, CSV | Diária | Estatísticas de eleição, candidaturas, comparecimento e filiação. |
| Prestação de contas - Eleições 2026 | Dados Eleitorais | tse.jus.br/eleicoes/eleicoes-2026-content/prestacao-de-contas | HTML | Por Demanda | Orientações e sistemas relacionados às contas de candidatos e partidos. |
| Prestação de contas eleitorais | Dados Eleitorais | tse.jus.br/eleicoes/historia/processo-eleitoral-brasileiro/contas-eleitorais | HTML | Por Demanda | Conceitos e normas sobre prestação de contas eleitorais e partidárias. |
| API Divulgação de Candidaturas | Dados Eleitorais | meucandidato.github.io/tse-apidoc/ | REST API, JSON | Tempo Real | Consulta programática de candidaturas, contas, doações e gastos. |
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
