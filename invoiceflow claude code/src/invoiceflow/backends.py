"""Pick the data, retrieval and LLM implementations from configuration.

This is the only place that knows which backend is in use; everything else depends on
the ports.
"""

from pathlib import Path

from invoiceflow.config import Settings
from invoiceflow.data.dataset import Dataset, read_dataset
from invoiceflow.ports.data import APDataReader

DATA_DIR = Path("data/generated")
DOCS_DIR = Path("data/docs")


def workspace_client(settings: Settings):  # type: ignore[no-untyped-def]
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient(profile=settings.databricks_config_profile)


def data_reader(settings: Settings, dataset: Dataset | None = None) -> APDataReader:
    if settings.invoiceflow_backend == "databricks":
        from invoiceflow.adapters.databricks.reader import Snapshot
        from invoiceflow.adapters.databricks.sql import StatementRunner
        from invoiceflow.adapters.local.memory import MemoryReader

        runner = StatementRunner(
            settings.require("databricks_warehouse_id"), workspace_client(settings)
        )
        # Batch runs read Unity Catalog once (8 statements) and serve from memory: per-record
        # reads take seconds each on a Free Edition 2X-Small warehouse. A long-lived service
        # would use DatabricksReader wrapped in CachingReader instead.
        return MemoryReader(
            Snapshot(runner, settings.invoiceflow_catalog, settings.invoiceflow_schema)
        )
    from invoiceflow.adapters.local.memory import MemoryReader

    return MemoryReader(dataset or read_dataset(DATA_DIR))
