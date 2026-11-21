import { api } from "../api";

type Graph = { nodes: Array<{ id: string; kind: string; team: string }>; edges: Array<{ source: string; target: string; type: string }> };

export default async function GraphPage() {
  const graph = await api<Graph>("/api/v1/graph");
  return <><header className="page-head"><div><div className="eyebrow">Neo4j topology projection</div><h1>Service dependency graph</h1><p>Investigation context across {graph.nodes.length} components and {graph.edges.length} relationships.</p></div></header><section className="card graph-canvas">{graph.nodes.map((node) => <div className="graph-node" key={node.id}><strong>{node.id}</strong><small>{node.kind} · {node.team}</small></div>)}<h2>Dependency edges</h2>{graph.edges.map((edge) => <span className="badge" key={`${edge.source}-${edge.target}`}>{edge.source} → {edge.target} ({edge.type})</span>)}</section></>;
}

