"""CSV connector for the synthetic dataset."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.connectors.base import Connector


class SyntheticCsvConnector(Connector):
    name = "synthetic_csv"

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def fetch(self, table: str) -> pd.DataFrame:
        path = self.data_dir / f"{table}.csv"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found. Run scripts.generate_synthetic_data first.")
        # Only empty cells are null. Otherwise pandas reads the region code "NA" as missing.
        return pd.read_csv(path, keep_default_na=False, na_values=[""])
