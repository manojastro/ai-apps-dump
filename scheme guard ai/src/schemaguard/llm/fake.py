"""Deterministic fake LLM for tests, CI and offline demos.

It is a scripted engineer, not a model: it reads the structured `context` and applies fixed
heuristics (a strategy ladder per change kind, plus line-level SQL/YAML edits). Eval numbers produced
with it measure SchemaGuard's pipeline (lineage, verdicts, sandbox, loop control), not LLM quality.
It ignores any instructions inside schema docs or SQL comments by construction.
"""

from __future__ import annotations

import json
import re
from typing import Any

from schemaguard.llm.base import LLMResponse, approx_tokens

# Strategy ladders: attempt N uses entry N (last entry repeats).
LADDERS: dict[str, list[str]] = {
    "renamed": ["update_sql_transform", "pin_schema_version"],
    "removed": ["add_coalesce_default", "pin_schema_version"],
    "type_changed": ["update_sql_transform", "pin_schema_version"],
    "nullability_changed": ["add_coalesce_default", "pin_schema_version"],
    "enum_symbols_added": ["update_data_test", "pin_schema_version"],
    "enum_symbols_removed": ["pin_schema_version"],
}
STRATEGY_RANK = ["update_sql_transform", "add_coalesce_default", "update_data_test", "pin_schema_version"]
DEFAULTS = {
    "VARCHAR": "'unknown'",
    "INTEGER": "0",
    "BIGINT": "0",
    "DOUBLE": "0",
    "FLOAT": "0",
    "BOOLEAN": "false",
}


class FakeLLM:
    name = "fake"
    model = "fake"

    def complete(
        self, task: str, system: str, user: str, context: dict[str, Any], json_mode: bool = True
    ) -> LLMResponse:
        handler = {
            "explain_change": self._explain,
            "plan_fix": self._plan,
            "generate_patch": self._patch,
            "write_summary": self._summary,
        }[task]
        out = handler(context)
        text = json.dumps(out) if json_mode else str(out)
        return LLMResponse(text, approx_tokens(system + user), approx_tokens(text), 0.0, "fake")

    # ------------------------------------------------------------------
    def _explain(self, ctx: dict[str, Any]) -> dict[str, Any]:
        parts = []
        for c in ctx.get("changes", []):
            k = c["kind"]
            if k == "renamed":
                parts.append(f"'{c['field']}' was renamed to '{c['new_field']}'")
            elif k == "removed":
                parts.append(f"'{c['field']}' was removed")
            elif k == "added":
                parts.append(f"'{c['field']}' was added")
            elif k == "type_changed":
                parts.append(f"'{c['field']}' changed type {c['old_type']} -> {c['new_type']}")
            elif k == "enum_symbols_added":
                parts.append(f"'{c['field']}' gained enum values {c['details']['symbols']}")
            elif k == "enum_symbols_removed":
                parts.append(f"'{c['field']}' lost enum values {c['details']['symbols']}")
            elif k == "nullability_changed":
                parts.append(
                    f"'{c['field']}' is now {'nullable' if c['details'].get('now_nullable') else 'required'}"
                )
            else:
                parts.append(f"'{c['field']}' {k.replace('_', ' ')}")
        topic = ctx.get("topic", "the topic")
        text = f"On {topic}, " + "; ".join(parts) + "." if parts else f"No field changes on {topic}."
        return {"explanation": text, "rename_suggestions": []}

    def _plan(self, ctx: dict[str, Any]) -> dict[str, Any]:
        changes = [c for c in ctx.get("changes", []) if c["kind"] in LADDERS]
        attempt = len(ctx.get("previous_attempts", []))
        edits = []
        strategies = []
        for c in changes:
            ladder = LADDERS[c["kind"]]
            strategy = ladder[min(attempt, len(ladder) - 1)]
            strategies.append(strategy)
            edits.append(
                {"change": c, "strategy": strategy, "files": ctx.get("edit_targets", {}).get(c["field"], [])}
            )
        if not edits:
            return {"strategy": "pin_schema_version", "rationale": "No automatic fix applies.", "edits": []}
        main = max(strategies, key=STRATEGY_RANK.index)
        rationale = {
            "update_sql_transform": "Update the staging SQL that reads the changed field so downstream columns keep their name and type.",
            "add_coalesce_default": "Replace the missing/nullable value with a typed default so downstream builds and tests keep working.",
            "update_data_test": "The new values are legitimate; extend the accepted-values test. Note: filters such as "
            "status <> 'CANCELLED' will now include the new values; the owning team should confirm that is intended.",
            "pin_schema_version": "No safe code fix: the change removes information downstream assets need. "
            "Recommend pinning consumers to the previous schema version and asking the producer team to restore it.",
        }[main]
        if attempt:
            rationale += f" (attempt {attempt + 1}; previous attempt failed: {ctx['previous_attempts'][-1].get('failures', [])[:2]})"
        return {"strategy": main, "rationale": rationale, "edits": edits}

    def _patch(self, ctx: dict[str, Any]) -> dict[str, Any]:
        files: dict[str, str] = dict(ctx.get("files", {}))
        types: dict[str, str] = ctx.get("old_types", {})
        changed: dict[str, str] = {}
        for e in ctx.get("plan", {}).get("edits", []):
            c, strategy = e["change"], e["strategy"]
            col = c["field"]
            for path in e.get("files", []):
                if path not in files or not path.endswith(".sql"):
                    continue
                src = changed.get(path, files[path])
                if c["kind"] == "renamed" and strategy == "update_sql_transform":
                    new = rewrite_refs(
                        src, col, lambda _m, nf=c["new_field"]: nf, bare=f"{c['new_field']} as {col}"
                    )
                elif c["kind"] == "type_changed" and strategy == "update_sql_transform":
                    t = types.get(col, "VARCHAR")
                    new = rewrite_refs(
                        src,
                        col,
                        lambda _m, t=t, col=col: f"cast({col} as {t})",
                        bare=f"cast({col} as {t}) as {col}",
                    )
                elif c["kind"] == "removed" and strategy == "add_coalesce_default":
                    t = types.get(col, "VARCHAR")
                    new = rewrite_refs(
                        src, col, lambda _m, t=t: f"cast(null as {t})", bare=f"cast(null as {t}) as {col}"
                    )
                elif c["kind"] == "nullability_changed" and strategy == "add_coalesce_default":
                    d = DEFAULTS.get(types.get(col, "VARCHAR"), "'unknown'")
                    new = rewrite_refs(
                        src,
                        col,
                        lambda _m, d=d, col=col: f"coalesce({col}, {d})",
                        bare=f"coalesce({col}, {d}) as {col}",
                    )
                else:
                    continue
                if new != src:
                    changed[path] = new
            if c["kind"] == "enum_symbols_added" and strategy == "update_data_test":
                path = "tests/data_tests.yaml"
                if path in files:
                    src = changed.get(path, files[path])
                    new = add_accepted_values(
                        src, e.get("tests", ctx.get("failing_tests", [])), c["details"]["symbols"]
                    )
                    if new != src:
                        changed[path] = new
        return {"files": changed, "summary": f"Edited {sorted(changed)}"}

    def _summary(self, ctx: dict[str, Any]) -> dict[str, Any]:
        b = ctx.get("counts", {})
        dashboards = ", ".join(ctx.get("dashboards", [])) or "no dashboards"
        outcome = ctx.get("outcome", "")
        return {
            "summary": (
                f"A schema change on {ctx.get('topic')} ({ctx.get('change_class')}) affects "
                f"{b.get('breaking', 0)} breaking and {b.get('degraded', 0)} degraded assets, reaching {dashboards}. "
                f"{outcome}"
            ).strip()
        }


