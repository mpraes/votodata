# 3. Matriz de Governança, Linhagem e Qualidade

Para garantir a confiabilidade dos dados do ecossistema político, todo lote ingerido passa obrigatoriamente pelas seguintes etapas de verificação:

```text
                               ┌─────────────────────────┐
                               │     Dado Capturado      │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │  Testes de Qualidade    │
                               └────────────┬────────────┘
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      ▼                                           ▼
             [ ✅ DADO APROVADO ]                       [ ❌ DADO REPROVADO ]
                      │                                           │
         ┌────────────┴────────────┐                 ┌────────────┴────────────┐
         │ Injeção de Linhagem     │                 │ Encaminhado para        │
         │ (Atributos de Auditoria)│                 │ a Quarentena            │
         └────────────┬────────────┘                 └────────────┬────────────┘
                      │                                           │
         ┌────────────┴────────────┐                 ┌────────────┴────────────┐
         │ Publicado para Consumo  │                 │ Notificação ao Operador │
         └─────────────────────────┘                 └─────────────────────────┘
```

## Protocolo de Validação de Qualidade

- **Verificação de Completude:** Checagem de campos obrigatórios (ex: número do candidato, sigla do partido, data da notícia).
- **Verificação de Unicidade:** Eliminação de duplicações via geração de hash único do conteúdo.
- **Tratamento de Anomalias (Quarentena):** Registros inconsistentes são desviados para uma área de Quarentena, impedindo que dados incorretos contaminem os relatórios finais. Um alerta é emitido imediatamente para análise.

## Atributos Rastreados (Linhagem de Dados)

Cada dado armazenado carrega metadados operacionais anexados:

- **Origem Exata:** URL do portal ou nome do arquivo original do TSE.
- **Data/Hora da Ingestão:** Momento exato em que o dado entrou na plataforma.
- **Identificador do Pipeline:** Código da execução que extraiu e processou o lote.
