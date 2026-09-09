"""Input/output helpers for the canonical JSONL release format."""

from __future__ import annotations

import ast
import csv
import gzip
import json
import re
from collections import Counter
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .labels import FiveLevelLabel, normalize_label, to_binary
from .schema import DisinfoMMRecord

SOURCE_LANGUAGE = {"snopes": "en", "pagella": "it", "poligrafo": "pt"}


def _list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, (list, tuple)):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except (SyntaxError, ValueError):
            pass
    return [x.strip() for x in text.split(",") if x.strip()]


def _urls(value: object) -> list[str]:
    return [x for x in _list(value) if urlparse(x).scheme in {"http", "https"}]


def _domains(urls: Iterable[str]) -> list[str]:
    return sorted({urlparse(url).netloc.lower().removeprefix("www.") for url in urls})


def standardize_csv(input_path: Path, output_path: Path) -> Counter[str]:
    """Convert the historical 14-column CSV snapshot into canonical JSONL."""

    counts: Counter[str] = Counter()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open(encoding="utf-8-sig", newline="") as source, output_path.open(
        "w", encoding="utf-8"
    ) as target:
        reader = csv.DictReader(source)
        for row_number, row in enumerate(reader, 1):
            source_name = str(row.get("Website", "")).strip().lower()
            raw_harmonized = row.get("Evaluation", "")
            label = normalize_label(raw_harmonized)
            flags: list[str] = []
            if not str(row.get("Claim", "")).strip():
                flags.append("missing_claim")
            if not str(row.get("Image", "")).strip():
                flags.append("missing_image_url")
            if not str(row.get("Explanation", "")).strip():
                flags.append("missing_explanation")
            if label is FiveLevelLabel.UNKNOWN:
                flags.append("unknown_label")
            binary = None if label is FiveLevelLabel.UNKNOWN else to_binary(label)
            evidence_urls = _urls(row.get("Article sources"))
            record = DisinfoMMRecord(
                id=f"disinfomm-{row_number:06d}",
                source=source_name,
                language=SOURCE_LANGUAGE.get(source_name, ""),
                claim=str(row.get("Claim", "")).strip(),
                label_five=label.value,
                label_binary=binary,
                label_source=str(row.get("Label", "")).strip(),
                explanation=re.sub(r"\s+", " ", str(row.get("Explanation", ""))).strip(),
                image_url=str(row.get("Image", "")).strip(),
                fact_check_url=str(row.get("Article Link", "")).strip(),
                published_at=str(row.get("Date", "")).strip(),
                claim_source_url=str(row.get("Declaration Link", "")).strip(),
                keywords=_list(row.get("Keywords")),
                tags=_list(row.get("Tags")),
                evidence_urls=evidence_urls,
                evidence_domains=_domains(evidence_urls) or _list(row.get("Process")),
                quality_flags=flags,
                source_num=str(row.get("Num", "")).strip(),
            )
            target.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            counts["records"] += 1
            counts[f"source:{source_name}"] += 1
            counts[f"label:{label.value}"] += 1
            for flag in flags:
                counts[f"flag:{flag}"] += 1
    return counts


