import json

from disinfomm.splits import make_splits


def test_splits_are_deterministic_and_disjoint(tmp_path):
    manifest = tmp_path / "all.jsonl"
    rows = []
    for i in range(40):
        rows.append({"id": f"x-{i}", "language": "en" if i < 20 else "pt", "label_binary": i % 2})
    manifest.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
    first, second = tmp_path / "first", tmp_path / "second"
    assert make_splits(manifest, first) == make_splits(manifest, second)
    seen = set()
    for name in ("train", "validation", "test"):
        assert (first / f"{name}.jsonl").read_bytes() == (second / f"{name}.jsonl").read_bytes()
        ids = {json.loads(line)["id"] for line in (first / f"{name}.jsonl").read_text().splitlines()}
        assert not seen.intersection(ids)
        seen.update(ids)
    assert len(seen) == 40
