"""Lineage extractors. Each one reads one kind of artefact (as data) and adds nodes/edges.

1. extract_avro        Avro schemas            -> Topic, Field, Owner
2. extract_airflow     DAG files (static ast)  -> Dag, Task, Table, raw Columns, CONSUMED_BY, WRITES
3. extract_sql         SQL transforms (sqlglot)-> Columns, DERIVES_FROM (value|join|filter|group)
4. extract_dashboards  dashboards.yaml         -> Dashboard, Visual, USED_BY, PART_OF, OWNED_BY
5. extract_data_tests  tests/data_tests.yaml   -> DataTest, TESTED_BY   (extension; see DECISIONS.md)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import sqlglot
import yaml
from sqlglot import exp
from sqlglot.lineage import lineage as sqlglot_lineage
from sqlglot.optimizer.qualify import qualify

from schemaguard.lineage.airflow_extractor import DagSpec, TaskSpec
from schemaguard.lineage.model import LineageGraph, column_id, field_id
from schemaguard.schemas.avro import RecordSchema

DIALECT = "duckdb"


def _layer(table: str) -> str:
    return table.split(".")[0]


def _owner(lg: LineageGraph, node: str, owner: str | None) -> None:
    if owner:
        lg.add_node(f"owner:{owner}", "Owner", name=owner)
        lg.add_edge(node, f"owner:{owner}", "OWNED_BY")


def ensure_column(lg: LineageGraph, table: str, col: str, **attrs: Any) -> str:
    tid = f"table:{table}"
    lg.add_node(tid, "Table", name=table, layer=_layer(table))
    cid = column_id(table, col)
    lg.add_node(cid, "Column", name=col, table=table, layer=_layer(table), **attrs)
    lg.add_edge(tid, cid, "HAS_COLUMN")
    return cid


# 1 -------------------------------------------------------------------------------------------
def extract_avro(lg: LineageGraph, schemas: dict[str, RecordSchema]) -> None:
    for topic, s in schemas.items():
        tid = f"topic:{topic}"
        lg.add_node(tid, "Topic", name=topic, record=s.full_name, doc=s.doc)
        _owner(lg, tid, s.owner)
        for f in s.fields:
            fid = field_id(topic, f.name)
            lg.add_node(
                fid,
                "Field",
                name=f.name,
                topic=topic,
                avro_type=f.type_label,
                nullable=f.nullable,
                symbols=list(f.symbols),
                doc=f.doc,
            )
            lg.add_edge(tid, fid, "HAS_FIELD")


# 2 -------------------------------------------------------------------------------------------
def extract_airflow(lg: LineageGraph, dags: list[DagSpec], schemas: dict[str, RecordSchema]) -> None:
    for d in dags:
        did = f"dag:{d.dag_id}"
        lg.add_node(did, "Dag", name=d.dag_id, file=d.file)
        _owner(lg, did, d.owner)
        for t in d.tasks:
            tid = f"task:{t.id}"
            lg.add_node(
                tid,
                "Task",
                name=t.task_id,
                dag=d.dag_id,
                operator=t.operator,
                file=t.file,
                line=t.line,
                sql_file=t.sql_file,
            )
            lg.add_edge(tid, did, "PART_OF")
            if t.target:
                table = f"table:{t.target}"
                lg.add_node(table, "Table", name=t.target, layer=_layer(t.target))
                lg.add_edge(tid, table, "WRITES")
                _owner(lg, table, d.owner)
            if t.reads_topic:
                topic_node = f"topic:{t.reads_topic}"
                lg.add_node(topic_node, "Topic", name=t.reads_topic)
                lg.add_edge(topic_node, tid, "CONSUMED_BY")
                schema = schemas.get(t.reads_topic)
                if schema and t.target:
                    for f in schema.fields:
                        cid = ensure_column(lg, t.target, f.name, dtype=f.duckdb_type)
                        lg.add_edge(
                            cid,
                            field_id(t.reads_topic, f.name),
                            "DERIVES_FROM",
                            via="ingest",
                            task=t.id,
                            transform="passthrough",
                        )


# 3 -------------------------------------------------------------------------------------------
def _expr_ops(select_expr: exp.Expr, col: exp.Column) -> tuple[list[str], str | None]:
    """Operators between the select expression root and a source column, outermost first."""
    ops: list[str] = []
    cast_to: str | None = None
    node: exp.Expr | None = col.parent
    while node is not None and node is not select_expr.parent:
        if isinstance(node, exp.Alias):
            node = node.parent
            continue
        if isinstance(node, exp.Cast):
            cast_to = cast_to or node.to.sql(dialect=DIALECT)
        if isinstance(node, exp.Anonymous):
            ops.append(str(node.name).lower())
        elif not isinstance(node, exp.Paren):
            ops.append(type(node).__name__.lower())
        node = node.parent
    ops.reverse()
    return ops, cast_to


def find_line(text: str, *patterns: str) -> int:
    lines = text.splitlines()
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            if rx.search(line.split("--")[0]):
                return i
    return 0


def _alias_map(tree: exp.Expr) -> dict[str, str]:
    out = {}
    for t in tree.find_all(exp.Table):
        full = f"{t.db}.{t.name}" if t.db else t.name
        out[t.alias_or_name] = full
        out[t.name] = full
    return out


def extract_sql(lg: LineageGraph, pipeline_dir: Path, sql_tasks: list[TaskSpec]) -> list[str]:
    """Add column-level lineage for SQL tasks (must be in dependency order). Returns warnings."""
    warnings: list[str] = []
    for t in sql_tasks:
        assert t.sql_file and t.target
        text = (Path(pipeline_dir) / t.sql_file).read_text(encoding="utf-8")
        sql = text.strip().rstrip(";")
        try:
            tree = sqlglot.parse_one(sql, dialect=DIALECT)
        except sqlglot.errors.ParseError as exc:
            warnings.append(f"{t.sql_file}: parse error {exc}")
            continue
        # sqlglot needs the columns of every upstream table.
        schema: dict[str, dict[str, dict[str, str]]] = {}
        for tbl in tree.find_all(exp.Table):
            full = f"{tbl.db}.{tbl.name}"
            cols = (
                {lg.node(c)["name"]: "varchar" for c, _ in lg.out(f"table:{full}", "HAS_COLUMN")}
                if lg.has(f"table:{full}")
                else {}
            )
            if not cols:
                warnings.append(f"{t.sql_file}: upstream table {full} unknown to lineage")
            schema.setdefault(tbl.db, {})[tbl.name] = cols

        outputs = list(tree.named_selects) if isinstance(tree, exp.Query) else []
        select_exprs = {e.alias_or_name: e for e in tree.selects} if isinstance(tree, exp.Query) else {}
        for out_col in outputs:
            cid = ensure_column(
                lg,
                t.target,
                out_col,
                sql_file=t.sql_file,
                line=find_line(
                    text, rf"\bas\s+{re.escape(out_col)}\b", rf"[\s.,]{re.escape(out_col)}\s*,?\s*$"
                ),
                expression=select_exprs[out_col].sql(dialect=DIALECT) if out_col in select_exprs else None,
            )
            try:
                root = sqlglot_lineage(out_col, sql, schema=schema, dialect=DIALECT)
            except Exception as exc:  # sqlglot raises several error types
                warnings.append(f"{t.sql_file}:{out_col}: lineage failed: {exc}")
                continue
            sel = select_exprs.get(out_col)
            for leaf in root.walk():
                if leaf.downstream or not isinstance(leaf.expression, exp.Table):
                    continue
                src_table = f"{leaf.expression.db}.{leaf.expression.name}"
                src_col = leaf.name.split(".")[-1]
                parent = column_id(src_table, src_col)
                if not lg.has(parent):
                    warnings.append(f"{t.sql_file}: {out_col} reads unknown column {src_table}.{src_col}")
                    ensure_column(lg, src_table, src_col, missing=True)
                ops: list[str] = []
                cast_to = None
                if sel is not None:
                    for c in sel.find_all(exp.Column):
                        if c.name == src_col:
                            ops, cast_to = _expr_ops(sel, c)
                            break
                lg.add_edge(
                    cid,
                    parent,
                    "DERIVES_FROM",
                    via="value",
                    sql_file=t.sql_file,
                    line=find_line(text, rf"\b{re.escape(src_col)}\b"),
                    expression=sel.sql(dialect=DIALECT) if sel is not None else None,
                    ops=ops,
                    cast_to=cast_to,
                    transform=_transform(ops),
                )

        # Columns used outside the projection (joins, filters, grouping) affect every output row.
        try:
            qtree = qualify(
                tree.copy(), schema=cast(Any, schema), dialect=DIALECT, validate_qualify_columns=False
            )
        except Exception:
            qtree = tree
        aliases = _alias_map(qtree)
        clauses: list[tuple[str, list[exp.Expr]]] = [
            ("join", [j.args["on"] for j in qtree.find_all(exp.Join) if j.args.get("on") is not None]),
            ("filter", [w for w in (qtree.args.get("where"), qtree.args.get("having")) if w is not None]),
            ("group", [g for g in [qtree.args.get("group")] if g is not None]),
        ]
        for via, nodes in clauses:
            for node in nodes:
                for c in node.find_all(exp.Column):
                    table = (
                        aliases.get(c.table)
                        if c.table
                        else (next(iter(set(aliases.values()))) if len(set(aliases.values())) == 1 else None)
                    )
                    if not table:
                        continue
                    parent = column_id(table, c.name)
                    if not lg.has(parent):
                        continue
                    for out_col in outputs:
                        child = column_id(t.target, out_col)
                        has_value = any(
                            d.get("via") == "value"
                            for d in (lg.g.get_edge_data(child, parent) or {}).values()
                        )
                        if not has_value:
                            lg.add_edge(
                                child,
                                parent,
                                "DERIVES_FROM",
                                via=via,
                                sql_file=t.sql_file,
                                line=find_line(
                                    text,
                                    rf"\b{re.escape(c.name)}\b\s*(<>|=|!=|<|>|in\b|is\b)",
                                    rf"\b{re.escape(c.name)}\b",
                                ),
                                expression=node.sql(dialect=DIALECT)[:200],
                                transform=via,
                            )
    return warnings


def _transform(ops: list[str]) -> str:
    aggs = {"sum", "avg", "min", "max", "count", "stddev", "median"}
    arith = {"add", "sub", "mul", "div", "mod"}
    if not ops:
        return "passthrough"
    if any(o in aggs for o in ops):
        return "aggregate"
    if any(o in arith for o in ops):
        return "arithmetic"
    if ops[0] == "cast" or "cast" in ops:
        return "cast"
    if "coalesce" in ops:
        return "coalesce"
    return "function"


# 4 -------------------------------------------------------------------------------------------
def extract_dashboards(lg: LineageGraph, manifest: Path) -> list[str]:
    warnings = []
    data = yaml.safe_load(Path(manifest).read_text(encoding="utf-8")) or {}
    for d in data.get("dashboards", []):
        did = f"dashboard:{d['name']}"
        lg.add_node(did, "Dashboard", name=d["name"], tool=d.get("tool"))
        _owner(lg, did, d.get("owner"))
        for v in d.get("visuals", []):
            vid = f"visual:{d['name']}/{v['name']}"
            lg.add_node(vid, "Visual", name=v["name"], dashboard=d["name"])
            lg.add_edge(vid, did, "PART_OF")
            for ref in v.get("columns", []):
                table, col = ref.rsplit(".", 1)
                cid = column_id(table, col)
                if not lg.has(cid):
                    warnings.append(
                        f"dashboard '{d['name']}' visual '{v['name']}' references unknown column {ref}"
                    )
                    ensure_column(lg, table, col, missing=True)
                lg.add_edge(cid, vid, "USED_BY")
    return warnings


# 5 -------------------------------------------------------------------------------------------
def extract_data_tests(lg: LineageGraph, tests_file: Path) -> None:
    data = yaml.safe_load(Path(tests_file).read_text(encoding="utf-8")) or {}
    for t in data.get("tests", []):
        tid = f"test:{t['name']}"
        lg.add_node(
            tid, "DataTest", name=t["name"], test_type=t["type"], values=t.get("values"), table=t.get("table")
        )
        refs: list[tuple[str, str]] = []
        if t.get("table") and t.get("column"):
            refs.append((t["table"], t["column"]))
        for key in ("left", "right"):
            if t.get(key):
                tree = sqlglot.parse_one(t[key], dialect=DIALECT)
                tables = [f"{x.db}.{x.name}" for x in tree.find_all(exp.Table)]
                for c in tree.find_all(exp.Column):
                    if len(tables) == 1:
                        refs.append((tables[0], c.name))
        for table, col in refs:
            cid = column_id(table, col)
            if lg.has(cid):
                lg.add_edge(cid, tid, "TESTED_BY")
