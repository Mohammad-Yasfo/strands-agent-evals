"""Hand labels that belong to one exact output.

Keyword rules give every output a first label. A person reads the outputs that matter and corrects labels in a
review file. Each correction is keyed to the output's identity and a hash of its exact text, so it can't silently
carry over to a different output after a re-run.
"""

import json
from pathlib import Path
from typing import Callable

from evalkit.runlog import sha


def key(row: dict, fields: tuple[str, ...], text: str) -> str:
    return "|".join(str(row[f]) for f in fields) + "|" + sha(row[text])


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def label(row: dict, review: dict, k: str, first: Callable[[dict], str]) -> str:
    return (review.get(k) or {}).get("label") or first(row)
