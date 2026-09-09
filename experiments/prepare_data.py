"""Build deterministic experiment inputs directly from Dataset.csv."""

import sys

from disinfomm.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["prepare-experiments", *sys.argv[1:]]))
