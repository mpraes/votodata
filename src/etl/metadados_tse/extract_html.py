from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from config import TSE_BASE_URL


def scrape_informacoes_adicionais(
    dataset_name: str,
    *,
    session: requests.Session | None = None,
) -> dict[str, str]:
    """
    Lê th.dataset-label / td.dataset-details da página do dataset.
    Retorna dict label_original -> valor (texto).
    """
    sess = session or requests.Session()
    url = f"{TSE_BASE_URL}/dataset/{dataset_name}"
    resp = sess.get(url, timeout=60)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.select_one("table.table.table-striped")
    if table is None:
        return {}

    out: dict[str, str] = {}
    for row in table.select("tr"):
        th = row.select_one("th.dataset-label")
        td = row.select_one("td.dataset-details")
        if not th or not td:
            continue
        label = " ".join(th.get_text(" ", strip=True).split())
        value = " ".join(td.get_text(" ", strip=True).split())
        if label:
            out[label] = value
    return out


def missing_priority_fields(extras: dict[str, str], *, criado_ok: bool) -> bool:
    """True se ainda falta algum campo prioritário após a API."""
    keys_norm_needed = {
        "contato para dúvidas/sugestões",
        "escopo geopolítico",
        "extração dos dados",
        "frequência de atualização",
        "área gestora",
    }
    # comparação simples casefold no label original
    have = {k.casefold() for k, v in extras.items() if v}
    if not keys_norm_needed.issubset(have):
        return True
    return not criado_ok