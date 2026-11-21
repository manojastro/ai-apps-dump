"""Print category balance of golden_set.jsonl (counts + smoke subset size)."""

import json
import sys
from collections import Counter
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "golden_set.jsonl"


def main(path: str = str(PATH)) -> None:
    cats: Counter[str] = Counter()
    smoke = 0
    total = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cats[row["category"]] += 1
        smoke += bool(row.get("smoke"))
        total += 1
    print(f"total={total} smoke={smoke}")
    for cat, count in sorted(cats.items()):
        print(f"{cat}: {count}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(PATH))
