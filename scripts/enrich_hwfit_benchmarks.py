#!/usr/bin/env python3
"""Refresh Cookbook model benchmark metadata from Hugging Face model cards.

The Cookbook ranking path is offline at runtime. This helper enriches
services/hwfit/data/hf_models.json ahead of release by reading structured
evaluation results from Hugging Face cardData/model-index metadata.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from huggingface_hub import HfApi


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "services" / "hwfit" / "data" / "hf_models.json"


def _metric_entries(info) -> list[dict]:
    card_data = getattr(info, "card_data", None) or getattr(info, "cardData", None)
    data = card_data.to_dict() if hasattr(card_data, "to_dict") else (card_data or {})
    model_index = (
        data.get("model-index")
        or data.get("model_index")
        or getattr(info, "model_index", None)
        or []
    )
    out = []
    if not isinstance(model_index, list):
        return out
    for entry in model_index:
        if not isinstance(entry, dict):
            continue
        for result in entry.get("results", []) or []:
            if not isinstance(result, dict):
                continue
            dataset = result.get("dataset") or {}
            source = result.get("source") or {}
            for metric in result.get("metrics", []) or []:
                if not isinstance(metric, dict):
                    continue
                value = metric.get("value")
                if value is None:
                    continue
                out.append({
                    "name": metric.get("type") or metric.get("name") or dataset.get("type") or dataset.get("name"),
                    "value": value,
                    "source": source.get("name") or source.get("url") or "model card",
                })
    return out


def enrich(limit: int = 0, dry_run: bool = False) -> int:
    models = json.loads(CATALOG.read_text())
    api = HfApi()
    changed = 0
    dirty = False
    scanned = 0
    for model in models:
        name = model.get("name")
        if not name or "/" not in name:
            continue
        scanned += 1
        if limit and scanned > limit:
            break
        try:
            info = api.model_info(
                name,
                files_metadata=False,
                expand=["cardData", "model-index", "downloads", "likes"],
            )
        except Exception as exc:
            print(f"! {name}: {exc}")
            continue
        entries = _metric_entries(info)
        if entries:
            model["benchmarks"] = entries
            model["benchmark_source"] = "huggingface:model-card"
            changed += 1
            dirty = True
            print(f"+ {name}: {len(entries)} benchmark result(s)")
        if getattr(info, "downloads", None) is not None:
            downloads = info.downloads or 0
            if model.get("hf_downloads") != downloads:
                model["hf_downloads"] = downloads
                dirty = True
        if getattr(info, "likes", None) is not None:
            likes = info.likes or 0
            if model.get("hf_likes") != likes:
                model["hf_likes"] = likes
                dirty = True
    if dirty and not dry_run:
        CATALOG.write_text(json.dumps(models, indent=2) + "\n")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Only scan N catalog repos")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print without writing")
    args = parser.parse_args()
    changed = enrich(limit=args.limit, dry_run=args.dry_run)
    print(f"enriched {changed} model(s)")


if __name__ == "__main__":
    main()
