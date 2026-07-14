#!/usr/bin/env python3
"""Extend the exact-ISBN Open Library snapshot for the current catalogue.

Only ISBNs absent from the existing snapshot are requested by default. This
preserves reviewed historical responses while enriching newly imported CLZ
records through Open Library's official Books API.

Run from the project root:

    python3 scripts/fetch_openlibrary_isbn.py
    python3 scripts/curate_library_data.py
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "assets/library/library-data.json"
DEFAULT_OUTPUT = ROOT / "data/library/openlibrary-isbn-cache.json"
ENDPOINT = "https://openlibrary.org/api/books"
USER_AGENT = (
    "AurelienNicosiaLibrary/1.0 "
    "(+https://aureliennicosiaulaval.github.io/web_site/)"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def batched(values: list[str], size: int) -> list[list[str]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def fetch_batch(isbns: list[str], timeout: float) -> dict[str, Any]:
    params = urllib.parse.urlencode({
        "bibkeys": ",".join(f"ISBN:{isbn}" for isbn in isbns),
        "jscmd": "data",
        "format": "json",
    })
    request = urllib.request.Request(
        f"{ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected Open Library Books API response.")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--pause", type=float, default=0.25)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Request every valid ISBN instead of only missing cache keys.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalogue = read_json(args.catalogue)
    cache = read_json(args.output) if args.output.exists() else {}
    all_isbns = sorted({
        str(record.get("isbn", "")).strip()
        for record in catalogue["records"]
        if record.get("isbn_status") == "valid"
        and re.fullmatch(r"\d{9}[\dX]|\d{13}", str(record.get("isbn", "")).strip())
    })
    targets = [
        isbn
        for isbn in all_isbns
        if args.refresh or f"ISBN:{isbn}" not in cache
    ]

    found = 0
    batches = batched(targets, args.batch_size)
    for index, batch in enumerate(batches):
        response = fetch_batch(batch, args.timeout)
        for key, entry in response.items():
            if key.startswith("ISBN:") and isinstance(entry, dict):
                cache[key] = entry
                found += 1
        if index + 1 < len(batches):
            time.sleep(args.pause)

    write_json(args.output, cache)
    print(
        f"Requested {len(targets)} missing ISBNs from Open Library; "
        f"found {found}; snapshot now contains {len(cache)} entries."
    )


if __name__ == "__main__":
    main()
