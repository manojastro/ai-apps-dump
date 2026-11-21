import pytest

from invoiceflow.data.dataset import Dataset
from invoiceflow.data.generator import DEFAULT_SEED, generate


@pytest.fixture(scope="session")
def dataset() -> Dataset:
    """The default-seed dataset, generated once per test session."""
    return generate(DEFAULT_SEED)
