# Dataset collection and harmonization

This directory is the first half of the repository: rebuilding or extending the CSV dataset.

The three source entry points are separate so that website changes can be diagnosed independently:

```bash
python collection/collect_snopes.py --output collected/snopes.csv --pages 1
python collection/collect_poligrafo.py --output collected/poligrafo.csv --pages 1
python collection/collect_pagella.py --output collected/pagella.csv --pages 1
```

Each command appends records using the same 14 columns as `Dataset.csv`. It skips article URLs already present in its output file. Collection output should first be treated as a new, dated snapshot—not appended blindly to the paper release.

Normalize source labels and rebuild the three evidence-link lists described in the paper:

```bash
python collection/harmonize.py collected/combined.csv collected/harmonized.csv \
  --source-lists collected/source_lists
```

The default thresholds reproduce the historical logic: a domain must appear more than 100 times to enter `frequent_domains.csv` and more than 300 times to enter `important_domains.csv`. `all_links.csv` retains every extracted evidence URL.

Website markup and APIs change. Unknown verdicts stay `Unknown` for manual review; the code does not guess a label silently. Use a descriptive contact in `DISINFOMM_CONTACT`, obey each source’s terms and robots policy, and keep the default delay or a slower one.

The reusable implementations live in `src/disinfomm/collection/`, `src/disinfomm/labels.py`, and `src/disinfomm/io.py`. These small files are only convenient executable entry points.
