"""Write a generated dataset to disk: full data, rendered contracts and a small sample.

Full data goes to `data/generated/` (git-ignored). Contracts and samples are committed, and a
test regenerates them with the default seed to catch drift.
"""

from pathlib import Path
from typing import Any

from invoiceflow.data.dataset import TABLES, Dataset, write_dataset
from invoiceflow.data.generator.contracts import render_contracts

SAMPLE_ROWS = 5


def export_dataset(
    dataset: Dataset, data_dir: Path, contracts_dir: Path, samples_dir: Path
) -> dict[str, Any]:
    manifest = write_dataset(dataset, data_dir)

    contracts_dir.mkdir(parents=True, exist_ok=True)
    for name, text in render_contracts(dataset).items():
        (contracts_dir / name).write_text(text, encoding="utf-8", newline="\n")

    samples_dir.mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        rows = getattr(dataset, table)[:SAMPLE_ROWS]
        (samples_dir / f"{table}.jsonl").write_text(
            "".join(row.model_dump_json() + "\n" for row in rows), encoding="utf-8", newline="\n"
        )
    return manifest
