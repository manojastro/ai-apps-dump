"""Nodes 12-13: human_approval (LangGraph interrupt) and open_pr (local branch; GitHub draft PR opt-in)."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
from langgraph.types import interrupt

from schemaguard.agent.nodes.fix import artifacts_dir
from schemaguard.agent.state import AgentState, Deps
from schemaguard.observability import get_logger
from schemaguard.sandbox.patching import apply_unified_diff

log = get_logger("approval")
BOT = ["-c", "user.name=SchemaGuard Bot", "-c", "user.email=schemaguard-bot@localhost"]


def make_human_approval(deps: Deps):
    def human_approval(state: AgentState) -> dict[str, Any]:
        # Everything before interrupt() re-runs on resume, so keep it side-effect free.
        request = {
            "run_id": state["run_id"],
            "question": "Approve this patch for a branch / draft PR?",
            "topic": state["schema_diff"]["topic"],
            "strategy": state["fix_plan"].get("strategy"),
            "rationale": state["fix_plan"].get("rationale"),
            "diff": state["patch"]["diff"],
            "tests": f"{state['test_results']['tests_passed']}/{state['test_results']['tests_total']} data tests passed",
            "counts": state["aggregate"]["counts"],
        }
        answer = interrupt(request)
        if not isinstance(answer, dict) or answer.get("decision") not in ("approve", "reject"):
            raise ValueError(f"invalid approval payload: {answer!r}")
        record = {
            "decision": answer["decision"],
            "reviewer": str(answer.get("reviewer") or "unknown")[:100],
            "comment": str(answer.get("comment") or "")[:2000],
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        approved = answer["decision"] == "approve"
        return {
            "approval": record,
            "approval_status": "approved" if approved else "rejected",
            "status": "running" if approved else "rejected",
        }

    return human_approval


def route_after_approval(state: AgentState) -> str:
    return "open_pr" if state.get("approval_status") == "approved" else "write_report"


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *BOT, "-C", str(repo), *args], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout.strip()


def ensure_target_repo(pipeline_dir: Path, repo: Path) -> None:
    """The repo SchemaGuard proposes changes to. Default: a local git copy of the pipeline."""
    if (repo / ".git").exists():
        return
    repo.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        pipeline_dir,
        repo,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("data", "*.duckdb*", "__pycache__"),
    )
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Baseline copy of the demo pipeline")


def make_open_pr(deps: Deps):
    def open_pr(state: AgentState) -> dict[str, Any]:
        run_id = state["run_id"]
        art = artifacts_dir(deps, run_id)
        patch_path = art / "fix.patch"
        patch_path.write_text(state["patch"]["diff"], encoding="utf-8", newline="\n")
        repo = deps.settings.resolved_target_repo
        topic = state["schema_diff"]["topic"]
        branch = f"schemaguard/{run_id[:8]}-{topic.replace('.', '-')}"
        out: dict[str, Any] = {"status": "completed"}
        try:
            ensure_target_repo(deps.pipeline_dir, repo)
            base = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
            _git(repo, "checkout", "-q", "-b", branch)
            try:
                apply_unified_diff(repo, state["patch"]["diff"])
                _git(repo, "add", "-A")
                msg = (
                    f"SchemaGuard: adapt pipeline to {topic} schema change\n\n"
                    f"Strategy: {state['fix_plan'].get('strategy')}\n"
                    f"Approved by: {state['approval']['reviewer']} at {state['approval']['at']}\n"
                    f"Run: {run_id}\n"
                )
                _git(repo, "commit", "-q", "-m", msg)
                sha = _git(repo, "rev-parse", "HEAD")
            finally:
                _git(repo, "checkout", "-q", base)
            result = f"branch {branch} @ {sha[:10]} in {repo}; patch {patch_path}"
            if deps.settings.github_token and deps.settings.github_repo:
                result += "; " + _open_github_draft_pr(deps, repo, branch, base, state)
            out["pr_url_or_patch_path"] = result
        except Exception as exc:  # report, keep the patch file
            log.error("open_pr failed", extra={"error": str(exc)})
            out["pr_url_or_patch_path"] = f"patch {patch_path} (branch not created: {exc})"
            out["errors"] = [f"open_pr: {exc}"]
        return out

    return open_pr


def _open_github_draft_pr(
    deps: Deps, repo: Path, branch: str, base: str, state: AgentState
) -> str:  # pragma: no cover
    """Only reached when GITHUB_TOKEN and GITHUB_REPO are set and a human approved. Not run in this build."""
    s = deps.settings
    _git(
        repo,
        "push",
        f"https://x-access-token:{s.github_token}@github.com/{s.github_repo}.git",
        f"{branch}:{branch}",
    )
    r = httpx.post(
        f"https://api.github.com/repos/{s.github_repo}/pulls",
        headers={"Authorization": f"Bearer {s.github_token}", "Accept": "application/vnd.github+json"},
        json={
            "title": f"SchemaGuard: adapt to {state['schema_diff']['topic']} schema change",
            "head": branch,
            "base": base,
            "draft": True,
            "body": state.get("report") or "Generated by SchemaGuard after human approval.",
        },
        timeout=30,
    )
    r.raise_for_status()
    return str(r.json()["html_url"])
