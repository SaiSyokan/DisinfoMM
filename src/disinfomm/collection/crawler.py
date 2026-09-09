"""Polite, incremental collection orchestration."""

from __future__ import annotations

import csv
import time
from pathlib import Path
from urllib.parse import urljoin

from ..io import append_dataset_csv, append_jsonl, read_jsonl
from .adapters import enrich_pagella, parse_pagella, parse_poligrafo, parse_snopes


def _dependencies():
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install collector dependencies with: pip install -e '.[collect]'") from exc
    return requests, BeautifulSoup


def _get(session, url: str, timeout: float):
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def collect(
    source: str,
    output: Path,
    *,
    pages: int = 1,
    delay: float = 1.0,
    timeout: float = 30.0,
    user_agent: str = "DisinfoMM/1.0 (+https://github.com/SaiSyokan/DisinfoMM)",
    limit: int | None = None,
) -> dict[str, int]:
    if source not in {"snopes", "poligrafo", "pagella"}:
        raise ValueError(f"unsupported source: {source!r}")
    requests, BeautifulSoup = _dependencies()
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    if output.exists() and output.suffix.lower() == ".csv":
        with output.open(encoding="utf-8-sig", newline="") as stream:
            existing = {
                str(row.get("Article Link", "")) for row in csv.DictReader(stream)
            }
    else:
        existing = {
            str(x.get("fact_check_url")) for x in read_jsonl(output)
        } if output.exists() else set()
    records = []
    skipped = 0

    if source == "pagella":
        for page in range(1, pages + 1):
            url = (
                "https://cdn.pagellapolitica.it/wp-json/wp/v2/dichiarazioni"
                f"?page={page}&per_page=20&_embed=wp:featuredmedia,wp:term"
            )
            for article in _get(session, url, timeout).json():
                if limit is not None and len(records) >= limit:
                    break
                linked = (article.get("acf") or {}).get("articolo") or {}
                linked_id = linked.get("ID") if isinstance(linked, dict) else None
                if linked_id:
                    linked_url = (
                        "https://cdn.pagellapolitica.it/wp-json/wp/v2/posts/"
                        f"{linked_id}?_embed=wp:featuredmedia,wp:term"
                    )
                    try:
                        article = enrich_pagella(
                            article, _get(session, linked_url, timeout).json()
                        )
                    except (ValueError, OSError):
                        pass
                record = parse_pagella(article)
                if record["fact_check_url"] in existing:
                    skipped += 1
                else:
                    records.append(record)
                    existing.add(record["fact_check_url"])
            time.sleep(max(delay, 0.0))
    else:
        parser = parse_snopes if source == "snopes" else parse_poligrafo
        next_url = (
            "https://www.snopes.com/fact-check/"
            if source == "snopes"
            else "https://poligrafo.sapo.pt/fact-checks/"
        )
        marker = "/fact-check/"
        for _ in range(pages):
            soup = BeautifulSoup(_get(session, next_url, timeout).text, "html.parser")
            urls = []
            for node in soup.select("a[href]"):
                url = urljoin(next_url, node.get("href", "")).split("?")[0]
                if marker in url and url.rstrip("/") != next_url.rstrip("/") and url not in urls:
                    urls.append(url)
            for url in urls:
                if limit is not None and len(records) >= limit:
                    break
                if url in existing:
                    skipped += 1
                    continue
                record = parser(_get(session, url, timeout).text, url)
                records.append(record)
                existing.add(url)
                time.sleep(max(delay, 0.0))
            if limit is not None and len(records) >= limit:
                break
            next_node = soup.select_one('a[rel="next"], a.next-button, a.page-numbers.next')
            if not next_node:
                break
            next_url = urljoin(next_url, next_node.get("href", ""))

    if output.suffix.lower() == ".csv":
        append_dataset_csv(output, records)
    else:
        append_jsonl(output, records)
    return {"collected": len(records), "existing": skipped}
