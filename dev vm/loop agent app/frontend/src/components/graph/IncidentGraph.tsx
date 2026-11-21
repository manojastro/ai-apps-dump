"use client";

import { useEffect, useMemo } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { statusTone } from "@/lib/utils";

function GraphNode({ data }: any) {
  const tone = statusTone(data.status);
  return (
    <div className={`min-w-[170px] rounded-md border px-3 py-2 bg-ink-800 shadow-glow ${tone}`}>
      <div className="text-[10px] uppercase tracking-[0.14em] opacity-70">{data.subgraph}</div>
      <div className="text-[12px] font-medium leading-tight mt-0.5">{data.label}</div>
      <div className="text-[10px] mt-1 font-mono">{data.status}</div>
    </div>
  );
}

const nodeTypes = { sentinel: GraphNode };

export default function IncidentGraph({ graph, onSelect }: { graph: any; onSelect?: (n: any) => void }) {
  const { nodes, edges } = useMemo(() => {
    if (!graph?.nodes) return { nodes: [], edges: [] };
    const byLane: Record<number, any[]> = {};
    graph.nodes.forEach((n: any) => {
      (byLane[n.lane] ||= []).push(n);
    });
    const rfNodes = graph.nodes.map((n: any) => {
      const laneNodes = byLane[n.lane] || [];
      const idx = laneNodes.findIndex((x) => x.id === n.id);
      return {
        id: n.id,
        type: "sentinel",
        position: { x: n.lane * 230, y: idx * 86 },
        data: n,
      };
    });
    const rfEdges = (graph.edges || []).map((e: any, i: number) => ({
      id: `${e.source}-${e.target}-${i}`,
      source: e.source,
      target: e.target,
      animated: e.type === "cycle" || e.type === "fanout",
      label: e.label,
      style: {
        stroke: e.type === "cycle" ? "#f59e0b" : e.type === "fanout" ? "#2dd4bf" : "#64748b",
      },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
    }));
    return { nodes: rfNodes, edges: rfEdges };
  }, [graph]);

  useEffect(() => {}, [graph]);

  return (
    <div className="h-[640px] rounded-lg border border-line bg-ink-900 grid-fade">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.3}
        onNodeClick={(_, n) => onSelect?.(n.data)}
      >
        <MiniMap pannable zoomable style={{ background: "#0b0d14" }} />
        <Controls />
        <Background color="#1f2430" gap={18} />
      </ReactFlow>
    </div>
  );
}
