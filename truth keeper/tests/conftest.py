"""Shared fixtures. Every test runs offline: outbound sockets are blocked and LLM_MODE is forced to mock."""

from __future__ import annotations

import shutil
import socket

import pytest

from app.applier.sandbox import reset_sandbox
from app.approval.store import Store
from app.config import get_settings
from data.generator.generate import generate


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("MOCK_PROFILE", "clean")
    monkeypatch.setenv("PHOENIX_COLLECTOR_ENDPOINT", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    real_connect = socket.socket.connect

    def guarded(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host in ("127.0.0.1", "::1", "localhost"):
            return real_connect(self, address)
        raise RuntimeError(f"network access blocked in tests (tried {address!r})")

    monkeypatch.setattr(socket.socket, "connect", guarded)


@pytest.fixture(scope="session")
def dataset(tmp_path_factory):
    """Default-profile dataset (seed 42, n=500) generated once per test session."""
    root = tmp_path_factory.mktemp("generated")
    gt = generate(seed=42, n=500, out_dir=root, gt_path=root / "ground_truth.json")
    return root, root / "ground_truth.json", gt


@pytest.fixture(scope="session")
def hard_dataset(tmp_path_factory):
    root = tmp_path_factory.mktemp("generated_hard")
    gt = generate(seed=7, n=500, out_dir=root, gt_path=root / "ground_truth.json", profile="hard")
    return root, root / "ground_truth.json", gt


@pytest.fixture
def env(tmp_path, dataset, monkeypatch):
    """A fresh sandbox + state db + regressions dir for one test, wired through settings."""
    gen_dir, gt_path, _ = dataset
    gen_copy = tmp_path / "generated"
    shutil.copytree(gen_dir, gen_copy)
    sandbox = tmp_path / "sandbox"
    monkeypatch.setenv("TK_GENERATED_DIR", str(gen_copy))
    monkeypatch.setenv("TK_SANDBOX_DIR", str(sandbox))
    monkeypatch.setenv("TK_STATE_DB", str(tmp_path / "state.db"))
    monkeypatch.setenv("TK_GROUND_TRUTH", str(gt_path))
    monkeypatch.setenv("TK_REGRESSIONS_DIR", str(tmp_path / "regressions"))
    reset_sandbox(gen_copy, sandbox)
    settings = get_settings()
    store = Store(settings.state_db, regressions_dir=settings.regressions_dir)
    yield settings, store
    store.close()
