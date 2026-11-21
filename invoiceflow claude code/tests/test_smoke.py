"""Smoke tests: the package installs, every planned subpackage imports, and the CLI starts."""

import importlib

import pytest

import invoiceflow
from invoiceflow.cli import main

SUBPACKAGES = [
    "core",
    "policy",
    "ports",
    "adapters",
    "adapters.local",
    "adapters.databricks",
    "data",
    "retrieval",
    "agent",
    "tools",
    "audit",
    "services",
    "services.erp_sandbox",
    "services.approvals",
    "observability",
    "evals",
]


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_imports(name: str) -> None:
    importlib.import_module(f"invoiceflow.{name}")


def test_cli_without_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: invoiceflow" in capsys.readouterr().out


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"invoiceflow {invoiceflow.__version__}"
