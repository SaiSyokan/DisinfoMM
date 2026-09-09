import csv
import json

from disinfomm.io import standardize_csv, validate_jsonl


def test_standardize_and_validate(tmp_path):
    source = tmp_path / "source.csv"
    fields = [
        "Num", "Website", "Date", "Image", "Claim", "Evaluation", "Label",
        "Keywords", "Tags", "Article Link", "Declaration Link", "Explanation",
        "Article sources", "Process",
    ]
    with source.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "Num": "7", "Website": "poligrafo", "Date": "2025-01-01",
                "Image": "https://example.org/image.jpg", "Claim": "Uma alegação.",
                "Evaluation": "Mostly True", "Label": "Descontextualizado",
                "Keywords": "politica,economia", "Tags": "", "Article Link": "https://example.org/fact/7",
                "Declaration Link": "", "Explanation": "Uma explicação.",
                "Article sources": "https://evidence.example/a,https://evidence.example/b",
                "Process": "evidence.example",
            }
        )
    output = tmp_path / "records.jsonl"
    counts = standardize_csv(source, output)
    assert counts["records"] == 1
    row = json.loads(output.read_text(encoding="utf-8"))
    assert row["language"] == "pt"
    assert row["label_binary"] == 0
    assert row["keywords"] == ["politica", "economia"]
    assert validate_jsonl(output)["valid"]


def test_flagged_missing_claim_is_a_warning(tmp_path):
    path = tmp_path / "flagged.jsonl"
    row = {
        "id": "x", "source": "snopes", "language": "en", "claim": "",
        "label_five": "Unknown", "label_binary": None, "label_source": "",
        "explanation": "text", "image_url": "", "fact_check_url": "https://example.org/x",
        "quality_flags": ["missing_claim", "unknown_label"],
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    result = validate_jsonl(path)
    assert result["valid"]
    assert result["warnings"] == [
        "line 1: quality flag: missing_claim",
        "line 1: quality flag: unknown_label",
    ]
