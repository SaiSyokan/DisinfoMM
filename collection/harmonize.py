"""Normalize labels and regenerate evidence-domain frequency lists."""

import sys

from disinfomm.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["harmonize", *sys.argv[1:]]))
