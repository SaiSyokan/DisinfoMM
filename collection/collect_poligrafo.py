"""Collect Polígrafo records into a Dataset.csv-compatible file."""

import sys

from disinfomm.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["collect", "poligrafo", *sys.argv[1:]]))
