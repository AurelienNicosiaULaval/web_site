#!/usr/bin/env python3
"""Build the hand-reviewed cover cache from stable external image URLs.

The automated providers sometimes expose generic "not the actual cover"
graphics. Every entry below was therefore reviewed visually before being
approved. ISBN entries use an exact AbeBooks ISBN page. Records without an
ISBN require agreement on title, author, publication year, and publisher.

Run from the project root:

    python3 scripts/fetch_verified_covers.py
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "assets/library/library-data.json"
DEFAULT_OUTPUT = ROOT / "data/library/verified-cover-cache.json"
USER_AGENT = "AurelienNicosiaLibrary/1.0 (+https://aureliennicosiaulaval.github.io/web_site/)"

# The standard ISBN endpoint is used only for images that were visually
# confirmed as real covers. Four ISBNs use seller photographs because the
# standard endpoint returned no image or a generic substitute.
APPROVED_ABEBOOKS_IMAGES = {
    "9782030754665": "https://pictures.abebooks.com/isbn/9782030754665-us.jpg",
    "9782130314363": "https://pictures.abebooks.com/isbn/9782130314363-us.jpg",
    "9782130353911": "https://pictures.abebooks.com/isbn/9782130353911-us.jpg",
    "9782130365327": "https://pictures.abebooks.com/inventory/31673988241.jpg",
    "9782130366027": "https://pictures.abebooks.com/isbn/9782130366027-us.jpg",
    "9782200210410": "https://pictures.abebooks.com/isbn/9782200210410-us.jpg",
    "9782704210046": "https://pictures.abebooks.com/isbn/9782704210046-us.jpg",
    "9782711720279": "https://pictures.abebooks.com/isbn/9782711720279-us.jpg",
    "9782733805855": "https://pictures.abebooks.com/isbn/9782733805855-us.jpg",
    "9782743008260": "https://pictures.abebooks.com/isbn/9782743008260-us.jpg",
    "9782763773636": "https://pictures.abebooks.com/isbn/9782763773636-us.jpg",
    "9782765107552": "https://pictures.abebooks.com/isbn/9782765107552-us.jpg",
    "9782766157426": "https://pictures.abebooks.com/isbn/9782766157426-us.jpg",
    "9782815202374": "https://pictures.abebooks.com/isbn/9782815202374-us.jpg",
    "9782815202381": "https://pictures.abebooks.com/inventory/30317561772.jpg",
    "9782815202398": "https://pictures.abebooks.com/isbn/9782815202398-us.jpg",
    "9782870770658": "https://pictures.abebooks.com/inventory/19309486828.jpg",
    "9782890943377": "https://pictures.abebooks.com/isbn/9782890943377-us.jpg",
    "9782892496017": "https://pictures.abebooks.com/isbn/9782892496017-us.jpg",
    "9782894714270": "https://pictures.abebooks.com/isbn/9782894714270-us.jpg",
    "9782957239115": "https://pictures.abebooks.com/isbn/9782957239115-us.jpg",
    "9782957239122": "https://pictures.abebooks.com/isbn/9782957239122-us.jpg",
    "9782957239139": "https://pictures.abebooks.com/isbn/9782957239139-us.jpg",
    "9783540908999": "https://pictures.abebooks.com/inventory/22776042990.jpg",
    "9785030007175": "https://pictures.abebooks.com/isbn/9785030007175-us.jpg",
    "9786001417351": "https://pictures.abebooks.com/isbn/9786001417351-us.jpg",
    "9798811583607": "https://pictures.abebooks.com/isbn/9798811583607-us.jpg",
    "9798991493604": "https://pictures.abebooks.com/isbn/9798991493604-us.jpg",
}

APPROVED_RECORD_IMAGES = {
    "book-0005": {
        "provider": "Mir Titles",
        "source_id": "mirtitles_cover",
        "source_url": "https://mirtitles.org/2023/09/04/elements-de-la-theorie-des-groupes-by-m-kargapolov-i-merzliakov/",
        "images": {
            "small": "https://mirtitles.org/wp-content/uploads/2023/08/kargapolov-merzliakov-elements-de-la-theorie-des-groupes-mir-1985_0000.jpg?w=320",
            "medium": "https://mirtitles.org/wp-content/uploads/2023/08/kargapolov-merzliakov-elements-de-la-theorie-des-groupes-mir-1985_0000.jpg?w=640",
            "large": "https://mirtitles.org/wp-content/uploads/2023/08/kargapolov-merzliakov-elements-de-la-theorie-des-groupes-mir-1985_0000.jpg",
        },
        "match": {
            "title": "éléments de la théorie des groupes",
            "author": "M. Kargapolov | Iou. Merzliakov",
            "publication_year": "1985",
            "publisher_normalized": "Éditions Mir",
        },
    },
    "book-0014": {
        "provider": "Anticariat.net",
        "source_id": "anticariat_cover",
        "source_url": "https://www.anticariat.net/p/275443/Programmation-lineaire-Achmanov-Achmanov",
        "images": {
            "small": "https://www.anticariat.net/coperta/programmation-lineaire-achmanov-275443_mid.jpg",
            "medium": "https://www.anticariat.net/coperta/programmation-lineaire-achmanov-275443_full.jpg",
            "large": "https://www.anticariat.net/coperta/programmation-lineaire-achmanov-275443_full.jpg",
        },
        "match": {
            "title": "Programmation linéaire",
            "author": "s. Achmanov",
            "publication_year": "1984",
            "publisher_normalized": "Éditions Mir",
        },
    },
    "book-0441": {
        "provider": "Internet Archive",
        "source_id": "internet_archive_cover",
        "source_url": "https://archive.org/details/analysenumerique0000unse",
        "images": {
            "small": "https://archive.org/services/img/analysenumerique0000unse",
            "medium": "https://archive.org/services/img/analysenumerique0000unse",
            "large": "https://archive.org/services/img/analysenumerique0000unse",
        },
        "match": {
            "title": "Analyse numérique",
            "author": "Roger Temam",
            "publication_year": "1970",
            "publisher_normalized": "Presses Universitaires de France",
        },
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def probe_image(url: str, timeout: float) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        payload = response.read()
    if not content_type.startswith("image/") or len(payload) < 5_000:
        raise RuntimeError(
            f"Rejected cover response ({content_type}, {len(payload)} bytes): {url}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--skip-probe", action="store_true")
    parser.add_argument("--retrieved-on", default=str(date.today()))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalogue = read_json(args.catalogue)
    records = catalogue["records"]
    by_isbn = {
        str(record.get("isbn", "")): record
        for record in records
        if record.get("isbn_status") == "valid"
    }
    by_id = {record["id"]: record for record in records}

    books: dict[str, Any] = {}
    for isbn, image_url in sorted(APPROVED_ABEBOOKS_IMAGES.items()):
        record = by_isbn.get(isbn)
        if record is None:
            raise RuntimeError(f"Approved ISBN is absent from the catalogue: {isbn}")
        if not args.skip_probe:
            probe_image(image_url, args.timeout)
        books[isbn] = {
            "isbn": isbn,
            "record_id": record["id"],
            "provider": "AbeBooks",
            "source_id": "abebooks_verified",
            "source_url": f"https://www.abebooks.com/book-search/isbn/{isbn}/",
            "match_method": "exact_isbn",
            "cover": {
                "small": image_url,
                "medium": image_url,
                "large": image_url,
            },
        }

    record_matches: dict[str, Any] = {}
    for record_id, approved in sorted(APPROVED_RECORD_IMAGES.items()):
        record = by_id.get(record_id)
        if record is None:
            raise RuntimeError(f"Approved record is absent from the catalogue: {record_id}")
        actual_match = {
            field: str(record.get(field, ""))
            for field in approved["match"]
        }
        if actual_match != approved["match"]:
            raise RuntimeError(
                f"Bibliographic fields changed for {record_id}: {actual_match}"
            )
        if not args.skip_probe:
            probe_image(approved["images"]["medium"], args.timeout)
        record_matches[record_id] = {
            **approved,
            "record_id": record_id,
            "match_method": "title_author_year_publisher",
        }

    payload = {
        "retrieved_on": args.retrieved_on,
        "review_policy": (
            "Every image was visually reviewed. Generic substitutes and images "
            "labelled as not being the actual cover were excluded."
        ),
        "isbn_cover_count": len(books),
        "record_cover_count": len(record_matches),
        "books": books,
        "record_matches": record_matches,
    }
    write_json(args.output, payload)
    print(
        f"Cached {len(books)} exact-ISBN and {len(record_matches)} "
        "strict bibliographic covers."
    )


if __name__ == "__main__":
    main()
