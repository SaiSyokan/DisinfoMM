# DisinfoMM

[![Paper](https://img.shields.io/badge/ICMI%202025-10.1145%2F3716553.3750813-blue)](https://doi.org/10.1145/3716553.3750813)
[![Tests](https://github.com/SaiSyokan/DisinfoMM/actions/workflows/tests.yml/badge.svg)](https://github.com/SaiSyokan/DisinfoMM/actions/workflows/tests.yml)
[![Code license: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![Data annotations: CC BY 4.0](https://img.shields.io/badge/annotations-CC%20BY%204.0-lightgrey.svg)](DATA_LICENSE.md)

Official code and release tooling for **“A Multilingual, Multimodal Dataset for Disinformation and Out-of-Context Analysis with Rich Supportive Information”**, ICMI 2025, pages 643–651.

DisinfoMM contains fact-checked image–claim pairs in English, Italian, and Portuguese. Each record preserves a source verdict, a harmonized five-level veracity label, an explanation, evidence links, and provenance metadata. The repository also implements the paper’s image–text baseline, multilingual model, and supportive-information teacher–student objective.

> The dataset is distributed separately from this code repository. Images are not committed to GitHub. See [Dataset access](#dataset-access) and [data rights](docs/DATASET.md#rights-and-responsible-use).

## At a glance

| Property | Value |
|---|---|
| Sources | Snopes, Pagella Politica, Polígrafo |
| Languages | English, Italian, Portuguese |
| Snapshot size | 25,752 collected records (approximately 25k in the paper) |
| Labels | True, Mostly True, Incomplete, Mostly False, False |
| Paper tasks | Binary multimodal disinformation/OOC detection |
| Supportive information | Explanations, verdicts, timestamps, keywords, article and evidence links |

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

Install optional components only when needed:

```bash
python -m pip install -e '.[train]'    # PyTorch, CLIP, multilingual training
python -m pip install -e '.[collect]'  # live collection adapters
python -m pip install -e '.[dev]'      # tests and linting
```

## Dataset access

The release package is hosted at [Hugging Face: `Syokan/DisinfoMM`](https://huggingface.co/datasets/Syokan/DisinfoMM). After downloading it, validate the metadata before downloading media:

```bash
disinfomm validate /path/to/disinfomm-v1.0.0.jsonl
disinfomm download-images /path/to/disinfomm-v1.0.0.jsonl \
  --output /path/to/DisinfoMM/images
```

The downloader is resumable and records failures. Source websites retain rights in their articles and media; review [DATA_LICENSE.md](DATA_LICENSE.md) before redistribution.

## Reproduce the paper experiments

The dataset release contains exact paper manifests under `paper_splits/`. Copy or link that directory to `data/paper_splits/`; the manifests are authoritative for sample membership and stored binary labels. Point each manifest at the downloaded media root, then run:

```bash
disinfomm train configs/basic_clip.yaml
disinfomm train configs/multilingual_clip.yaml
disinfomm train configs/supportive_clip.yaml
```

Evaluate a saved checkpoint:

```bash
disinfomm train configs/basic_clip.yaml --evaluate-only --checkpoint runs/basic_clip/best.pt
```

Paper hyperparameters are the defaults in the configs: 30 epochs, batch size 64, six workers, Adam, classifier learning rate `5e-5`, CLIP learning rate `5e-7`, dropout `0.1`, and weight decay `1.2e-6`. Full instructions and known differences between the archived research scripts and this release are in [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Update or extend the dataset

The collector runs incrementally and never overwrites existing records:

```bash
disinfomm collect snopes --output collected/snopes.jsonl --pages 1
disinfomm collect poligrafo --output collected/poligrafo.jsonl --pages 1
disinfomm collect pagella --output collected/pagella.jsonl --pages 1
```

Websites change. Every collection run stores its timestamp and source URL; unknown labels remain `Unknown` for manual review rather than being silently guessed. Use a descriptive user agent, obey each site’s terms and robots policy, and rate-limit requests. See [docs/COLLECTION.md](docs/COLLECTION.md).

## Repository map

```text
configs/                 paper-aligned training configurations
data/examples/           synthetic, redistributable smoke-test records
data/paper_splits/       location for dataset-release experiment manifests
docs/                    dataset, collection, labels, and reproduction guides
results/                 tables reported in the paper
src/disinfomm/           reusable collection, data, model, and evaluation code
tests/                   offline unit tests
```

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

## Contact

Shuhan Cui — The University of Tokyo — `syokan [at] g.ecc.u-tokyo.ac.jp`

## Licenses

Code is released under the [MIT License](LICENSE). Dataset annotations and original metadata contributed by the DisinfoMM authors are released under [CC BY 4.0](DATA_LICENSE.md). Third-party text, images, trademarks, and linked resources are not relicensed; see [THIRD_PARTY.md](THIRD_PARTY.md).
