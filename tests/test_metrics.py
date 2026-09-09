import pytest

from disinfomm.metrics import binary_metrics


def test_binary_metrics_matches_paper_convention():
    result = binary_metrics([0, 0, 1, 1], [0, 1, 1, 1])
    assert result["accuracy"] == 75.0
    assert result["authentic_accuracy"] == 50.0
    assert result["disinformation_accuracy"] == 100.0


def test_binary_metrics_rejects_bad_inputs():
    with pytest.raises(ValueError):
        binary_metrics([0], [0, 1])
