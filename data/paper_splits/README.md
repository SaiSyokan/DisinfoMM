# Archived paper split manifests

`archived/` contains the exact derived JSON files recovered from the ICMI experiment directory. They are included for auditability; `Dataset.csv` remains the authoritative dataset.

| Regime | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| English | 5,641 | 706 | 705 | 7,052 |
| Multilingual | 8,294 | 1,037 | 1,037 | 10,368 |

`data.json` is the historical lookup catalog expected by the old dataset loader. The six annotation files store `id`, `image_id`, and `falsified`. Every recovered annotation pairs a record with its own image (`id == image_id`); the binary label represents the verdict rather than a synthetically mismatched image.

The historical catalog contains 19,887 entries and refers to local images that are no longer complete. Do not treat it as a second dataset release. For new runs, use `experiments/prepare_data.py` to derive clean manifests directly from `Dataset.csv`; that process records the input CSV hash and every sampling decision.

The paper rounded the subset sizes to 7,000 English and 10,000 multilingual samples. The exact recovered counts above are preserved rather than altered.

From this directory, run `shasum -a 256 -c checksums.sha256` to verify that the recovered files have not changed.
