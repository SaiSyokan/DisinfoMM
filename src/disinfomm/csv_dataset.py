"""CSV-first access and deterministic experiment subset construction."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from .io import SOURCE_LANGUAGE, _list, _urls
from .labels import FiveLevelLabel, normalize_label, to_binary


def _rank(seed: int, record_id: str) -> str:
    return hashlib.sha256(f"{seed}:{record_id}".encode()).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_dataset_csv(path: Path):
    """Yield experiment-ready records without changing the archival CSV."""

    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row_number, row in enumerate(csv.DictReader(stream), 1):
            source = str(row.get("Website", "")).strip().lower()
            source_num = str(row.get("Num", "")).strip()
            record_id = source_num or f"row-{row_number:06d}"
            evaluation = normalize_label(row.get("Evaluation", ""))
            if evaluation is FiveLevelLabel.UNKNOWN:
                evaluation = normalize_label(row.get("Label", ""))
            claim = str(row.get("Claim", "")).strip()
            explanation = " ".join(str(row.get("Explanation", "")).split())
            image_url = str(row.get("Image", "")).strip()
            flags = []
            if not claim:
                flags.append("missing_claim")
            if not image_url or urlparse(image_url).scheme not in {"http", "https"}:
                flags.append("invalid_image_url")
            if not explanation:
                flags.append("missing_explanation")
            if evaluation is FiveLevelLabel.UNKNOWN:
                flags.append("unknown_label")
            yield {
                "id": record_id,
                "source_num": source_num,
                "source": source,
                "language": SOURCE_LANGUAGE.get(source, ""),
                "claim": claim,
                "explanation": explanation,
                "label_five": evaluation.value,
                "label_binary": (
                    None if evaluation is FiveLevelLabel.UNKNOWN else to_binary(evaluation)
                ),
                "label_source": str(row.get("Label", "")).strip(),
                "image_url": image_url,
                "image_path": f"{record_id}.jpg",
                "fact_check_url": str(row.get("Article Link", "")).strip(),
                "claim_source_url": str(row.get("Declaration Link", "")).strip(),
                "published_at": str(row.get("Date", "")).strip(),
                "keywords": _list(row.get("Keywords")),
                "tags": _list(row.get("Tags")),
                "evidence_urls": _urls(row.get("Article sources")),
                "evidence_domains": _list(row.get("Process")),
                "quality_flags": flags,
            }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def _split(rows: list[dict], seed: int) -> dict[str, list[dict]]:
    """Create exact 8:1:1 splits while preserving the selected class balance."""

    result = {"train": [], "validation": [], "test": []}
    for label in (0, 1):
        group = sorted(
            (row for row in rows if row["label_binary"] == label),
            key=lambda row: _rank(seed + 1, str(row["id"])),
        )
        train_end = int(len(group) * 0.8)
        validation_end = train_end + int(len(group) * 0.1)
        result["train"].extend(group[:train_end])
        result["validation"].extend(group[train_end:validation_end])
        result["test"].extend(group[validation_end:])
    for split_rows in result.values():
        split_rows.sort(key=lambda row: _rank(seed + 2, str(row["id"])))
    return result


def prepare_experiment_splits(
    csv_path: Path,
    output_dir: Path,
    *,
    regime: str,
    size: int,
    fake_ratio: float = 0.5,
    seed: int = 1111,
) -> dict:
    """Select a task subset from Dataset.csv and write modern and legacy JSON.

    The full CSV remains authoritative. Generated JSON files are disposable,
    deterministic experiment inputs.
    """

    if regime not in {"english", "multilingual"}:
        raise ValueError("regime must be 'english' or 'multilingual'")
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 < fake_ratio < 1:
        raise ValueError("fake_ratio must be between 0 and 1")

    all_rows = list(read_dataset_csv(csv_path))
    language_rows = [
        row
        for row in all_rows
        if regime == "multilingual" or row["language"] == "en"
    ]
    exclusions = Counter()
    eligible = []
    for row in language_rows:
        blocking = {
            flag
            for flag in row["quality_flags"]
            if flag
            in {
                "missing_claim",
                "missing_explanation",
                "invalid_image_url",
                "unknown_label",
            }
        }
        if blocking:
            for flag in blocking:
                exclusions[flag] += 1
        else:
            eligible.append(row)

    fake_count = round(size * fake_ratio)
    authentic_count = size - fake_count
    requested = {0: authentic_count, 1: fake_count}
    selected = []
    available = Counter(row["label_binary"] for row in eligible)
    for label, count in requested.items():
        candidates = sorted(
            (row for row in eligible if row["label_binary"] == label),
            key=lambda row: _rank(seed, str(row["id"])),
        )
        if len(candidates) < count:
            name = "authentic" if label == 0 else "disinformation"
            raise ValueError(f"requested {count} {name} rows but only {len(candidates)} are eligible")
        selected.extend(candidates[:count])

    splits = _split(selected, seed)
    jsonl_dir = output_dir / "jsonl"
    for name, rows in splits.items():
        _write_jsonl(jsonl_dir / f"{name}.jsonl", rows)

    legacy_dir = output_dir / "legacy"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    selected_by_id = {str(row["id"]): row for row in selected}
    catalog = [
        {
            "id": row["id"],
            "caption": row["claim"],
            "explanation": row["explanation"],
            "image_id": row["id"],
            "image_path": row["image_path"],
            "image_url": row["image_url"],
            "website": row["source"],
            "evaluation": row["label_five"],
        }
        for row in sorted(selected_by_id.values(), key=lambda row: str(row["id"]))
    ]
    (legacy_dir / "data.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name, rows in splits.items():
        legacy_name = "val" if name == "validation" else name
        annotations = {
            "annotations": [
                {"id": row["id"], "image_id": row["id"], "falsified": bool(row["label_binary"])}
                for row in rows
            ]
        }
        (legacy_dir / f"{legacy_name}.json").write_text(
            json.dumps(annotations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    counts = {
        "regime": regime,
        "seed": seed,
        "requested_size": size,
        "fake_ratio": fake_ratio,
        "csv_sha256": _sha256_file(csv_path),
        "input_records": len(all_rows),
        "regime_records": len(language_rows),
        "eligible_records": len(eligible),
        "available_authentic": available[0],
        "available_disinformation": available[1],
        "excluded": dict(sorted(exclusions.items())),
        "selected": len(selected),
        "selected_authentic": authentic_count,
        "selected_disinformation": fake_count,
        "splits": {name: len(rows) for name, rows in splits.items()},
        "sources": dict(sorted(Counter(row["source"] for row in selected).items())),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audit.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return counts
