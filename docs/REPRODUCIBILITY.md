# Reproducing the ICMI 2025 experiments

## What is reproduced

This repository implements the paper’s three in-repository architectures:

- basic CLIP: ViT-B/32 image/text encoders, LayerNorm, learned scalar fusion, and an MLP;
- multilingual CLIP: CLIP image features with `M-CLIP/XLM-Roberta-Large-Vit-L-14` text features projected into the shared space;
- supportive-information model: a teacher–student objective using the explanation during training and image–claim inputs at inference.

The external evidence-based comparison and the DT-Transformer-derived comparison require their upstream repositories and separately licensed datasets. They are documented as baselines rather than vendored.

## Exact data membership

Use `paper_splits/english/` and `paper_splits/multilingual/` from the dataset release, copied or linked into `data/paper_splits/`. These files are rebuilt from the archived annotation files and preserve each stored `falsified` label. The English split has 5,641/706/705 train/validation/test entries; the multilingual split has 8,294/1,037/1,037.

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
