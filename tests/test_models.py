import pytest

torch = pytest.importorskip("torch")
from torch import nn
from torch.nn import functional

from disinfomm.models import _baseline_class, _supportive_class


class TinyBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.visual = type("Visual", (), {"output_dim": 4})()
        self.image = nn.Linear(3, 4)
        self.text = nn.Embedding(16, 4)

    def encode_image(self, value):
        return self.image(value)

    def encode_text(self, value):
        return self.text(value).mean(dim=1)


def test_baseline_forward_shape():
    model = _baseline_class(torch, nn, functional)(TinyBackbone(), dropout=0.0)
    assert model(torch.randn(2, 3), torch.tensor([[1, 2], [3, 4]])).shape == (2, 1)


def test_supportive_objective_backpropagates():
    model = _supportive_class(torch, nn, functional)(TinyBackbone(), dropout=0.0)
    loss, parts = model.objective(
        torch.randn(2, 3),
        torch.tensor([[1, 2], [3, 4]]),
        torch.tensor([[5, 6], [7, 8]]),
        torch.tensor([0.0, 1.0]),
    )
    loss.backward()
    assert set(parts) == {"classification_loss", "teacher_loss"}
    assert torch.isfinite(loss)
