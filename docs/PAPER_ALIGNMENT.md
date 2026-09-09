# Paper-to-repository alignment

| Paper section | Repository artifact |
|---|---|
| 3.1 dataset attributes | `docs/DATASET.md`, canonical JSONL schema |
| 3.2 three source websites | `src/disinfomm/collection/` |
| 3.3 rating standardization | `src/disinfomm/labels.py`, `docs/LABELS.md` |
| 3.3 source-link extraction | canonical `evidence_urls` and `evidence_domains` |
| 4.2 basic approach | `basic_clip` model and config |
| 4.3 enhanced approach | `supportive_clip` model, objective, and config |
| 5.1 settings and metrics | configs, `src/disinfomm/metrics.py` |
| 5.2–5.5 results | `results/` CSV files |

The code is a release-quality reimplementation based on the paper and recovered research scripts. Where the archived scripts conflict with the final paper, the public configs follow the paper and the discrepancy is documented in `REPRODUCIBILITY.md`.
