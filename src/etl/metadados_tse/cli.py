from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import OUT_DIR, REQUEST_SLEEP_SECONDS
from extract_api import extras_as_dict, load_inventory_names, package_show
from extract_html import missing_priority_fields, scrape_informacoes_adicionais
from persist_local import ensure_out_dir, load_dataset, save_dataset
from load_pg import load_from_out
from transform import transform_package
from validate import apply_validation


def _log_run(run_id: uuid.UUID, event: dict) -> None:
    ensure_out_dir()
    path = OUT_DIR / "runs" / f"{run_id}.jsonl"
    event = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def cmd_extract(args: argparse.Namespace) -> int:
    run_id = uuid.uuid4()
    names = [args.name] if args.name else load_inventory_names()
    if args.limit is not None:
        names = names[: args.limit]

    ok = fail = 0
    session = requests.Session()
    _log_run(run_id, {"level": "INFO", "message": "extract start", "total": len(names)})

    for name in names:
        try:
            package = package_show(name, session=session)
            extras = extras_as_dict(package)
            criado_ok = bool(package.get("metadata_created"))
            html_fields = None
            if missing_priority_fields(extras, criado_ok=criado_ok):
                html_fields = scrape_informacoes_adicionais(name, session=session)
                _log_run(run_id, {"level": "INFO", "dataset_name": name, "message": "html fallback"})

            record = transform_package(package, html_fields=html_fields)
            result = apply_validation(record)
            if not result.ok_to_persist:
                fail += 1
                _log_run(
                    run_id,
                    {
                        "level": "ERROR",
                        "dataset_name": name,
                        "message": "validation failed",
                        "errors": result.dq.errors,
                    },
                )
            else:
                path = save_dataset(record)
                ok += 1
                _log_run(
                    run_id,
                    {
                        "level": "WARN" if result.dq.warnings else "INFO",
                        "dataset_name": name,
                        "message": f"saved {path.name}",
                        "warnings": result.dq.warnings,
                    },
                )
        except Exception as exc:  # noqa: BLE001 — isola dataset, segue o loop
            fail += 1
            _log_run(
                run_id,
                {"level": "ERROR", "dataset_name": name, "message": str(exc)},
            )

        time.sleep(REQUEST_SLEEP_SECONDS)

    _log_run(run_id, {"level": "INFO", "message": "extract done", "ok": ok, "fail": fail})
    print(f"run_id={run_id} ok={ok} fail={fail}")
    return 1 if fail and not ok else 0

def cmd_load(args: argparse.Namespace) -> int:
    from load_pg import load_from_out

    result = load_from_out(name=args.name)
    print(result)
    return 0 if result["fail"] == 0 else 1

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ETL metadados TSE")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("extract", help="Extrai metadados para out/")
    e.add_argument("--name", help="Slug de um dataset")
    e.add_argument("--limit", type=int, help="Limita quantidade do inventário")
    e.set_defaults(func=cmd_extract)

    l = sub.add_parser("load", help="Carrega metadados para Postgres")
    l.add_argument("--name", help="Slug de um dataset")
    l.set_defaults(func=cmd_load)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())