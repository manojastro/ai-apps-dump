"""Sandbox management. Fixes are only ever written to data/sandbox/ copies, never to the originals."""

from __future__ import annotations

import shutil
from pathlib import Path

DB_FILES = ("crm.db", "billing.db", "marketing.db")


class SandboxViolation(PermissionError):
    pass


def reset_sandbox(generated_dir: Path, sandbox_dir: Path) -> list[Path]:
    """Copy the generated originals into the sandbox (overwrites previous sandbox state)."""
    generated_dir, sandbox_dir = Path(generated_dir).resolve(), Path(sandbox_dir).resolve()
    if generated_dir == sandbox_dir:
        raise SandboxViolation("sandbox dir must differ from the generated originals dir")
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for name in DB_FILES:
        src = generated_dir / name
        if not src.exists():
            raise FileNotFoundError(f"{src} missing - run: python -m data.generator.generate")
        dst = sandbox_dir / name
        shutil.copyfile(src, dst)
        out.append(dst)
    return out


def sandbox_ready(sandbox_dir: Path) -> bool:
    return all((Path(sandbox_dir) / n).exists() for n in DB_FILES)


def assert_writable(db_path: Path, sandbox_dir: Path, generated_dir: Path) -> Path:
    """Refuse any write outside the sandbox, and any write into the generated originals."""
    p, sb, gen = Path(db_path).resolve(), Path(sandbox_dir).resolve(), Path(generated_dir).resolve()
    if not p.is_relative_to(sb):
        raise SandboxViolation(f"refusing to write {p}: not inside sandbox {sb}")
    if p.is_relative_to(gen) and gen != sb:
        raise SandboxViolation(f"refusing to write generated original {p}")
    return p
