#!/usr/bin/env python3
"""Check public links listed in metadata/link-check.yml.

The script is intentionally lightweight and non-destructive. It reads a small
YAML configuration, checks each URL, reports ok/warning/failed and exits with a
non-zero status only when required links fail.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("metadata/link-check.yml")
DEFAULT_TIMEOUT = 20
DEFAULT_USER_AGENT = "AurelienNicosiaULaval-web-site-link-check/1.0"


@dataclass
class ProbeResult:
    status: int | None
    final_url: str
    method: str
    error: str | None = None


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def parse_key_value(text: str) -> tuple[str, Any]:
    key, value = text.split(":", 1)
    return key.strip(), parse_scalar(value)


def fallback_parse_yaml(path: Path) -> dict[str, Any]:
    """Parse the restricted YAML shape used by metadata/link-check.yml.

    This is not a general YAML parser. It supports top-level scalar settings
    and a top-level links list made of flat key-value mappings.
    """

    data: dict[str, Any] = {"settings": {}, "links": []}
    section: str | None = None
    current_link: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()

        if not raw_line.startswith(" ") and stripped.endswith(":"):
            section = stripped[:-1]
            current_link = None
            if section == "links":
                data.setdefault("links", [])
            else:
                data.setdefault(section, {})
            continue

        if section == "settings" and raw_line.startswith("  "):
            key, value = parse_key_value(stripped)
            data["settings"][key] = value
            continue

        if section == "links" and raw_line.startswith("  - "):
            current_link = {}
            data["links"].append(current_link)
            rest = raw_line.split("- ", 1)[1].strip()
            if rest:
                key, value = parse_key_value(rest)
                current_link[key] = value
            continue

        if section == "links" and raw_line.startswith("    ") and current_link is not None:
            key, value = parse_key_value(stripped)
            current_link[key] = value
            continue

        raise ValueError(f"Unsupported YAML line: {raw_line!r}")

    return data


def load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        if not isinstance(loaded, dict):
            raise ValueError("YAML root must be a mapping.")
        return loaded
    except ModuleNotFoundError:
        return fallback_parse_yaml(path)


def probe_url(url: str, timeout: int, user_agent: str) -> ProbeResult:
    headers = {"User-Agent": user_agent, "Accept": "*/*"}
    last_error: str | None = None

    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return ProbeResult(
                    status=response.status,
                    final_url=response.geturl(),
                    method=method,
                )
        except urllib.error.HTTPError as error:
            if method == "HEAD":
                last_error = f"HTTP {error.code} on HEAD"
                continue
            return ProbeResult(
                status=error.code,
                final_url=error.geturl(),
                method=method,
                error=str(error),
            )
        except urllib.error.URLError as error:
            if method == "HEAD":
                last_error = str(error.reason)
                continue
            return ProbeResult(
                status=None,
                final_url=url,
                method=method,
                error=str(error.reason),
            )
        except TimeoutError:
            if method == "HEAD":
                last_error = "timeout"
                continue
            return ProbeResult(status=None, final_url=url, method=method, error="timeout")

    return ProbeResult(status=None, final_url=url, method="HEAD/GET", error=last_error)


def classify_result(link: dict[str, Any], probe: ProbeResult) -> str:
    required = bool(link.get("required", True))
    warning_statuses = {int(code) for code in link.get("warning_statuses", [])}

    if probe.status is not None and probe.status in warning_statuses:
        return "warning"
    if probe.status is not None and 200 <= probe.status < 400:
        return "ok"
    if not required:
        return "warning"
    return "failed"


def format_status(status: int | None) -> str:
    return str(status) if status is not None else "ERROR"


def check_links(config: dict[str, Any], delay_seconds: float = 0.0) -> list[dict[str, Any]]:
    settings = config.get("settings", {})
    timeout = int(settings.get("timeout_seconds", DEFAULT_TIMEOUT))
    user_agent = str(settings.get("user_agent", DEFAULT_USER_AGENT))
    links = config.get("links", [])

    if not isinstance(links, list) or not links:
        raise ValueError("Configuration must contain a non-empty links list.")

    rows: list[dict[str, Any]] = []
    for link in links:
        if not isinstance(link, dict):
            raise ValueError("Each link entry must be a mapping.")
        url = str(link["url"])
        probe = probe_url(url, timeout=timeout, user_agent=user_agent)
        result = classify_result(link, probe)
        rows.append(
            {
                "name": str(link.get("name", "")),
                "category": str(link.get("category", "")),
                "url": url,
                "status": format_status(probe.status),
                "method": probe.method,
                "result": result,
                "final_url": probe.final_url,
                "message": probe.error or "",
            }
        )
        if delay_seconds > 0:
            time.sleep(delay_seconds)
    return rows


def print_report(rows: list[dict[str, Any]]) -> None:
    header = ["result", "status", "category", "name", "url"]
    print("\t".join(header))
    for row in rows:
        print("\t".join(str(row[column]) for column in header))

    counts = {"ok": 0, "warning": 0, "failed": 0}
    for row in rows:
        counts[row["result"]] += 1

    print()
    print(
        "Summary: "
        f"total={len(rows)} "
        f"ok={counts['ok']} "
        f"warning={counts['warning']} "
        f"failed={counts['failed']}"
    )

    warnings = [row for row in rows if row["result"] == "warning"]
    failures = [row for row in rows if row["result"] == "failed"]

    if warnings:
        print()
        print("Warnings:")
        for row in warnings:
            print(f"- {row['name']}: status={row['status']} url={row['url']}")

    if failures:
        print()
        print("Failures:")
        for row in failures:
            print(f"- {row['name']}: status={row['status']} url={row['url']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check public ecosystem links.")
    parser.add_argument(
        "config",
        nargs="?",
        default=str(DEFAULT_CONFIG),
        help="Path to metadata/link-check.yml.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Optional delay in seconds between requests.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    config = load_config(config_path)
    rows = check_links(config, delay_seconds=args.delay)
    print_report(rows)

    return 1 if any(row["result"] == "failed" for row in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
