"""Paper-aligned binary accuracy metrics."""

from __future__ import annotations


def binary_metrics(labels: list[int], predictions: list[int]) -> dict[str, float | int]:
    if len(labels) != len(predictions):
        raise ValueError("labels and predictions must have the same length")
    if not labels:
        raise ValueError("at least one prediction is required")
    for value in labels + predictions:
        if value not in {0, 1}:
            raise ValueError("binary metrics accept only 0 and 1")
    correct = sum(a == b for a, b in zip(labels, predictions))
    result: dict[str, float | int] = {
        "n": len(labels),
        "accuracy": 100.0 * correct / len(labels),
    }
    for label, name in ((0, "authentic_accuracy"), (1, "disinformation_accuracy")):
        indices = [i for i, value in enumerate(labels) if value == label]
        result[name] = (
            100.0 * sum(predictions[i] == label for i in indices) / len(indices)
            if indices
            else float("nan")
        )
    return result
