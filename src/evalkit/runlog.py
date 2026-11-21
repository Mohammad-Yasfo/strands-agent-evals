"""Record a run once, then score it as often as you like.

A run file is JSON Lines: one header row that says what produced the run (models, prompt hashes, settings), then one
row per result with the raw model output and its token usage. Scoring reads the file and never calls a model.
"""

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# USD per million tokens, on demand in US East, for the models used here. Check current pricing before relying on it.
PRICES = {"us.amazon.nova-lite-v1:0": (0.06, 0.24), "us.amazon.nova-pro-v1:0": (0.80, 3.20)}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def estimate(model: str, calls: int, input_tokens: int, output_tokens: int) -> float:
    """What a planned run should cost, to print before it starts."""
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    return calls * (input_tokens * price_in + output_tokens * price_out) / 1e6


class RunLog:
    def __init__(self, folder: Path, name: str, **header):
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{name}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.jsonl"
        self._write({"header": True, "started": datetime.now(timezone.utc).isoformat(timespec="seconds"), **header})

    def _write(self, row: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def add(self, **row) -> None:
        self._write(row)


def read(path: Path) -> tuple[dict, list[dict]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    header = next((r for r in rows if r.get("header")), {})
    return header, [r for r in rows if not r.get("header")]


def cost(rows: list[dict]) -> dict[str, dict]:
    """Tokens and USD per model, from the usage each row recorded under usage[model]."""
    totals: dict[str, dict] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "usd": 0.0})
    for row in rows:
        for model, u in (row.get("usage") or {}).items():
            t = totals[model]
            t["input_tokens"] += u.get("input_tokens", 0)
            t["output_tokens"] += u.get("output_tokens", 0)
    for model, t in totals.items():
        price_in, price_out = PRICES.get(model, (0.0, 0.0))
        t["usd"] = (t["input_tokens"] * price_in + t["output_tokens"] * price_out) / 1e6
    return dict(totals)
