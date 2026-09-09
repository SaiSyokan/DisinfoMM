"""Five-level label harmonization documented in the DisinfoMM paper."""

from __future__ import annotations

import re
from enum import Enum


class FiveLevelLabel(str, Enum):
    TRUE = "True"
    MOSTLY_TRUE = "Mostly True"
    INCOMPLETE = "Incomplete"
    MOSTLY_FALSE = "Mostly False"
    FALSE = "False"
    UNKNOWN = "Unknown"


def _key(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return text.replace("…", "...")


ALIASES: dict[str, FiveLevelLabel] = {
    # Canonical labels and spelling variants in the historical snapshot.
    "true": FiveLevelLabel.TRUE,
    "mostly true": FiveLevelLabel.MOSTLY_TRUE,
    "moslty true, exagerated or missing details": FiveLevelLabel.MOSTLY_TRUE,
    "mostly true, exaggerated or missing details": FiveLevelLabel.MOSTLY_TRUE,
    "incomplete": FiveLevelLabel.INCOMPLETE,
    "mostly false": FiveLevelLabel.MOSTLY_FALSE,
    "moslty false or misleading": FiveLevelLabel.MOSTLY_FALSE,
    "mostly false or misleading": FiveLevelLabel.MOSTLY_FALSE,
    "false": FiveLevelLabel.FALSE,
    "unknown": FiveLevelLabel.UNKNOWN,
    # Snopes source ratings used by the collection snapshot.
    "correct attribution": FiveLevelLabel.TRUE,
    "legit": FiveLevelLabel.TRUE,
    "labeled satire": FiveLevelLabel.MOSTLY_TRUE,
    "research in progress": FiveLevelLabel.INCOMPLETE,
    "recall": FiveLevelLabel.INCOMPLETE,
    "mixture": FiveLevelLabel.MOSTLY_FALSE,
    "outdated": FiveLevelLabel.MOSTLY_FALSE,
    "legend": FiveLevelLabel.MOSTLY_FALSE,
    "originated as satire": FiveLevelLabel.MOSTLY_FALSE,
    "unproven": FiveLevelLabel.FALSE,
    "unfounded": FiveLevelLabel.FALSE,
    "miscaptioned": FiveLevelLabel.FALSE,
    "misattributed": FiveLevelLabel.FALSE,
    "scam": FiveLevelLabel.FALSE,
    "fake": FiveLevelLabel.FALSE,
    "lost legend": FiveLevelLabel.FALSE,
    # Polígrafo source ratings.
    "verdadeiro": FiveLevelLabel.TRUE,
    "verdadeiro, mas...": FiveLevelLabel.MOSTLY_TRUE,
    "missing context": FiveLevelLabel.MOSTLY_TRUE,
    "descontextualizado": FiveLevelLabel.MOSTLY_TRUE,
    "impreciso": FiveLevelLabel.MOSTLY_FALSE,
    "manipulado": FiveLevelLabel.MOSTLY_FALSE,
    "purposefully falsified": FiveLevelLabel.FALSE,
    "pimenta na língua": FiveLevelLabel.FALSE,
    "falso": FiveLevelLabel.FALSE,
}


def normalize_label(value: object, *, strict: bool = False) -> FiveLevelLabel:
    """Return a canonical five-level label, retaining unknowns for review."""

    key = _key(value)
    if key in ALIASES:
        return ALIASES[key]
    if strict:
        raise ValueError(f"Unrecognized veracity label: {value!r}")
    return FiveLevelLabel.UNKNOWN


def to_binary(label: FiveLevelLabel | str) -> int:
    """Map five levels to the paper's binary task (0 authentic, 1 disinformation).

    The exact historical experiment manifests already contain their binary labels
    and remain authoritative for paper reproduction. This function is the cleaned,
    case-insensitive policy for newly prepared data.
    """

    canonical = label if isinstance(label, FiveLevelLabel) else normalize_label(label)
    if canonical in {FiveLevelLabel.TRUE, FiveLevelLabel.MOSTLY_TRUE}:
        return 0
    if canonical in {
        FiveLevelLabel.INCOMPLETE,
        FiveLevelLabel.MOSTLY_FALSE,
        FiveLevelLabel.FALSE,
    }:
        return 1
    raise ValueError("Unknown labels must be reviewed before binary conversion")
