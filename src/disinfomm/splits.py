"""Deterministic stratified split generation."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .io import read_jsonl


def _rank(seed: int, record_id: str) -> str:
    return hashlib.sha256(f"{seed}:{record_id}".encode()).hexdigest()


def make_splits(
    input_path: Path,
    output_dir: Path,
    *,
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
    seed: int = 1111,
) -> dict[str, int]:
    if not 0 < train_ratio < 1 or not 0 <= validation_ratio < 1:
        raise ValueError("ratios must be between 0 and 1")
    if train_ratio + validation_ratio >= 1:
        raise ValueError("train_ratio + validation_ratio must be less than 1")
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for item in read_jsonl(input_path):
        groups[(item.get("language"), item.get("label_binary"))].append(item)
    splits: dict[str, list[dict]] = {"train": [], "validation": [], "test": []}
    for rows in groups.values():
        rows.sort(key=lambda item: _rank(seed, str(item["id"])))
        n_train = int(len(rows) * train_ratio)
        n_validation = int(len(rows) * validation_ratio)
        splits["train"].extend(rows[:n_train])
        splits["validation"].extend(rows[n_train : n_train + n_validation])
        splits["test"].extend(rows[n_train + n_validation :])
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in splits.items():
        rows.sort(key=lambda item: str(item["id"]))
        with (output_dir / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {name: len(rows) for name, rows in splits.items()}
