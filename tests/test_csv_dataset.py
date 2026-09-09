import csv
import json

from disinfomm.csv_dataset import prepare_experiment_splits, read_dataset_csv
from disinfomm.download import download_images
from disinfomm.io import DATASET_COLUMNS, harmonize_csv, write_source_link_lists


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(index, evaluation, source="snopes"):
    return {
        "Num": str(index),
        "Website": source,
        "Date": "2025-01-01",
        "Image": f"https://example.org/{index}.jpg",
        "Claim": f"claim {index}",
        "Evaluation": evaluation,
        "Label": evaluation,
        "Keywords": "topic",
        "Tags": "",
        "Article Link": f"https://fact.example/{index}",
        "Declaration Link": "",
        "Explanation": f"explanation {index}",
        "Article sources": "https://evidence.example/a",
        "Process": "evidence.example",
    }


def test_csv_first_preparation_is_balanced_and_deterministic(tmp_path):
    source = tmp_path / "Dataset.csv"
    rows = [_row(i, "True" if i <= 10 else "False") for i in range(1, 21)]
    _write_csv(source, rows)

    first, second = tmp_path / "first", tmp_path / "second"
    result = prepare_experiment_splits(source, first, regime="english", size=10, seed=7)
    prepare_experiment_splits(source, second, regime="english", size=10, seed=7)

    assert result["selected_authentic"] == result["selected_disinformation"] == 5
    assert result["splits"] == {"train": 8, "validation": 0, "test": 2}
    for relative in (
        "jsonl/train.jsonl",
        "jsonl/validation.jsonl",
        "jsonl/test.jsonl",
        "legacy/data.json",
        "legacy/train.json",
        "legacy/val.json",
        "legacy/test.json",
        "audit.json",
    ):
        assert (first / relative).read_bytes() == (second / relative).read_bytes()
    train_rows = [json.loads(line) for line in (first / "jsonl/train.jsonl").read_text().splitlines()]
    assert {row["label_binary"] for row in train_rows} == {0, 1}


def test_harmonization_and_source_lists(tmp_path):
    source = tmp_path / "Dataset.csv"
    _write_csv(source, [_row(1, "Moslty false or misleading")])
    output = tmp_path / "harmonized.csv"
    counts = harmonize_csv(source, output)
    assert counts["label:Mostly False"] == 1
    assert next(iter(read_dataset_csv(output)))["label_binary"] == 1

    lists = tmp_path / "lists"
    result = write_source_link_lists(
        output, lists, frequent_threshold=0, important_threshold=0
    )
    assert result["frequent_domains"] == 1
    assert "evidence.example" in (lists / "important_domains.csv").read_text()


def test_downloader_accepts_dataset_csv(tmp_path):
    source = tmp_path / "Dataset.csv"
    row = _row(1, "True")
    row["Image"] = ""
    _write_csv(source, [row])
    assert download_images(source, tmp_path / "media", delay=0) == {
        "downloaded": 0,
        "existing": 0,
        "failed": 0,
        "skipped": 1,
    }
