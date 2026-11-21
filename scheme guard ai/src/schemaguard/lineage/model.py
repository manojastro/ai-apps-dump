"""Lineage graph model and the deterministic graph queries.

Node ids are typed strings:  topic:orders.v1  field:orders.v1.amount  dag:build_staging
task:build_staging.stg_orders  table:stg.stg_orders  column:stg.stg_orders.amount
dashboard:Sales Overview  visual:Sales Overview/Revenue by Day  owner:finance  test:<name>

Edges are stored in their natural direction:
  HAS_FIELD topic->field, CONSUMED_BY topic->task, WRITES task->table, HAS_COLUMN table->column,
  DERIVES_FROM column->(column|field)  [child points at parent; attr `via` = ingest|value|join|filter|group],
  USED_BY column->visual, PART_OF visual->dashboard and task->dag, OWNED_BY *->owner,
  TESTED_BY column->test.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any, Literal

import networkx as nx

NodeType = Literal[
    "Topic", "Field", "Dag", "Task", "Table", "Column", "Dashboard", "Visual", "Owner", "DataTest"
]
EdgeType = Literal[
    "HAS_FIELD",
    "CONSUMED_BY",
    "WRITES",
    "HAS_COLUMN",
    "DERIVES_FROM",
    "USED_BY",
    "PART_OF",
    "OWNED_BY",
    "TESTED_BY",
]
VIA_RANK = {"ingest": 0, "value": 0, "join": 1, "filter": 2, "group": 3}


def field_id(topic: str, name: str) -> str:
    return f"field:{topic}.{name}"


def column_id(table: str, col: str) -> str:
    return f"column:{table}.{col}"


@dataclass
class ImpactedNode:
    id: str
    type: str
    depth: int
    path: list[str]
    vias: list[str] = field(default_factory=list)  # edge `via` along the path (DERIVES_FROM hops)
    context: bool = False  # True for tables/tasks/dags/owners reached as context, not data flow

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "depth": self.depth,
            "path": self.path,
            "vias": self.vias,
            "context": self.context,
        }


class LineageGraph:
    def __init__(self) -> None:
        self.g: nx.MultiDiGraph = nx.MultiDiGraph()

    # ---------- building ----------
    def add_node(self, node_id: str, type_: NodeType, **attrs: Any) -> None:
        if node_id in self.g:
            self.g.nodes[node_id].update({k: v for k, v in attrs.items() if v is not None})
        else:
            self.g.add_node(node_id, type=type_, **{k: v for k, v in attrs.items() if v is not None})

    def add_edge(self, src: str, dst: str, type_: EdgeType, **attrs: Any) -> None:
        existing = self.g.get_edge_data(src, dst) or {}
        for data in existing.values():
            if data.get("type") == type_ and data.get("via") == attrs.get("via"):
                return
        self.g.add_edge(src, dst, type=type_, **attrs)

    # ---------- accessors ----------
    def node(self, node_id: str) -> dict[str, Any]:
        return dict(self.g.nodes[node_id])

    def has(self, node_id: str) -> bool:
        return node_id in self.g

    def nodes_of(self, type_: str) -> list[str]:
        return sorted(n for n, d in self.g.nodes(data=True) if d.get("type") == type_)

    def edges(self) -> list[tuple[str, str, dict[str, Any]]]:
        return [(u, v, dict(d)) for u, v, d in self.g.edges(data=True)]

    def out(self, node_id: str, type_: str) -> list[tuple[str, dict[str, Any]]]:
        return [(v, d) for _, v, d in self.g.out_edges(node_id, data=True) if d.get("type") == type_]

    def inn(self, node_id: str, type_: str) -> list[tuple[str, dict[str, Any]]]:
        return [(u, d) for u, _, d in self.g.in_edges(node_id, data=True) if d.get("type") == type_]

    def content_hash(self) -> str:
        payload = {
            "nodes": sorted(
                (n, json.dumps(d, sort_keys=True, default=str)) for n, d in self.g.nodes(data=True)
            ),
            "edges": sorted(
                (u, v, json.dumps(d, sort_keys=True, default=str)) for u, v, d in self.g.edges(data=True)
            ),
        }
        return hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:16]

    # ---------- flow ----------
    def _flow_children(self, node_id: str) -> list[tuple[str, dict[str, Any]]]:
        """Data-flow successors: where values of `node_id` go next."""
        out: list[tuple[str, dict[str, Any]]] = []
        out += self.out(node_id, "HAS_FIELD")
        out += self.inn(node_id, "DERIVES_FROM")  # children point at parents
        out += self.out(node_id, "USED_BY")
        out += self.out(node_id, "TESTED_BY")
        if self.g.nodes[node_id].get("type") == "Visual":
            out += self.out(node_id, "PART_OF")
        return out

    def _flow_parents(self, node_id: str) -> list[tuple[str, dict[str, Any]]]:
        out: list[tuple[str, dict[str, Any]]] = []
        out += self.inn(node_id, "HAS_FIELD")
        out += self.out(node_id, "DERIVES_FROM")
        out += self.inn(node_id, "USED_BY")
        out += self.inn(node_id, "TESTED_BY")
        if self.g.nodes[node_id].get("type") == "Dashboard":
            out += self.inn(node_id, "PART_OF")
        return out

    def _bfs(self, start: str, step: Any, max_depth: int) -> list[ImpactedNode]:
        if start not in self.g:
            raise KeyError(f"node {start!r} not in lineage graph")
        best: dict[str, ImpactedNode] = {}
        q: deque[ImpactedNode] = deque([ImpactedNode(start, self.g.nodes[start]["type"], 0, [start])])

        def rank(n: ImpactedNode) -> tuple[int, int]:
            return (max((VIA_RANK.get(v, 0) for v in n.vias), default=0), n.depth)

        while q:
            cur = q.popleft()
            if cur.depth >= max_depth:
                continue
            for nxt, data in step(cur.id):
                if nxt in cur.path:
                    continue
                vias = cur.vias + ([data["via"]] if data.get("via") else [])
                cand = ImpactedNode(nxt, self.g.nodes[nxt]["type"], cur.depth + 1, cur.path + [nxt], vias)
                prev = best.get(nxt)
                if prev is None or rank(cand) < rank(prev):
                    best[nxt] = cand
                    q.append(cand)
        return sorted(best.values(), key=lambda n: (n.depth, n.id))

    # ---------- queries ----------
    def downstream(
        self, node_id: str, max_depth: int = 12, include_context: bool = True
    ) -> list[ImpactedNode]:
        """Everything downstream of a node, each with its best path (value edges preferred)."""
        flow = self._bfs(node_id, self._flow_children, max_depth)
        if not include_context:
            return flow
        ctx: dict[str, ImpactedNode] = {}
        for n in flow:
            if n.type == "Column":
                for table, _ in self.inn(n.id, "HAS_COLUMN"):
                    self._ctx(ctx, table, n, flow)
                    for task, _ in self.inn(table, "WRITES"):
                        self._ctx(ctx, task, n, flow, extra=[table])
                        for dag, _ in self.out(task, "PART_OF"):
                            self._ctx(ctx, dag, n, flow, extra=[table, task])
                    for owner, _ in self.out(table, "OWNED_BY"):
                        self._ctx(ctx, owner, n, flow, extra=[table])
            if n.type == "Dashboard":
                for owner, _ in self.out(n.id, "OWNED_BY"):
                    self._ctx(ctx, owner, n, flow)
        return flow + sorted(ctx.values(), key=lambda n: (n.type, n.id))

    def _ctx(
        self,
        ctx: dict[str, ImpactedNode],
        node: str,
        via: ImpactedNode,
        flow: list[ImpactedNode],
        extra: list[str] | None = None,
    ) -> None:
        if node in ctx or any(f.id == node for f in flow):
            return
        path = via.path + (extra or []) + [node]
        ctx[node] = ImpactedNode(
            node, self.g.nodes[node]["type"], len(path) - 1, path, via.vias, context=True
        )

    def flow_digraph(self) -> nx.DiGraph:
        """Data-flow DiGraph (parent -> child). Parallel edges collapse to the best `via`."""
        dg: nx.DiGraph = nx.DiGraph()
        for n in self.g.nodes:
            for child, data in self._flow_children(n):
                prev = dg.get_edge_data(n, child)
                if prev is None or VIA_RANK.get(data.get("via", "value"), 0) < VIA_RANK.get(
                    prev.get("via", "value"), 0
                ):
                    dg.add_edge(n, child, **data)
        return dg

    def paths_between(
        self, src: str, dst: str, limit: int = 20, dg: nx.DiGraph | None = None
    ) -> list[list[dict[str, Any]]]:
        """All simple data-flow paths src -> dst (shortest first), each as a list of hop dicts."""
        dg = dg if dg is not None else self.flow_digraph()
        if src not in dg or dst not in dg:
            return []
        out = []
        for i, p in enumerate(nx.shortest_simple_paths(dg, src, dst)):
            if i >= limit:
                break
            hops = []
            for u, v in zip(p, p[1:], strict=False):
                d = dg.get_edge_data(u, v)
                hops.append(
                    {"from": u, "to": v, "edge": d.get("type"), **{k: x for k, x in d.items() if k != "type"}}
                )
            out.append(hops)
        return out

    def upstream(self, node_id: str, max_depth: int = 12) -> list[ImpactedNode]:
        return self._bfs(node_id, self._flow_parents, max_depth)

    def label(self, node_id: str) -> str:
        d = self.g.nodes[node_id]
        t = d["type"]
        if t == "Field":
            return f"{d['topic']}.{d['name']}"
        if t == "Column":
            return f"{d['table'].split('.')[-1]}.{d['name']}"
        if t == "Visual":
            return f"{d['dashboard']} / {d['name']}"
        return str(d.get("name", node_id.split(":", 1)[-1]))

    def impact_paths(self, node_id: str, include_raw: bool = False) -> list[str]:
        """Human-readable paths from a field/column to every visual (and to leaf columns)."""
        flow = self.downstream(node_id, include_context=False)
        terminals = [
            n
            for n in flow
            if n.type == "Visual"
            or (
                n.type == "Column"
                and not any(
                    self.g.nodes[c]["type"] in ("Column", "Visual") for c, _ in self._flow_children(n.id)
                )
            )
        ]
        lines = []
        for t in terminals:
            hops = [h for h in t.path if include_raw or self.g.nodes[h].get("layer") != "raw"]
            text = " → ".join(self.label(h) for h in hops)
            worst = max(t.vias, key=lambda v: VIA_RANK.get(v, 0), default="value")
            if VIA_RANK.get(worst, 0) > 0:
                text += f"  (via {worst})"
            lines.append(text)
        return sorted(set(lines))

    def owner_of(self, node_id: str) -> str | None:
        d = self.g.nodes[node_id]
        t = d["type"]
        if t in ("Dashboard", "Table", "Topic", "Dag"):
            owners = self.out(node_id, "OWNED_BY")
            return owners[0][0].split(":", 1)[1] if owners else None
        if t == "Visual":
            dash = self.out(node_id, "PART_OF")
            return self.owner_of(dash[0][0]) if dash else None
        if t == "Column":
            tables = self.inn(node_id, "HAS_COLUMN")
            return self.owner_of(tables[0][0]) if tables else None
        if t == "DataTest":
            cols = self.inn(node_id, "TESTED_BY")
            return self.owner_of(cols[0][0]) if cols else None
        if t == "Field":
            topics = self.inn(node_id, "HAS_FIELD")
            return self.owner_of(topics[0][0]) if topics else None
        if t == "Task":
            dags = self.out(node_id, "PART_OF")
            return self.owner_of(dags[0][0]) if dags else None
        return None

    def blast_radius_summary(self, node_id: str) -> dict[str, Any]:
        nodes = [n for n in self.downstream(node_id) if n.type != "Owner"]
        by_type = Counter(n.type for n in nodes)
        by_owner: Counter[str] = Counter()
        for n in nodes:
            if n.type in ("Column", "Visual", "Dashboard", "DataTest") and not n.context:
                by_owner[self.owner_of(n.id) or "unowned"] += 1
        return {
            "node": node_id,
            "by_type": dict(sorted(by_type.items())),
            "by_owner": dict(sorted(by_owner.items())),
            "dashboards": sorted(self.label(n.id) for n in nodes if n.type == "Dashboard"),
            "owners_to_notify": sorted(by_owner),
        }

    # ---------- (de)serialisation ----------
    def to_records(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        nodes = [
            {"id": n, "type": d["type"], "attrs": {k: v for k, v in d.items() if k != "type"}}
            for n, d in self.g.nodes(data=True)
        ]
        edges = [
            {"src": u, "dst": v, "type": d["type"], "attrs": {k: x for k, x in d.items() if k != "type"}}
            for u, v, d in self.g.edges(data=True)
        ]
        return nodes, edges

    @classmethod
    def from_records(cls, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> LineageGraph:
        lg = cls()
        for n in nodes:
            lg.g.add_node(n["id"], type=n["type"], **n.get("attrs", {}))
        for e in edges:
            lg.g.add_edge(e["src"], e["dst"], type=e["type"], **e.get("attrs", {}))
        return lg

    def to_dot(self, focus: list[str] | None = None, verdicts: dict[str, str] | None = None) -> str:
        """Graphviz DOT for the UI (subgraph of `focus` nodes if given)."""
        colors = {"breaking": "#e5484d", "degraded": "#f5a524", "safe": "#46a758"}
        keep = set(focus) if focus else set(self.g.nodes)
        lines = [
            "digraph lineage {",
            "rankdir=LR;",
            'node [shape=box, style="rounded,filled", fillcolor="#f4f4f5", fontsize=10];',
        ]
        for n in sorted(keep):
            if n not in self.g:
                continue
            v = (verdicts or {}).get(n)
            fill = colors.get(v or "", "#f4f4f5")
            t = self.g.nodes[n]["type"]
            lines.append(f'"{n}" [label="{self.label(n)}\\n<{t}>", fillcolor="{fill}"];')
        for u, v, d in self.g.edges(data=True):
            if (
                u in keep
                and v in keep
                and d["type"] in ("DERIVES_FROM", "USED_BY", "PART_OF", "HAS_FIELD", "TESTED_BY")
            ):
                if d["type"] == "DERIVES_FROM":
                    style = "solid" if d.get("via") in ("value", "ingest") else "dashed"
                    lines.append(f'"{v}" -> "{u}" [style={style}, label="{d.get("via", "")}", fontsize=8];')
                else:
                    lines.append(f'"{u}" -> "{v}";')
        lines.append("}")
        return "\n".join(lines)
