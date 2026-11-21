"""Reset demo runtime state (M28). Removes local runtime DBs; code seeds stay.

Clears: data/*.db* (incidents, evidence, runs, approvals, metrics, learned
demo state). Preserves: baselines (knowledge/, policies, script seeds,
workflow logic — all live in code and reseed on next run).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def reset(data_dir: str = "./data") -> list[str]:
    removed = []
    root = Path(data_dir)
    if not root.is_dir():
        return removed
    for path in sorted(root.glob("*.db*")):
        if path.is_file():
            path.unlink()
            removed.append(str(path))
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset demo runtime state")
    parser.add_argument("--data-dir", default="./data")
    args = parser.parse_args()
    removed = reset(args.data_dir)
    print(f"cleared {len(removed)} runtime file(s); baselines preserved in code")
    for path in removed:
        print(f"  removed {path}")


if __name__ == "__main__":
    main()
