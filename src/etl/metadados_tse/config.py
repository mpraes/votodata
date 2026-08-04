from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "out"
INVENTORY_PATH = BASE_DIR / "tse_datasets_inventory.json"
SQL_DIR = BASE_DIR / "sql"

TSE_BASE_URL = os.getenv("TSE_BASE_URL", "https://dadosabertos.tse.jus.br").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL", "")
REQUEST_SLEEP_SECONDS = float(os.getenv("REQUEST_SLEEP_SECONDS", "0.3"))

CACHE_DIR = Path(os.getenv("VOTODATA_CACHE_DIR", str(BASE_DIR / "cache")))
PROBE_SLEEP_SECONDS = float(os.getenv("PROBE_SLEEP_SECONDS", str(REQUEST_SLEEP_SECONDS)))

PRIORITY_DATASETS = (
    "candidatos-2026",
    "pesquisas-eleitorais-2026",
    "eleitorado-2026",
    "eleitorado-atual",
    "prestacao-de-contas-partidarias-2026",
)