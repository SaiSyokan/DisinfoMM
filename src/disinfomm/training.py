"""Config-driven training and evaluation entry points."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import yaml

from .io import read_jsonl
from .metrics import binary_metrics
from .models import build_model


def load_config(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("training config must be a YAML mapping")
    base = path.parent
    for key in ("train_manifest", "validation_manifest", "test_manifest", "media_root", "run_dir"):
        if key in value and value[key] and not Path(value[key]).is_absolute():
            value[key] = str((base / value[key]).resolve())
    return value


def _torch_dependencies():
    try:
        import torch
        from PIL import Image
        from torch.utils.data import DataLoader, Dataset
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install model dependencies with: pip install -e '.[train]'") from exc
    return torch, Image, DataLoader, Dataset


def run(config_path: Path, *, evaluate_only: bool = False, checkpoint: Path | None = None) -> dict:
    torch, Image, DataLoader, Dataset = _torch_dependencies()
    config = load_config(config_path)
    seed = int(config.get("seed", 1111))
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    device = torch.device(config.get("device") or ("cuda" if torch.cuda.is_available() else "cpu"))
    model, preprocess, tokenizer = build_model(config)
    model.to(device)

    class ManifestDataset(Dataset):
        def __init__(self, path: str):
            self.rows = list(read_jsonl(Path(path)))
            self.media_root = Path(config.get("media_root", "."))

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, index):
            row = self.rows[index]
            image_path = Path(row.get("image_path", ""))
            if str(image_path) and not image_path.is_absolute():
                image_path = self.media_root / image_path
            if not str(row.get("image_path", "")) or not image_path.exists():
                media_id = str(row.get("image_record_id") or row.get("id"))
                matches = sorted(self.media_root.glob(f"{media_id}.*"))
                if not matches:
                    raise FileNotFoundError(
                        f"No downloaded media for {media_id!r} in {self.media_root}"
                    )
                image_path = matches[0]
            with Image.open(image_path) as image:
                image_tensor = preprocess(image.convert("RGB"))
            return row, image_tensor

    multilingual = config.get("model") in {"comparison_multilingual", "multilingual_clip"}

    def collate(batch):
        rows, images = zip(*batch)
        claims = [str(x["claim"]) for x in rows]
        explanations = [str(x.get("explanation", "")) for x in rows]
        if multilingual:
            tokens = claims
            explanation_tokens = None
        else:
            tokens = tokenizer(claims)
            explanation_tokens = tokenizer(explanations)
        labels = torch.tensor([int(x["label_binary"]) for x in rows], dtype=torch.float32)
        return torch.stack(images), tokens, explanation_tokens, labels

    def loader(key: str, shuffle: bool):
        return DataLoader(
            ManifestDataset(config[key]),
            batch_size=int(config.get("batch_size", 64)),
            shuffle=shuffle,
            num_workers=int(config.get("num_workers", 6)),
            pin_memory=device.type == "cuda",
            collate_fn=collate,
        )

    def move_tokens(value):
        if isinstance(value, dict):
            return {key: tensor.to(device) for key, tensor in value.items()}
        return value if isinstance(value, list) else value.to(device)

    def evaluate(data_loader, *, use_explanation=False):
        model.eval()
        labels_all: list[int] = []
        predictions: list[int] = []
        with torch.no_grad():
            for images, tokens, explanation_tokens, labels in data_loader:
                images, tokens = images.to(device), move_tokens(tokens)
                explanation_tokens = (
                    move_tokens(explanation_tokens) if explanation_tokens is not None else None
                )
                logits = model(
                    images,
                    tokens,
                    explanation_tokens=explanation_tokens,
                    use_explanation=use_explanation,
                ).squeeze(-1)
                predictions.extend((torch.sigmoid(logits) >= 0.5).long().cpu().tolist())
                labels_all.extend(labels.long().tolist())
        return binary_metrics(labels_all, predictions)

    run_dir = Path(config.get("run_dir", "runs/default"))
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint or (run_dir / "best.pt")
    if evaluate_only:
        state = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(state.get("model", state))
        result = evaluate(loader("test_manifest", False))
        (run_dir / "test_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    train_loader = loader("train_manifest", True)
    validation_loader = loader("validation_manifest", False)
    classifier_parameters = []
    backbone_parameters = []
    for name, parameter in model.named_parameters():
        (classifier_parameters if any(x in name for x in ("classifier", "alpha", "projection")) else backbone_parameters).append(parameter)
    optimizer = torch.optim.Adam(
        [
            {"params": backbone_parameters, "lr": float(config.get("lr_backbone", 5e-7))},
            {"params": classifier_parameters, "lr": float(config.get("lr_classifier", 5e-5))},
        ],
        weight_decay=float(config.get("weight_decay", 1.2e-6)),
    )
    criterion = torch.nn.BCEWithLogitsLoss()
    best = -1.0
    history_path = run_dir / "history.jsonl"
    for epoch in range(1, int(config.get("epochs", 30)) + 1):
        model.train()
        total_loss = 0.0
        for images, tokens, explanation_tokens, labels in train_loader:
            images, tokens, labels = images.to(device), move_tokens(tokens), labels.to(device)
            explanation_tokens = (
                move_tokens(explanation_tokens) if explanation_tokens is not None else None
            )
            optimizer.zero_grad(set_to_none=True)
            if config.get("model") in {"proposed_with_evidence", "supportive_clip"}:
                loss, _ = model.objective(
                    images,
                    tokens,
                    explanation_tokens,
                    labels,
                    lambda_teacher=float(config.get("lambda_teacher", 1.0)),
                )
            else:
                logits = model(images, tokens).squeeze(-1)
                loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach())
        metrics = evaluate(validation_loader)
        event: dict[str, Any] = {
            "epoch": epoch,
            "train_loss": total_loss / max(1, len(train_loader)),
            **metrics,
        }
        with history_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event) + "\n")
        if float(metrics["accuracy"]) > best:
            best = float(metrics["accuracy"])
            torch.save({"model": model.state_dict(), "config": config, "epoch": epoch}, checkpoint_path)
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state["model"])
    result = evaluate(loader("test_manifest", False))
    (run_dir / "test_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
