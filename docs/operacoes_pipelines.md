# 2. Cadência Operacional da Ingestão

Os dados são categorizados por cadência de execução para otimizar o uso do servidor e garantir atualização contínua:

## Tempo Real / Alta Frequência (Múltiplas vezes ao dia)

- **Objeto:** Cobertura midiática e notícias políticas (G1, Poder360, Folha, CNN, etc.).
- **Processo:** Execução de rotinas de scraping e leitura de feeds RSS a cada 1 a 3 horas.
- **Objetivo:** Capturar o fluxo imediato de fatos, declarações e movimentações do pleito.

## Diário (Janela Noturna)

- **Objeto:** Registros de candidaturas, atualizações do Portal da Transparência, compras públicas e proposições legislativas.
- **Processo:** Execução programada durante a madrugada para evitar concorrência de processamento.
- **Objetivo:** Atualizar bases transacionais e operacionais do governo e do TSE.

## Semanal

- **Objeto:** Pesquisas eleitorais registradas, estatísticas partidárias e relatórios consolidados.
- **Processo:** Consolidadores semanais com geração de relatórios de variação e indicadores.
- **Objetivo:** Alimentar análises de tendência e séries temporais.

## Por Demanda / Cargas Volumosas (Batch)

- **Objeto:** Histórico do TSE (prestações de contas completas, votação por seção eleitoral de anos anteriores).
- **Processo:** Disparo manual ou agendado em períodos de baixo uso da infraestrutura.
- **Objetivo:** Carga e preservação da base histórica primária.
