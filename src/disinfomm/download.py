"""Resumable media download with checksums and failure logging."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import time
import urllib.request
from pathlib import Path

from .io import read_jsonl, utc_now


def download_images(
    manifest: Path,
    output: Path,
    *,
    timeout: float = 30.0,
    delay: float = 0.25,
    user_agent: str = "DisinfoMM/1.0 (+https://github.com/SaiSyokan/DisinfoMM)",
    limit: int | None = None,
) -> dict[str, int]:
    output.mkdir(parents=True, exist_ok=True)
    failures = output / "download_failures.jsonl"
    index_path = output / "media_index.jsonl"
    counts = {"downloaded": 0, "existing": 0, "failed": 0, "skipped": 0}
    for position, record in enumerate(read_jsonl(manifest)):
        if limit is not None and position >= limit:
            break
        url = str(record.get("image_url", ""))
        if not url:
            counts["skipped"] += 1
            continue
        base = str(record.get("id", f"row-{position:06d}"))
        matches = list(output.glob(f"{base}.*"))
        if matches:
            counts["existing"] += 1
            continue
        try:
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read()
                content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                raise ValueError(f"unexpected content type {content_type!r}")
            extension = mimetypes.guess_extension(content_type) or ".jpg"
            path = output / f"{base}{extension}"
            path.write_bytes(content)
            event = {
                "id": base,
                "path": path.name,
                "source_url": url,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "downloaded_at": utc_now(),
            }
            with index_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            counts["downloaded"] += 1
        except (OSError, ValueError) as exc:  # network failures are expected and auditable
            with failures.open("a", encoding="utf-8") as stream:
                stream.write(
                    json.dumps({"id": base, "url": url, "error": str(exc)}, ensure_ascii=False)
                    + "\n"
                )
            counts["failed"] += 1
        time.sleep(max(0.0, delay))
    return counts
