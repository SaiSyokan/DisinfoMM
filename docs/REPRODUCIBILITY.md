# Reproducing the ICMI 2025 experiments

## What is reproduced

This repository implements five clearly named local architectures:

- comparison basic: recovered ViT-B/32 product-fusion classifier;
- comparison multilingual: recovered CLIP image and M-CLIP/XLM-R text classifier;
- comparison latest: recovered SigLIP exploratory variant;
- proposed basic: paper Section 4.2 LayerNorm, scalar fusion, and MLP;
- proposed with evidence: paper Section 4.3 explanation-guided teacher-student model.

The paper’s external online-retrieval Evidence-based CLIP comparison requires its upstream repository and separately gathered evidence. It is documented in `EXTERNAL_BASELINES.md` rather than vendored.

## Exact data membership

The authoritative release is `Dataset.csv`. Generate a current, deterministic balanced subset with `experiments/prepare_data.py`; this writes the self-contained manifests expected by the five configs and an audit file containing the CSV hash and sampling choices.

For historical auditing, `data/paper_splits/archived/` preserves the exact old `data.json` and annotation JSON. The English split has 5,641/706/705 train/validation/test entries; the multilingual split has 8,294/1,037/1,037. These files reference missing local images and should not be mistaken for an independent dataset.

The historical files named `test_original` and `val_original` were identical full-dataset intermediates, as were the `*_english` and `*_other` pairs. They are intentionally excluded from the public experiment interface because they are not independent splits.

## Paper settings

The paper specifies Adam training for 30 epochs, batch size 64, six workers, dropout 0.1, weight decay `1.2e-6`, classifier learning rate `5e-5`, and CLIP backbone learning rate `5e-7`. Those values are in `configs/`.

Archived exploratory scripts defaulted to 300 epochs and sometimes used dropout 0.05, different worker counts, or SigLIP. Those defaults are not silently presented as the paper protocol. The `latest_*` files were a later SigLIP experiment and are not part of the ICMI tables.

## Supportive-information objective

For normalized image, claim, and explanation embeddings `v`, `t`, and `s`, the student is `z_student = alpha*v + (1-alpha)*t`. A softmax-constrained three-way mixture forms the training representation from `v`, `t`, and `s`. Training minimizes binary cross entropy plus `lambda * (1 - cosine(z_student, s))`. At default inference, the explanation is omitted and the student representation is used.

## Metrics

The CLI reports overall accuracy and independent authentic/disinformation class accuracies, matching the tables. The archived evaluator accidentally retained labels from only the last batch when computing F1; F1 is not a paper metric and that behavior is not reproduced.

## Expected results

`results/` transcribes Tables 2–5. Exact numbers require the original images, upstream comparison datasets, model checkpoints, dependency versions, and hardware. Randomness and currently downloadable media may cause variation; record the final config, snapshot hash, checkpoint hash, and runtime versions for every new run.
