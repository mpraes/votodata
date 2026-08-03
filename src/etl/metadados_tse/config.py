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