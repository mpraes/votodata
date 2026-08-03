from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from config import INVENTORY_PATH, REQUEST_SLEEP_SECONDS, TSE_BASE_URL


def load_inventory_names(path: Path = INVENTORY_PATH) -> list[str]:
    """Lê slugs dos datasets a partir do inventário local."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [d["name"] for d in data["datasets"] if d.get("name")]


def package_show(name: str, session: requests.Session | None = None) -> dict[str, Any]:
    """
    Busca metadados de um dataset no CKAN.
    Endpoint: /api/3/action/package_show?id=<slug>
    """
    sess = session or requests.Session()
    url = f"{TSE_BASE_URL}/api/3/action/package_show"
    resp = sess.get(url, params={"id": name}, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"package_show falhou para {name}: {payload}")
    return payload["result"]


def extras_as_dict(package: dict[str, Any]) -> dict[str, str]:
    """Converte result.extras (lista de {key,value}) em dict simples."""
    out: dict[str, str] = {}
    for item in package.get("extras") or []:
        key = item.get("key")
        if key is None:
            continue
        out[str(key)] = "" if item.get("value") is None else str(item["value"])
    return out