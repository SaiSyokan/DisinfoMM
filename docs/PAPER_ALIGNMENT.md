# Paper-to-repository alignment

| Paper section | Repository artifact |
|---|---|
| 3.1 dataset attributes | `Dataset.csv` and `docs/DATASET.md` |
| 3.2 three source websites | `collection/` and `src/disinfomm/collection/` |
| 3.3 rating standardization | `collection/harmonize.py`, `src/disinfomm/labels.py` |
| 3.3 source-link extraction | `write_source_link_lists` and its three CSV outputs |
| 4.2 basic approach | `proposed_basic` model and config |
| 4.3 enhanced approach | `proposed_with_evidence` model, objective, and config |
| 5.1 settings and metrics | configs, `src/disinfomm/metrics.py` |
| 5.2–5.5 results | `results/` CSV files |

The three comparison families are clean reimplementations of recovered research scripts. The two proposed models are reconstructed from the paper because complete local implementations were not found. Where archived defaults conflict with the final paper, the public configs follow the paper. See `SOURCE_CODE_AUDIT.md` and `REPRODUCIBILITY.md`.
