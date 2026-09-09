"""Paper-aligned multimodal detectors.

Heavy dependencies are imported lazily so data tooling remains usable without a
GPU environment.
"""

from __future__ import annotations

from typing import Any


def _dependencies():
    try:
        import open_clip
        import torch
        from torch import nn
        from torch.nn import functional
    except ImportError as exc:  # pragma: no cover - depends on optional installation
        raise RuntimeError("Install model dependencies with: pip install -e '.[train]'") from exc
    return torch, nn, functional, open_clip


def _output_dim(backbone: Any) -> int:
    visual = getattr(backbone, "visual", None)
    value = getattr(visual, "output_dim", None)
    if value:
        return int(value)
    projection = getattr(backbone, "text_projection", None)
    if projection is not None:
        return int(projection.shape[-1])
    raise ValueError("Unable to infer CLIP embedding dimension")


def build_model(config: dict):
    """Build a detector, image transform, and tokenizers from a config mapping."""

    torch, nn, functional, open_clip = _dependencies()
    model_name = config.get("clip_model", "ViT-B-32")
    pretrained = config.get("pretrained", "openai")
    backbone, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained=pretrained
    )
    variant = config.get("model", "basic_clip")
    dropout = float(config.get("dropout", 0.1))
    if variant == "basic_clip":
        model = _baseline_class(torch, nn, functional)(backbone, dropout)
        tokenizer = open_clip.get_tokenizer(model_name)
    elif variant == "supportive_clip":
        model = _supportive_class(torch, nn, functional)(backbone, dropout)
        tokenizer = open_clip.get_tokenizer(model_name)
    elif variant == "multilingual_clip":
        try:
            from multilingual_clip import pt_multilingual_clip
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install model dependencies with: pip install -e '.[train]'") from exc
        text_name = config.get(
            "multilingual_text_model", "M-CLIP/XLM-Roberta-Large-Vit-L-14"
        )
        text_encoder = pt_multilingual_clip.MultilingualCLIP.from_pretrained(text_name)
        tokenizer = AutoTokenizer.from_pretrained(text_name)
        model = _multilingual_class(torch, nn, functional)(
            backbone,
            text_encoder,
            tokenizer,
            int(config.get("multilingual_dim", 768)),
            dropout,
        )
    else:
        raise ValueError(f"Unknown model variant: {variant!r}")
    return model, preprocess, tokenizer


def _mlp(nn, dim: int, dropout: float):
    return nn.Sequential(
        nn.Dropout(dropout),
        nn.Linear(dim, dim),
        nn.GELU(),
        nn.Dropout(dropout),
        nn.Linear(dim, 1),
    )


def _baseline_class(torch, nn, functional):
    class BaselineCLIPDetector(nn.Module):
        """Section 4.2: LayerNorm, learned image/text fusion, and an MLP."""

        def __init__(self, backbone, dropout: float = 0.1):
            super().__init__()
            self.backbone = backbone
            dim = _output_dim(backbone)
            self.image_norm = nn.LayerNorm(dim)
            self.text_norm = nn.LayerNorm(dim)
            self.alpha_logit = nn.Parameter(torch.tensor(0.0))
            self.classifier = _mlp(nn, dim, dropout)

        def encode(self, images, text_tokens):
            image = self.image_norm(self.backbone.encode_image(images))
            text = self.text_norm(self.backbone.encode_text(text_tokens))
            return functional.normalize(image, dim=-1), functional.normalize(text, dim=-1)

        def student_representation(self, images, text_tokens):
            image, text = self.encode(images, text_tokens)
            alpha = torch.sigmoid(self.alpha_logit)
            return alpha * image + (1.0 - alpha) * text

        def forward(self, images, text_tokens, **_):
            return self.classifier(self.student_representation(images, text_tokens))

    return BaselineCLIPDetector


def _supportive_class(torch, nn, functional):
    Baseline = _baseline_class(torch, nn, functional)

    class SupportiveInformationDetector(Baseline):
        """Section 4.3 teacher–student model with optional explanation input."""

        def __init__(self, backbone, dropout: float = 0.1):
            super().__init__(backbone, dropout)
            dim = _output_dim(backbone)
            self.explanation_norm = nn.LayerNorm(dim)
            self.final_mix_logits = nn.Parameter(torch.zeros(3))

        def representations(self, images, text_tokens, explanation_tokens=None):
            image, text = self.encode(images, text_tokens)
            alpha = torch.sigmoid(self.alpha_logit)
            student = alpha * image + (1.0 - alpha) * text
            if explanation_tokens is None:
                return student, None
            explanation = self.explanation_norm(self.backbone.encode_text(explanation_tokens))
            explanation = functional.normalize(explanation, dim=-1)
            weights = torch.softmax(self.final_mix_logits, dim=0)
            final = weights[0] * image + weights[1] * text + weights[2] * explanation
            return student, (final, explanation)

        def forward(self, images, text_tokens, explanation_tokens=None, use_explanation=True):
            student, supportive = self.representations(images, text_tokens, explanation_tokens)
            representation = supportive[0] if supportive is not None and use_explanation else student
            return self.classifier(representation)

        def objective(self, images, text_tokens, explanation_tokens, labels, lambda_teacher=1.0):
            student, supportive = self.representations(images, text_tokens, explanation_tokens)
            if supportive is None:
                raise ValueError("explanations are required during supportive training")
            final, explanation = supportive
            logits = self.classifier(final).squeeze(-1)
            classification = functional.binary_cross_entropy_with_logits(logits, labels.float())
            teacher = (1.0 - functional.cosine_similarity(student, explanation, dim=-1)).mean()
            return classification + float(lambda_teacher) * teacher, {
                "classification_loss": classification.detach(),
                "teacher_loss": teacher.detach(),
            }

    return SupportiveInformationDetector


def _multilingual_class(torch, nn, functional):
    class MultilingualCLIPDetector(nn.Module):
        """CLIP image encoder plus an XLM-R text encoder and learned projection."""

        def __init__(
            self, backbone, text_encoder, tokenizer, text_dim: int = 768, dropout: float = 0.1
        ):
            super().__init__()
            self.backbone = backbone
            self.text_encoder = text_encoder
            self.tokenizer = tokenizer
            image_dim = _output_dim(backbone)
            self.image_norm = nn.LayerNorm(image_dim)
            self.text_norm = nn.LayerNorm(image_dim)
            self.text_projection = nn.Linear(text_dim, image_dim)
            self.alpha_logit = nn.Parameter(torch.tensor(0.0))
            self.classifier = _mlp(nn, image_dim, dropout)

        def forward(self, images, text_tokens, **_):
            image = functional.normalize(self.image_norm(self.backbone.encode_image(images)), dim=-1)
            encoded = self.text_encoder.forward(text_tokens, self.tokenizer)
            text = functional.normalize(self.text_norm(self.text_projection(encoded)), dim=-1)
            alpha = torch.sigmoid(self.alpha_logit)
            return self.classifier(alpha * image + (1.0 - alpha) * text)

    return MultilingualCLIPDetector
