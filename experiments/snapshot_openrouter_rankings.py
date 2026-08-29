"""Snapshot the public OpenRouter weekly usage ranking for model selection."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


RANKINGS_URL = "https://openrouter.ai/rankings"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()

    response = requests.get(
        RANKINGS_URL,
        headers={"User-Agent": "DeAIodorantResearch/0.1 (+ranking-snapshot)"},
        timeout=args.timeout,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    leaderboard: dict[str, object] | None = None
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            value = json.loads(node.get_text())
        except json.JSONDecodeError:
            continue
        if (
            isinstance(value, dict)
            and value.get("@type") == "ItemList"
            and isinstance(value.get("itemListElement"), list)
        ):
            leaderboard = value
            break
    if leaderboard is None:
        raise RuntimeError("OpenRouter ranking ItemList was not found")

    entries: list[dict[str, object]] = []
    for item in leaderboard["itemListElement"]:
        if not isinstance(item, dict):
            continue
        entries.append(
            {
                "position": item.get("position"),
                "name": item.get("name"),
                "url": item.get("item"),
            }
        )
    payload = {
        "schema_version": "deaiodorant-openrouter-ranking-snapshot-1.0",
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "url": RANKINGS_URL,
        "ranking_name": leaderboard.get("name"),
        "page_sha256": hashlib.sha256(response.content).hexdigest(),
        "entries": entries,
        "interpretation": (
            "This is a weekly token-usage ranking, not a quality or task-fitness "
            "benchmark. Model use still requires a task-specific interface smoke test."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
