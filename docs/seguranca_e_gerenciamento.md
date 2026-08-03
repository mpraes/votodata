# 4. Estratégias Governamentais de Segurança, Qualidade e Governança

## 4.1. Segurança da Infraestrutura

- **Rede Privada Mesh (Tailscale):** Sem abertura de portas públicas no roteador local. Todo o tráfego administrativo para o Prefect, MinIO e Metabase viaja por um túnel WireGuard criptografado.
- **Exposição Web Controlada (Ngrok Browser):** Para acessos externos ao Metabase sem a VPN instalada, o acesso é protegido obrigatoriamente pela opção `--basic-auth="usuario:senha_forte"`.
- **Gestão de Segredos:** Nenhuma credencial é gravada no código. As variáveis ficam isoladas no arquivo `.env` (fora do git) e nos Blocks do Prefect.

## 4.2. Qualidade dos Dados (Data Quality Framework)

- **Validação In-Memory (Polars):** Checagens completas sem custo adicional de memória antes da gravação na camada Silver.
- **Completude:** Teste `is_not_null()` sobre chaves primárias e campos obrigatórios (`CPF_CANDIDATO`, `ID_PROPOSICAO`).
- **Unicidade:** Deduplicação por hash do registro (`_data_hash`).
- **Faixa de Domínio:** Datas coerentes e validação da lista oficial das 27 UFs.
- **Isolamento em Quarentena (`quarantine/`):** Dados que falham nos testes não interrompem o ecossistema; são desviados para a quarentena no MinIO e disparam um Webhook de alerta para o Discord/Telegram.

## 4.3. Gerenciamento de Metadados e Dicionário

O PostgreSQL aloca o schema `metadata` dedicado para atuar como um catálogo leve sem sobrecarregar a máquina:

- `metadata.data_catalog`: Mapeia localização, formato, responsável e camada Medallion de cada dataset.
- `metadata.data_dictionary`: Mapeia siglas e significados das colunas brutas do TSE.
- `metadata.pipeline_execution_logs`: Registra métricas de execução (runtime, consumo de memória, quantidade de linhas inseridas/rejeitadas).

## 4.4. Linhagem dos Dados (Data Lineage)

Todas as tabelas nas camadas Silver e Gold incluem nativamente as seguintes colunas de auditoria:

- `_ingested_at`: Timestamp UTC exacto da ingestão.
- `_source_file`: URL do arquivo de origem ou nome da API.
- `_pipeline_run_id`: UUID da execução do Prefect para rastreabilidade de logs.
- `_data_hash`: Hash MD5 do conteúdo da linha para auditoria de alterações na origem.

## 4. Matriz Operacional de Segurança e Controle de Acesso

O gerenciamento do acesso aos componentes da plataforma segue o princípio do menor privilégio:

| Nível | Componente / Interface | Política de Acesso Operacional |
| --- | --- | --- |
| Administração | Painel do Orquestrador e Servidor | Restrito ao operador principal via VPN Privada (Tailscale). |
| Armazenamento Bruto | Console do Data Lake | Acesso exclusivo para verificação de dados e quarentena. |
| Consultas e Relatórios | Interface de BI (Metabase) | Acesso protegido por autenticação com usuário e senha. |
