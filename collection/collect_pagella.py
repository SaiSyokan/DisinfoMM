"""Collect Pagella Politica records into a Dataset.csv-compatible file."""

import sys

from disinfomm.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["collect", "pagella", *sys.argv[1:]]))
