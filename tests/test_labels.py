import pytest

from disinfomm.labels import FiveLevelLabel, normalize_label, to_binary


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("True", FiveLevelLabel.TRUE),
        ("Mostly true", FiveLevelLabel.MOSTLY_TRUE),
        ("Moslty true, exagerated or missing details", FiveLevelLabel.MOSTLY_TRUE),
        ("Descontextualizado", FiveLevelLabel.MOSTLY_TRUE),
        ("Impreciso", FiveLevelLabel.MOSTLY_FALSE),
        ("Miscaptioned", FiveLevelLabel.FALSE),
    ],
)
def test_normalize_label(raw, expected):
    assert normalize_label(raw) is expected


def test_binary_policy():
    assert to_binary("True") == 0
    assert to_binary("Mostly True") == 0
    assert to_binary("Incomplete") == 1
    assert to_binary("False") == 1
    with pytest.raises(ValueError):
        to_binary("unmapped label")
