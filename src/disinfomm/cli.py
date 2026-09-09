"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .collection import collect
from .download import download_images
from .io import read_jsonl, standardize_csv, validate_jsonl
from .metrics import binary_metrics
from .splits import make_splits


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="disinfomm")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("standardize", help="convert the historical CSV to canonical JSONL")
    command.add_argument("input", type=Path)
    command.add_argument("output", type=Path)

    command = sub.add_parser("validate", help="validate a canonical JSONL manifest")
    command.add_argument("manifest", type=Path)
    command.add_argument("--require-binary", action="store_true")

    command = sub.add_parser("make-splits", help="make deterministic 8:1:1-style splits")
    command.add_argument("manifest", type=Path)
    command.add_argument("output", type=Path)
    command.add_argument("--train-ratio", type=float, default=0.8)
    command.add_argument("--validation-ratio", type=float, default=0.1)
    command.add_argument("--seed", type=int, default=1111)

    command = sub.add_parser("evaluate", help="evaluate JSONL label/prediction pairs")
    command.add_argument("predictions", type=Path)
    command.add_argument("--label-field", default="label_binary")
    command.add_argument("--prediction-field", default="prediction")

    command = sub.add_parser("download-images", help="download media referenced by a manifest")
    command.add_argument("manifest", type=Path)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--delay", type=float, default=0.25)

    command = sub.add_parser("collect", help="collect current fact-check records incrementally")
    command.add_argument("source", choices=["snopes", "poligrafo", "pagella"])
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--pages", type=int, default=1)
    command.add_argument("--limit", type=int)
    command.add_argument("--delay", type=float, default=1.0)
    command.add_argument("--user-agent")

    command = sub.add_parser("train", help="train or evaluate a paper model")
    command.add_argument("config", type=Path)
    command.add_argument("--evaluate-only", action="store_true")
    command.add_argument("--checkpoint", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "standardize":
        result = dict(standardize_csv(args.input, args.output))
    elif args.command == "validate":
        result = validate_jsonl(args.manifest, require_binary=args.require_binary)
        if not result["valid"]:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
    elif args.command == "make-splits":
        result = make_splits(
            args.manifest,
            args.output,
            train_ratio=args.train_ratio,
            validation_ratio=args.validation_ratio,
            seed=args.seed,
        )
    elif args.command == "evaluate":
        rows = list(read_jsonl(args.predictions))
        result = binary_metrics(
            [int(x[args.label_field]) for x in rows],
            [int(x[args.prediction_field]) for x in rows],
        )
    elif args.command == "download-images":
        result = download_images(
            args.manifest, args.output, limit=args.limit, delay=args.delay
        )
    elif args.command == "collect":
        contact = os.environ.get("DISINFOMM_CONTACT", "https://github.com/SaiSyokan/DisinfoMM")
        result = collect(
            args.source,
            args.output,
            pages=args.pages,
            delay=args.delay,
            limit=args.limit,
            user_agent=args.user_agent or f"DisinfoMM/1.0 (+{contact})",
        )
    elif args.command == "train":
        from .training import run

        result = run(args.config, evaluate_only=args.evaluate_only, checkpoint=args.checkpoint)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
