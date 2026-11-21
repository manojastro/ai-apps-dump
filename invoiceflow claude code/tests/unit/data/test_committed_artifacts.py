"""The committed contracts and samples must equal a fresh default-seed generation.

If this fails, run `uv run invoiceflow data generate` and commit the result (and explain
in the commit why the generated data changed)."""

from pathlib import Path

from invoiceflow.data.dataset import TABLES, Dataset
from invoiceflow.data.export import SAMPLE_ROWS
from invoiceflow.data.generator.contracts import render_contracts

ROOT = Path(__file__).resolve().parents[3]


def test_committed_contracts_match_generation(dataset: Dataset) -> None:
    rendered = render_contracts(dataset)
    on_disk = {
        p.name: p.read_text(encoding="utf-8") for p in (ROOT / "data/docs/contracts").glob("*.md")
    }
    assert on_disk == rendered


def test_committed_samples_match_generation(dataset: Dataset) -> None:
    for table in TABLES:
        expected = "".join(
            row.model_dump_json() + "\n" for row in getattr(dataset, table)[:SAMPLE_ROWS]
        )
        assert (ROOT / "data/samples" / f"{table}.jsonl").read_text(encoding="utf-8") == expected


def test_contracts_are_marked_synthetic(dataset: Dataset) -> None:
    for text in render_contracts(dataset).values():
        assert "SYNTHETIC DOCUMENT" in text
