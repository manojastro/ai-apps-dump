"use client";

import { useEffect, useMemo, useState } from "react";
import { Background, Controls, MarkerType, MiniMap, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { getLineage } from "@/lib/api";

export default function LineagePage() {
  const [data, setData] = useState<any>({ nodes: [], edges: [] });
  const [selected, setSelected] = useState<any>(null);
  useEffect(() => {
    getLineage().then(setData).catch(() => {});
  }, []);
  const { nodes, edges } = useMemo(() => {
    const layers = ["source", "raw", "staging", "warehouse", "consumer"];
    const grouped: Record<string, any[]> = {};
    (data.nodes || []).forEach((n: any) => {
      (grouped[n.layer] ||= []).push(n);
    });
    const rfNodes = (data.nodes || []).map((n: any) => {
      const lane = Math.max(0, layers.indexOf(n.layer));
      const idx = (grouped[n.layer] || []).findIndex((x) => x.id === n.id);
      return {
        id: n.id,
        position: { x: lane * 240, y: idx * 90 },
        data: n,
        style: {
          background: "#12141c",
          color: "#e7eaf2",
          border: "1px solid #2a3040",
          borderRadius: 8,
          padding: 10,
          fontSize: 12,
          width: 180,
        },
      };
    });
    const rfEdges = (data.edges || []).map((e: any, i: number) => ({
      id: `${e.source}-${e.target}-${i}`,
      source: e.source,
      target: e.target,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#2dd4bf" },
      style: { stroke: "#2dd4bf" },
    }));
    return { nodes: rfNodes, edges: rfEdges };
  }, [data]);
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Lineage</h1>
      <div className="h-[640px] rounded-lg border border-line bg-ink-900">
        <ReactFlow nodes={nodes} edges={edges} fitView onNodeClick={(_, n) => setSelected(n.data)}>
          <MiniMap style={{ background: "#0b0d14" }} />
          <Controls />
          <Background color="#1f2430" />
        </ReactFlow>
      </div>
      {selected ? (
        <div className="rounded-lg border border-line p-4 text-sm">
          <div className="font-mono text-teal-200">{selected.id}</div>
          <div className="text-zinc-400 mt-1">
            layer {selected.layer} · health {selected.health} · rows {selected.row_count} · pipeline{" "}
            {selected.pipeline_id}
          </div>
        </div>
      ) : null}
    </div>
  );
}