def read_jsonl(path: Path) -> Iterator[dict]:
    opener = gzip.open if path.suffix == ".gz" else Path.open
    kwargs = {"mode": "rt", "encoding": "utf-8"} if path.suffix == ".gz" else {"encoding": "utf-8"}
    with opener(path, **kwargs) as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def append_jsonl(path: Path, records: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("a", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


DATASET_COLUMNS = [
    "Num", "Website", "Date", "Image", "Claim", "Evaluation", "Label",
    "Keywords", "Tags", "Article Link", "Declaration Link", "Explanation",
    "Article sources", "Process",
]


def append_dataset_csv(path: Path, records: Iterable[dict]) -> int:
    """Append collected canonical records using the original Dataset.csv columns."""

    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    count = 0
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=DATASET_COLUMNS)
        if write_header:
            writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "Num": record.get("source_num") or record.get("id", ""),
                    "Website": record.get("source", ""),
                    "Date": record.get("published_at", ""),
                    "Image": record.get("image_url", ""),
                    "Claim": record.get("claim", ""),
                    "Evaluation": record.get("label_five", "Unknown"),
                    "Label": record.get("label_source", ""),
                    "Keywords": ",".join(record.get("keywords", [])),
                    "Tags": ",".join(record.get("tags", [])),
                    "Article Link": record.get("fact_check_url", ""),
                    "Declaration Link": record.get("claim_source_url", ""),
                    "Explanation": record.get("explanation", ""),
                    "Article sources": ",".join(record.get("evidence_urls", [])),
                    "Process": ",".join(record.get("evidence_domains", [])),
                }
            )
            count += 1
    return count


def harmonize_csv(input_path: Path, output_path: Path) -> dict:
    """Normalize the Evaluation column while preserving the original CSV schema."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    with input_path.open(encoding="utf-8-sig", newline="") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header")
        missing = set(DATASET_COLUMNS) - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
        writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            label = normalize_label(row.get("Evaluation", ""))
            if label is FiveLevelLabel.UNKNOWN:
                label = normalize_label(row.get("Label", ""))
            row["Evaluation"] = label.value
            writer.writerow(row)
            counts["records"] += 1
            counts[f"label:{label.value}"] += 1
    return dict(sorted(counts.items()))


def write_source_link_lists(
    csv_path: Path,
    output_dir: Path,
    *,
    frequent_threshold: int = 100,
    important_threshold: int = 300,
) -> dict:
    """Rebuild the paper's all/frequent/important evidence-domain lists."""

    output_dir.mkdir(parents=True, exist_ok=True)
    links: list[str] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            links.extend(_urls(row.get("Article sources")))
    domain_counts = Counter(
        urlparse(url).netloc.lower().removeprefix("www.") for url in links
    )
    with (output_dir / "all_links.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["url"])
        writer.writerows([url] for url in links)
    for filename, threshold in (
        ("frequent_domains.csv", frequent_threshold),
        ("important_domains.csv", important_threshold),
    ):
        with (output_dir / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["domain", "count"])
            writer.writerows(
                (domain, count)
                for domain, count in sorted(domain_counts.items(), key=lambda item: (-item[1], item[0]))
                if count > threshold
            )
    return {
        "links": len(links),
        "domains": len(domain_counts),
        "frequent_domains": sum(count > frequent_threshold for count in domain_counts.values()),
        "important_domains": sum(count > important_threshold for count in domain_counts.values()),
    }


def validate_jsonl(path: Path, *, require_binary: bool = False) -> dict:
    ids: set[str] = set()
    errors: list[str] = []
    warnings: list[str] = []
    counts: Counter[str] = Counter()
    for line_number, item in enumerate(read_jsonl(path), 1):
        try:
            record = DisinfoMMRecord.from_dict(item)
        except (KeyError, TypeError) as exc:
            errors.append(f"line {line_number}: schema error: {exc}")
            continue
        if record.id in ids:
            errors.append(f"line {line_number}: duplicate id {record.id!r}")
        ids.add(record.id)
        for issue in record.validate(require_binary=require_binary):
            flagged = (
                (issue == "claim is empty" and "missing_claim" in record.quality_flags)
                or (issue == "label_binary is required" and "unknown_label" in record.quality_flags)
            )
            if not flagged or require_binary:
                errors.append(f"line {line_number}: {issue}")
        for flag in record.quality_flags:
            warnings.append(f"line {line_number}: quality flag: {flag}")
        counts["records"] += 1
        counts[f"source:{record.source}"] += 1
        counts[f"language:{record.language}"] += 1
        counts[f"label:{record.label_five}"] += 1
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": dict(sorted(counts.items())),
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
