# Experiments

This directory is the second half of the repository. It deliberately separates three recovered comparison families from the two architectures proposed in the paper.

## Prepare data from Dataset.csv

The CSV is the source of truth. Generate a balanced 7,000-record English subset and a balanced 10,000-record multilingual subset:

```bash
python experiments/prepare_data.py /path/to/Dataset.csv data/splits/english \
  --regime english --size 7000 --fake-ratio 0.5 --seed 1111

python experiments/prepare_data.py /path/to/Dataset.csv data/splits/multilingual \
  --regime multilingual --size 10000 --fake-ratio 0.5 --seed 1111
```

Each run writes:

- `jsonl/`: self-contained manifests used by the cleaned training code;
- `legacy/`: the historical `data.json` plus `train.json`, `val.json`, and `test.json` shape;
- `audit.json`: input hash, exclusions, label counts, source counts, seed, and split sizes.

The selection is deterministic. It excludes missing claims, missing explanations, invalid image URLs, and unresolved labels so the same split can be used by every model family. It does not require images to have already been downloaded.

Download the selected images:

```bash
disinfomm download-images data/splits/english/jsonl/train.jsonl --output media
disinfomm download-images data/splits/english/jsonl/validation.jsonl --output media
disinfomm download-images data/splits/english/jsonl/test.jsonl --output media
```

## Model families

| Group | Directory | Implementation |
|---|---|---|
| Recovered comparison | `comparison/basic/` | ViT-B/32 CLIP, normalized image/text product, linear classifier |
| Recovered comparison | `comparison/multilingual/` | CLIP image encoder plus multilingual XLM-R text encoder and projection |
| Recovered exploratory | `comparison/latest/` | SigLIP (`ViT-SO400M-14-SigLIP`); found in `latest_*` files, not a final-paper method |
| Proposed | `proposed/basic/` | Paper Section 4.2: LayerNorm, learnable scalar fusion, MLP |
| Proposed | `proposed/with_evidence/` | Paper Section 4.3: explanation-guided teacher-student objective |

Run any family through its local `run.py`, for example:

```bash
python experiments/comparison/basic/run.py
python experiments/comparison/multilingual/run.py
python experiments/comparison/latest/run.py
python experiments/proposed/basic/run.py
python experiments/proposed/with_evidence/run.py
```

Pass `--evaluate-only --checkpoint PATH` to evaluate a saved checkpoint. The paper-aligned defaults are in `configs/`.

The third representative final-paper method, Open-Domain Evidence-based CLIP/CCN [Abdelnabi et al., CVPR 2022], is an external method with its own online retrieval pipeline. It is not the same as the paper’s proposed “with evidence” training. To avoid silently republishing upstream code and Google-derived evidence, this repository documents the required upstream project in `docs/EXTERNAL_BASELINES.md` instead of vendoring it.
