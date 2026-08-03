# 2. Especificação do Hardware do Homelab

A infraestrutura foi dimensionada para respeitar os limites físicos da máquina hospedeira sem acionar o OOM Killer do Linux.

## Especificações do Sistema

- **Modelo:** HP Pavilion g4 Notebook PC
- **Processador (CPU):** AMD A6-4400M APU (2 Cores / 2 Threads @ 2.7 GHz máx)
- **Memória RAM:** 5.3 GiB total (~4.2 GiB livres para o Docker)
- **Armazenamento Interno (SSD /dev/sda - 112 GB):** Sistema Operacional Ubuntu 24.04 LTS + PostgreSQL (data_warehouse) + Metabase + Swap (8 GB no SSD)
- **Armazenamento Externo (HD /dev/sdb - 466 GB montado em /mnt/hd_externo):** Volumes do MinIO (sandbox, bronze, silver, quarantine)
