"""A generated dataset and its on-disk form: one JSON Lines file per table plus a manifest.

The manifest records the seed, generator and Faker versions, and the SHA-256 of every
file. `dataset_version` is a hash over those file hashes, so any change to any row gives
a new version. `read_dataset` refuses files whose hash does not match the manifest.
"""

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from invoiceflow.data.models import (
    ContractTerms,
    Frozen,
    GoodsReceipt,
    GroundTruth,
    Invoice,
    PurchaseOrder,
    Split,
    Vendor,
)

TABLES: dict[str, type[BaseModel]] = {
    "vendors": Vendor,
    "purchase_orders": PurchaseOrder,
    "goods_receipts": GoodsReceipt,
    "invoices": Invoice,
    "ground_truth": GroundTruth,
    "contracts": ContractTerms,
}


class DatasetIntegrityError(RuntimeError):
    pass


class Dataset(Frozen):
    seed: int
    generator_version: str
    faker_version: str
    vendors: tuple[Vendor, ...]
    purchase_orders: tuple[PurchaseOrder, ...]
    goods_receipts: tuple[GoodsReceipt, ...]
    invoices: tuple[Invoice, ...]
    ground_truth: tuple[GroundTruth, ...]
    contracts: tuple[ContractTerms, ...]

    def labels(self, split: Split) -> tuple[GroundTruth, ...]:
        return tuple(label for label in self.ground_truth if label.split is split)

    @property
    def version(self) -> str:
        return _dataset_version({name: _sha256(_jsonl(getattr(self, name))) for name in TABLES})


def _jsonl(rows: Sequence[BaseModel]) -> bytes:
    return "".join(row.model_dump_json() + "\n" for row in rows).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dataset_version(file_hashes: dict[str, str]) -> str:
    joined = "\n".join(f"{name}:{file_hashes[name]}" for name in sorted(file_hashes))
    return _sha256(joined.encode("utf-8"))


def write_dataset(dataset: Dataset, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    for name in TABLES:
        rows: tuple[BaseModel, ...] = getattr(dataset, name)
        data = _jsonl(rows)
        (out_dir / f"{name}.jsonl").write_bytes(data)
        files[name] = {"rows": len(rows), "sha256": _sha256(data)}
    manifest = {
        "seed": dataset.seed,
        "generator_version": dataset.generator_version,
        "faker_version": dataset.faker_version,
        "dataset_version": _dataset_version({n: f["sha256"] for n, f in files.items()}),
        "files": files,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def read_dataset(data_dir: Path) -> Dataset:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise DatasetIntegrityError(
            f"no manifest in {data_dir}; run `invoiceflow data generate` first"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tables: dict[str, tuple[BaseModel, ...]] = {}
    for name, model in TABLES.items():
        data = (data_dir / f"{name}.jsonl").read_bytes()
        expected = manifest["files"][name]["sha256"]
        if _sha256(data) != expected:
            raise DatasetIntegrityError(
                f"{name}.jsonl does not match the manifest hash; regenerate the dataset"
            )
        tables[name] = tuple(model.model_validate_json(line) for line in data.splitlines())
    return Dataset.model_validate(
        {
            "seed": manifest["seed"],
            "generator_version": manifest["generator_version"],
            "faker_version": manifest["faker_version"],
            **tables,
        }
    )
