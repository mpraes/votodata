from __future__ import annotations

import json
from pathlib import Path

from config import OUT_DIR
from models import DatasetRecord


def ensure_out_dir(out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "runs").mkdir(parents=True, exist_ok=True)
    return out_dir


def dataset_path(name: str, out_dir: Path = OUT_DIR) -> Path:
    return out_dir / f"{name}.json"


def save_dataset(record: DatasetRecord, out_dir: Path = OUT_DIR) -> Path:
    """Escreve out/{name}.json e append em index.jsonl."""
    ensure_out_dir(out_dir)
    path = dataset_path(record.dataset.name, out_dir)
    path.write_text(
        record.model_dump_json(indent=2),
        encoding="utf-8",
    )

    index_line = {
        "name": record.dataset.name,
        "path": str(path.relative_to(out_dir)),
        "status": record.dq.status,
        "html_fallback_usado": record.tecnico.html_fallback_usado,
        "metadata_hash": record.dataset.metadata_hash,
        "dq_status": record.dq.status,
    }
    with (out_dir / "index.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(index_line, ensure_ascii=False) + "\n")

    return path


def load_dataset(name: str, out_dir: Path = OUT_DIR) -> DatasetRecord:
    path = dataset_path(name, out_dir)
    return DatasetRecord.model_validate_json(path.read_text(encoding="utf-8"))