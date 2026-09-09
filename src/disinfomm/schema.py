"""Canonical record schema and validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse

from .labels import FiveLevelLabel


@dataclass(slots=True)
class DisinfoMMRecord:
    id: str
    source: str
    language: str
    claim: str
    label_five: str
    label_binary: int | None
    label_source: str
    explanation: str
    image_url: str
    fact_check_url: str
    published_at: str = ""
    claim_source_url: str = ""
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    evidence_urls: list[str] = field(default_factory=list)
    evidence_domains: list[str] = field(default_factory=list)
    collected_at: str = ""
    quality_flags: list[str] = field(default_factory=list)
    source_num: str = ""

    def validate(self, *, require_binary: bool = False) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("id is empty")
        if self.source not in {"snopes", "pagella", "poligrafo"}:
            errors.append(f"unsupported source: {self.source!r}")
        if self.language not in {"en", "it", "pt"}:
            errors.append(f"unsupported language: {self.language!r}")
        if not self.claim.strip():
            errors.append("claim is empty")
        if self.label_five not in {x.value for x in FiveLevelLabel}:
            errors.append(f"invalid label_five: {self.label_five!r}")
        if self.label_binary not in {None, 0, 1}:
            errors.append(f"invalid label_binary: {self.label_binary!r}")
        if require_binary and self.label_binary is None:
            errors.append("label_binary is required")
        for name in ("image_url", "fact_check_url"):
            value = getattr(self, name)
            if value and urlparse(value).scheme not in {"http", "https"}:
                errors.append(f"{name} is not an HTTP(S) URL")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DisinfoMMRecord:
        fields = cls.__dataclass_fields__
        return cls(**{key: value[key] for key in fields if key in value})