# ---------------------------------------------------------------------- text edit helpers
def rewrite_refs(sql: str, col: str, repl: Any, bare: str) -> str:
    """Rewrite references to `col` in SQL text, line by line, outside comments.

    A select item that is just the column (``col`` or ``col,``) becomes `bare` (keeps the output
    name). Other references are replaced via `repl`, except an alias right after ``as``.
    """
    out = []
    word = re.compile(rf"(?<![\w.])(?<!as )(?<!AS ){re.escape(col)}\b")
    for line in sql.splitlines(keepends=True):
        code, sep, comment = line.partition("--")
        nl = "\n" if line.endswith("\n") and not sep else ""
        body = code.rstrip("\n")
        stripped = body.strip()
        if stripped.rstrip(",") == col:
            indent = body[: len(body) - len(body.lstrip())]
            comma = "," if stripped.endswith(",") else ""
            new_code = f"{indent}{bare}{comma}"
        else:
            new_code = word.sub(repl, body)
        out.append(new_code + (sep + comment if sep else nl))
    return "".join(out)


def add_accepted_values(yaml_text: str, test_names: list[str], symbols: list[str]) -> str:
    """Append symbols to the `values: [...]` list of the named accepted_values tests."""
    lines = yaml_text.splitlines(keepends=True)
    current: str | None = None
    for i, line in enumerate(lines):
        m = re.search(r"name:\s*([\w.-]+)", line)
        if m:
            current = m.group(1)
        if current in test_names and re.search(r"values:\s*\[", line):
            inner = re.search(r"\[(.*)\]", line)
            if inner:
                existing = [v.strip() for v in inner.group(1).split(",") if v.strip()]
                merged = existing + [s for s in symbols if s not in existing]
                lines[i] = line[: inner.start(1)] + ", ".join(merged) + line[inner.end(1) :]
    return "".join(lines)
