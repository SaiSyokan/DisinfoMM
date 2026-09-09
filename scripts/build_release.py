"""Build the canonical dataset snapshot and exact paper pair manifests.

This maintainer tool consumes the author-held historical files. It is not needed
by dataset users after a release has been published.
"""

from __future__ import annotations

import argparse
import difflib
import gzip
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path

from disinfomm.io import read_jsonl, standardize_csv


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compress_jsonl(root: Path) -> None:
    for path in root.rglob("*.jsonl"):
        target = path.with_suffix(path.suffix + ".gz")
        with path.open("rb") as source, target.open("wb") as raw, gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0
        ) as output:
            shutil.copyfileobj(source, output)
        path.unlink()


def write_checksums(root: Path) -> None:
    files = sorted(
        path for path in root.rglob("*") if path.is_file() and path.name != "checksums.sha256"
    )
    text = "".join(f"{sha256(path)}  {path.relative_to(root)}\n" for path in files)
    (root / "checksums.sha256").write_text(text, encoding="utf-8")


def align(legacy: list[dict], current: list[dict]) -> tuple[dict[str, int], dict]:
    left = [normalize(x.get("caption", "")) for x in legacy]
    right = [normalize(x.get("claim", "")) for x in current]
    matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
    mapping: dict[str, int] = {}
    replacements = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for old_index, new_index in zip(range(i1, i2), range(j1, j2)):
                mapping[str(legacy[old_index]["id"])] = new_index
                replacements += int(tag == "replace")
    return mapping, {
        "legacy_records": len(legacy),
        "canonical_records": len(current),
        "aligned": len(mapping),
        "unaligned": len(legacy) - len(mapping),
        "one_to_one_replacements": replacements,
        "sequence_ratio": matcher.ratio(),
    }


def build_pairs(
    annotations_dir: Path,
    regime: str,
    suffix: str,
    legacy_by_id: dict[str, dict],
    alignment: dict[str, int],
    canonical: list[dict],
    output: Path,
) -> dict[str, int]:
    counts = {}
    for stem, public_name in (("train", "train"), ("val", "validation"), ("test", "test")):
        source_name = f"{stem}{suffix}.json"
        annotations = json.loads((annotations_dir / source_name).read_text(encoding="utf-8"))["annotations"]
        target = output / regime / f"{public_name}.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as stream:
            for position, annotation in enumerate(annotations, 1):
                claim_id = str(annotation["id"])
                image_id = str(annotation["image_id"])
                claim_legacy = legacy_by_id[claim_id]
                claim_row = canonical[alignment[claim_id]] if claim_id in alignment else {}
                image_row = canonical[alignment[image_id]] if image_id in alignment else {}
                pair = {
                    "id": f"{regime}-{public_name}-{position:06d}",
                    "split": public_name,
                    "regime": regime,
                    "claim": claim_legacy["caption"],
                    "explanation": claim_row.get("explanation", ""),
                    "label_five": claim_row.get("label_five", "Unknown"),
                    "label_binary": int(bool(annotation["falsified"])),
                    "source": claim_row.get("source", ""),
                    "language": claim_row.get("language", ""),
                    "fact_check_url": claim_row.get("fact_check_url", ""),
                    "image_url": image_row.get("image_url", ""),
                    "claim_record_id": claim_row.get("id", f"legacy-{claim_id}"),
                    "image_record_id": image_row.get("id", f"legacy-{image_id}"),
                    "legacy_claim_id": claim_id,
                    "legacy_image_id": image_id,
                    "quality_flags": ([] if claim_id in alignment and image_id in alignment else ["legacy_alignment_missing"]),
                }
                stream.write(json.dumps(pair, ensure_ascii=False) + "\n")
        counts[public_name] = len(annotations)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--legacy-data", type=Path, required=True)
    parser.add_argument("--english", type=Path, required=True)
    parser.add_argument("--multilingual", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data_dir = args.output / "data"
    canonical_path = data_dir / "disinfomm-v1.0.0.jsonl"
    counts = standardize_csv(args.csv, canonical_path)
    canonical = list(read_jsonl(canonical_path))
    legacy = json.loads(args.legacy_data.read_text(encoding="utf-8"))
    legacy_by_id = {str(x["id"]): x for x in legacy}
    alignment, alignment_stats = align(legacy, canonical)
    split_stats = {
        "english": build_pairs(args.english, "english", "", legacy_by_id, alignment, canonical, args.output / "paper_splits"),
        "multilingual": build_pairs(args.multilingual, "multilingual", "_mul", legacy_by_id, alignment, canonical, args.output / "paper_splits"),
    }
    provenance = {
        "inputs": {
            "csv_sha256": sha256(args.csv),
            "legacy_data_sha256": sha256(args.legacy_data),
            "english_split_sha256": {x: sha256(args.english / x) for x in ("train.json", "val.json", "test.json")},
            "multilingual_split_sha256": {x: sha256(args.multilingual / x) for x in ("train_mul.json", "val_mul.json", "test_mul.json")},
        },
        "canonical_counts": dict(counts),
        "alignment": alignment_stats,
        "paper_splits": split_stats,
    }
    (args.output / "metadata").mkdir(parents=True, exist_ok=True)
    (args.output / "metadata" / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    compress_jsonl(args.output)
    write_checksums(args.output)
    print(json.dumps(provenance, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
