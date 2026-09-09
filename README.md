# DisinfoMM

[![Paper](https://img.shields.io/badge/ICMI%202025-10.1145%2F3716553.3750813-blue)](https://doi.org/10.1145/3716553.3750813)
[![Tests](https://github.com/SaiSyokan/DisinfoMM/actions/workflows/tests.yml/badge.svg)](https://github.com/SaiSyokan/DisinfoMM/actions/workflows/tests.yml)
[![Code license: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![Data annotations: CC BY 4.0](https://img.shields.io/badge/annotations-CC%20BY%204.0-lightgrey.svg)](DATA_LICENSE.md)

Official code for **“A Multilingual, Multimodal Dataset for Disinformation and Out-of-Context Analysis with Rich Supportive Information”**, ICMI 2025, pages 643–651.

DisinfoMM contains 25,752 fact-checking records collected from Snopes, Polígrafo, and Pagella Politica. It covers English, Portuguese, and Italian and preserves the claim, image URL, original verdict, harmonized five-level evaluation, explanation, evidence links, and metadata.

## One dataset file, two code sections

The original `Dataset.csv` is the sole authoritative dataset file and is prepared separately for Hugging Face at [`Syokan/DisinfoMM`](https://huggingface.co/datasets/Syokan/DisinfoMM). Images are not redistributed; the CSV contains their source URLs.

This repository has two intentionally separate workflows:

```text
collection/                 three website collectors + label/evidence harmonization
experiments/                CSV subset preparation + five clearly separated model families
src/disinfomm/              tested reusable implementations used by both workflows
configs/                    paper-aligned run configurations
data/paper_splits/archived  exact recovered paper-era derived JSON files
results/                    final-paper Tables 2–5 in machine-readable form
```

## Installation

Python 3.10 or newer is required.

```bash
git clone https://github.com/SaiSyokan/DisinfoMM.git
cd DisinfoMM
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Optional dependencies:

```bash
python -m pip install -e '.[collect]'  # live website collection
python -m pip install -e '.[train]'    # PyTorch, CLIP, M-CLIP, SigLIP
python -m pip install -e '.[dev]'      # tests and linting
```

## Part 1: collect and harmonize the dataset

The source-specific entry points write the same 14-column structure as `Dataset.csv`:

```bash
python collection/collect_snopes.py --output collected/snopes.csv --pages 1
python collection/collect_poligrafo.py --output collected/poligrafo.csv --pages 1
python collection/collect_pagella.py --output collected/pagella.csv --pages 1
```

Normalize the five-level `Evaluation` column and regenerate the evidence-domain lists described in the paper:

```bash
python collection/harmonize.py collected/combined.csv collected/harmonized.csv \
  --source-lists collected/source_lists
```

The harmonizer preserves `Label` as the source-specific verdict. Unknown values remain `Unknown` for review. See [collection/README.md](collection/README.md) and [docs/LABELS.md](docs/LABELS.md).

## Part 2: prepare and run experiments

The full CSV is not class-balanced. Reproduce the paper’s sampling principle directly from the CSV:

```bash
python experiments/prepare_data.py /path/to/Dataset.csv data/splits/english \
  --regime english --size 7000 --fake-ratio 0.5 --seed 1111

python experiments/prepare_data.py /path/to/Dataset.csv data/splits/multilingual \
  --regime multilingual --size 10000 --fake-ratio 0.5 --seed 1111
```

This creates deterministic 8:1:1 splits in both self-contained JSONL and the historical `data.json`/annotation JSON format. Every run writes `audit.json` with the input CSV hash, exclusions, selected labels, sources, and split sizes.

Download media referenced by the chosen subset:

```bash
disinfomm download-images data/splits/english/jsonl/train.jsonl --output media
```

The downloader resumes existing files and records failures and SHA-256 hashes. Media availability may differ from the paper-era snapshot because the source websites control the URLs.

### Experiment families

| Group | Command | Meaning |
|---|---|---|
| Comparison: ordinary | `python experiments/comparison/basic/run.py` | Recovered CLIP product-fusion baseline |
| Comparison: multi | `python experiments/comparison/multilingual/run.py` | Recovered multilingual text encoder variant |
| Comparison: latest | `python experiments/comparison/latest/run.py` | Recovered later SigLIP experiment; not a final-paper method |
| Proposed: ordinary | `python experiments/proposed/basic/run.py` | Paper Section 4.2, without supportive information |
| Proposed: with evidence | `python experiments/proposed/with_evidence/run.py` | Paper Section 4.3, explanation-guided teacher-student training |

The final paper also reports an external Evidence-based CLIP comparison using online retrieval. It is different from the proposed “with evidence” model; see [docs/EXTERNAL_BASELINES.md](docs/EXTERNAL_BASELINES.md).

Paper settings are encoded in `configs/`: Adam, 30 epochs, batch size 64, six workers, classifier learning rate `5e-5`, backbone learning rate `5e-7`, dropout `0.1`, and weight decay `1.2e-6`. The memory-intensive SigLIP configuration uses the recovered batch size 16 and four workers.

## Implementation coverage

The repository provides the three comparison families, the historical CSV-to-JSON-compatible formatter, and complete implementations of both proposed architectures from Sections 4.2 and 4.3 of the paper. [docs/SOURCE_CODE_AUDIT.md](docs/SOURCE_CODE_AUDIT.md) records the source materials and implementation corrections used to assemble the release.

The exact recovered experiment JSON files are kept under `data/paper_splits/archived/`. They contain 7,052 English and 10,368 multilingual examples—the exact counts behind the paper’s rounded 7k/10k description. For new experiments, generate fresh audited subsets from `Dataset.csv` rather than treating the archived `data.json` as another dataset release.

## Dataset labels

The normalized five-level scheme is:

```text
True → Mostly True → Incomplete → Mostly False → False
```

For the paper’s binary task, `True` and `Mostly True` are authentic (`0`); `Incomplete`, `Mostly False`, and `False` are disinformation (`1`). The two unresolved CSV rows are excluded from binary subsets until reviewed. Source-specific mappings and historical spelling variants are listed in [docs/LABELS.md](docs/LABELS.md).

## Tests

```bash
python -m pytest -q
ruff check .
```

Tests are offline and cover label mapping, CSV preservation, balanced deterministic sampling, source adapters, source-domain lists, metrics, split disjointness, and the proposed teacher loss.

## Citation

```bibtex
@inproceedings{cui2025disinfomm,
  author    = {Shuhan Cui and Hanrui Wang and Ching-Chun Chang and Huy H. Nguyen and Isao Echizen},
  title     = {A Multilingual, Multimodal Dataset for Disinformation and Out-of-Context Analysis with Rich Supportive Information},
  booktitle = {Proceedings of the 27th International Conference on Multimodal Interaction},
  pages     = {643--651},
  year      = {2025},
  doi       = {10.1145/3716553.3750813}
}
```

## Contact and licenses

Shuhan Cui — The University of Tokyo — `syokan [at] g.ecc.u-tokyo.ac.jp`

Code is under the [MIT License](LICENSE). Author-created dataset annotations and harmonized metadata are under [CC BY 4.0](DATA_LICENSE.md). Source articles, images, quotations, trademarks, and linked evidence are not relicensed; see [THIRD_PARTY.md](THIRD_PARTY.md).
