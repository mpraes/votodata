from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from models import RecursoColuna  # DB model name stays until a later rename


def _is_data_member(name: str) -> bool:
    lower = name.lower().replace("\\", "/")
    if lower.endswith("/"):
        return False
    base = lower.rsplit("/", 1)[-1]
    if any(token in base for token in ("leiame", "leia-me", "readme")):
        return False
    return base.endswith((".csv", ".txt"))


def _read_header_from_bytes(raw: bytes) -> list[str]:
    text = None
    for encoding in ("latin-1", "utf-8", "cp1252"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("latin-1", errors="replace")

    first_line = text.splitlines()[0] if text else ""
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","
    row = next(csv.reader([first_line], delimiter=delimiter))
    return [col.strip().strip('"') for col in row if col.strip()]


def extract_columns_from_file(path: Path) -> list[RecursoColuna]:
    path = Path(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            members = sorted(name for name in archive.namelist() if _is_data_member(name))
            if not members:
                return []
            with archive.open(members[0]) as handle:
                headers = _read_header_from_bytes(handle.read(64 * 1024))
    else:
        headers = _read_header_from_bytes(path.read_bytes()[: 64 * 1024])

    return [
        RecursoColuna(
            nome_coluna=header,          # field names match DB/Pydantic for now
            tipo_dado_declarado="text",
            descricao=None,
            ordem=index,
        )
        for index, header in enumerate(headers)
    ]