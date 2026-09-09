"""Run the paper's proposed basic architecture without supportive information."""

import sys
from pathlib import Path

from disinfomm.cli import main

CONFIG = Path(__file__).resolve().parents[3] / "configs" / "proposed_basic.yaml"

if __name__ == "__main__":
    raise SystemExit(main(["train", str(CONFIG), *sys.argv[1:]]))
