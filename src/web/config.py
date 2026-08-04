from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

DATABASE_URL = os.getenv("DATABASE_URL", "")

PRIORITY_DATASETS = (
    "candidatos-2026",
    "pesquisas-eleitorais-2026",
    "eleitorado-2026",
    "eleitorado-atual",
    "prestacao-de-contas-partidarias-2026",
)
