# Implementation source notes

The release consolidates the supplied research code, experiment materials, and final-paper specifications into one installable and tested repository.

## Dataset collection: recovered

The supplied `files_save/Data_collection/` directory contains:

- `dataset.py`: one Scrapy spider orchestrating all three websites;
- `fonctions_snopes.py`: Snopes claim, verdict, explanation, image, keyword, and evidence extraction;
- `fonctions_poligrafo.py`: Polígrafo extraction and verdict mapping;
- `fonctions_pagella.py`: Pagella API parsing, translated keyword rules, sentiment fallback, explanation parsing, and evidence extraction;
- `fonctions.py`: evidence-domain counting and filtering;
- `fonctions_website_template.py`: an unfinished template for future sources.

These files establish the historical behavior, but they also contain fixed paths, broad exception handlers, obsolete selectors, eager model downloads, and cross-module imports that prevent a clean standalone installation. The public implementation retains the behavior in source-specific adapters under `src/disinfomm/collection/` and exposes three independent entry points under `collection/`.

The historical evidence filtering uses strict frequency thresholds: more than 100 citations for the frequent/approved list and more than 300 for the important list. The cleaned `harmonize` command reproduces those thresholds and writes all three lists explicitly.

## Dataset formatting: recovered

The supplied `files_save/Format/createJSON.py` confirms that experiment JSON was derived from a CSV, that `True` and `Mostly true` were mapped to authentic, and that all other recognized levels were mapped to disinformation. It also filtered by caption length and locally available image files and provided several experimental scenarios.

The old script is not deterministic, references a fixed 20,000-entry limit, can reference an uninitialized file-size variable when an image is missing, and has case-sensitive label handling. The cleaned `prepare-experiments` command replaces it with deterministic selection, explicit balance controls, an audit file, and both modern and legacy JSON output.

## Comparison experiments: recovered

The supplied experiment directory contains three recognizable families:

| Family | Recovered files | Recovered behavior |
|---|---|---|
| Basic | `clip_classifier.py`, `dataset_mismatch.py`, `main_ft_clip.py`, `evaluate_clip.py` | OpenAI CLIP ViT-B/32, L2-normalized image/text embeddings, element-wise product, dropout, linear classifier |
| Multilingual | `clip_multiclassifier.py`, `dataset_mismatch_multi.py`, `main_ft_multiclip.py`, `evaluate_multiclip.py` | CLIP image encoder plus M-CLIP/XLM-R text embeddings projected into the image space |
| Latest | `latest_clip_classifier.py`, `latest_dataset_mismatch.py`, `latest_main_ft_clip.py`, `latest_evaluate_clip.py` | OpenCLIP SigLIP `ViT-SO400M-14-SigLIP`; an exploratory later variant |

The release reimplements these families behind one tested trainer rather than publishing the path-dependent copies. Important corrections include using all evaluation batches, separating classifier and backbone learning rates correctly, removing CUDA-only assumptions, and recording deterministic configuration.

The `latest_*` family is not the Evidence-based CLIP method cited in the final paper. It is retained because it was explicitly present in the experiment archive and is useful as a modern exploratory comparison.

## Proposed paper models

The repository includes complete implementations of the two proposed architectures:

- `proposed_basic`: CLIP ViT-B/32 image and claim encoders, LayerNorm, learnable scalar fusion, and an MLP;
- `proposed_with_evidence`: the same student representation plus a three-way image/claim/explanation training representation and cosine teacher loss. Explanation is optional at inference.

## External evidence-based comparison

The local research archive contains the upstream CVPR 2022 `OoC-multi-modal-fc` project associated with the paper’s Evidence-based CLIP comparison. That method performs web retrieval and has separate evidence data, Google API requirements, and upstream preparation steps. It is documented in `EXTERNAL_BASELINES.md` and is not confused with the proposed explanation-guided model.
