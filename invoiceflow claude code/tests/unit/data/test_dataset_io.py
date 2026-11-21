import json
from pathlib import Path

import pytest

from invoiceflow.data.dataset import Dataset, DatasetIntegrityError, read_dataset, write_dataset


def test_write_then_read_round_trips(dataset: Dataset, tmp_path: Path) -> None:
    manifest = write_dataset(dataset, tmp_path)
    assert manifest["dataset_version"] == dataset.version
    assert manifest["files"]["invoices"]["rows"] == len(dataset.invoices)
    assert read_dataset(tmp_path) == dataset


def test_written_files_are_byte_identical_across_writes(dataset: Dataset, tmp_path: Path) -> None:
    write_dataset(dataset, tmp_path / "a")
    write_dataset(dataset, tmp_path / "b")
    for name in ("invoices.jsonl", "manifest.json"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


def test_tampered_file_is_refused(dataset: Dataset, tmp_path: Path) -> None:
    write_dataset(dataset, tmp_path)
    path = tmp_path / "invoices.jsonl"
    path.write_bytes(path.read_bytes().replace(b'"CLEAN"', b'"DIRTY"', 1) + b" ")
    with pytest.raises(DatasetIntegrityError, match=r"invoices\.jsonl"):
        read_dataset(tmp_path)


def test_missing_manifest_says_how_to_fix(tmp_path: Path) -> None:
    with pytest.raises(DatasetIntegrityError, match="data generate"):
        read_dataset(tmp_path)


def test_manifest_records_provenance(dataset: Dataset, tmp_path: Path) -> None:
    write_dataset(dataset, tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == dataset.seed
    assert manifest["faker_version"]
    assert manifest["generator_version"]
