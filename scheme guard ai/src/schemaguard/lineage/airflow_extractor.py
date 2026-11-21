"""Static Airflow DAG parser (no Airflow import, no scheduler).

Reads DAG files with `ast` and extracts dag_id, owner, tasks, the topic/table each task reads or
writes (from literal `op_kwargs`) and `>>` dependencies. DAG files are treated as data: nothing in
them is executed.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TaskSpec:
    dag_id: str
    task_id: str
    operator: str
    callable: str | None
    kwargs: dict[str, Any] = field(default_factory=dict)
    upstream: list[str] = field(default_factory=list)
    file: str = ""
    line: int = 0

    @property
    def id(self) -> str:
        return f"{self.dag_id}.{self.task_id}"

    @property
    def reads_topic(self) -> str | None:
        return self.kwargs.get("topic")

    @property
    def sql_file(self) -> str | None:
        return self.kwargs.get("sql_file")

    @property
    def target(self) -> str | None:
        return self.kwargs.get("target")


@dataclass
class DagSpec:
    dag_id: str
    owner: str | None
    file: str
    tasks: list[TaskSpec] = field(default_factory=list)


def _literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None


def _kw(call: ast.Call, name: str) -> ast.AST | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _call_name(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def parse_dag_file(path: Path, root: Path | None = None) -> DagSpec | None:
    src = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    rel = str(Path(path).relative_to(root)).replace("\\", "/") if root else Path(path).name

    dag_id: str | None = None
    owner: str | None = None
    var_to_task: dict[str, TaskSpec] = {}
    tasks: list[TaskSpec] = []
    deps: list[tuple[list[str], list[str]]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) == "DAG":
            dag_id_node = _kw(node, "dag_id") or (node.args[0] if node.args else None)
            dag_id = _literal(dag_id_node) if dag_id_node is not None else None
            default_args = _kw(node, "default_args")
            da = _literal(default_args) if default_args is not None else None
            if isinstance(da, dict):
                owner = da.get("owner")

    if not dag_id:
        return None

    def names(n: ast.AST) -> list[str]:
        if isinstance(n, ast.Name):
            return [n.id]
        if isinstance(n, ast.List | ast.Tuple):
            return [e.id for e in n.elts if isinstance(e, ast.Name)]
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.RShift):
            # a >> b >> c  : the value of (a >> b) is b
            return names(n.right)
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            op = _call_name(call)
            if op.endswith("Operator") or op.endswith("Sensor"):
                task_id_node = _kw(call, "task_id")
                task_id = _literal(task_id_node) if task_id_node is not None else None
                if not isinstance(task_id, str):
                    continue
                kwargs_node = _kw(call, "op_kwargs")
                kwargs = _literal(kwargs_node) if kwargs_node is not None else {}
                callable_node = _kw(call, "python_callable")
                t = TaskSpec(
                    dag_id=dag_id,
                    task_id=task_id,
                    operator=op,
                    callable=callable_node.id if isinstance(callable_node, ast.Name) else None,
                    kwargs=kwargs if isinstance(kwargs, dict) else {},
                    file=rel,
                    line=node.lineno,
                )
                tasks.append(t)
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        var_to_task[tgt.id] = t
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.BinOp):
            chain: list[ast.AST] = []
            cur: ast.AST = node.value
            while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.RShift):
                chain.insert(0, cur.right)
                cur = cur.left
            chain.insert(0, cur)
            for a, b in zip(chain, chain[1:], strict=False):
                deps.append((names(a), names(b)))

    for ups, downs in deps:
        for d in downs:
            for u in ups:
                if d in var_to_task and u in var_to_task:
                    var_to_task[d].upstream.append(var_to_task[u].task_id)

    return DagSpec(dag_id=dag_id, owner=owner, file=rel, tasks=tasks)


def parse_dags(dags_dir: Path, root: Path | None = None) -> list[DagSpec]:
    out = []
    for p in sorted(Path(dags_dir).glob("*.py")):
        if p.name.startswith("_"):
            continue
        spec = parse_dag_file(p, root=root)
        if spec:
            out.append(spec)
    return out
