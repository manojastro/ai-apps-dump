"use client";

import {
  Background,
  type Edge,
  Handle,
  MarkerType,
  type Node,
  type NodeProps,
  Position,
  ReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import { Bot, CircleDot, Lock, ShieldCheck, UserCheck } from "lucide-react";
import { useMemo } from "react";

import "@xyflow/react/dist/style.css";

import type { Topology, TopologyNode } from "@/lib/types";
import { cn } from "@/lib/utils";

type NodeState = { status: string; attempts?: number; latency_ms?: number | null };
type FlowNodeData = { node: TopologyNode; state?: NodeState; selected: boolean; horizontal: boolean };

const MAIN = ["ingest", "normalize", "correlate_asset", "enrich_threat", "calculate_risk", "plan_remediation",
  "analyze_change_impact", "validate_evidence", "human_approval", "servicenow_write_gate", "sync_servicenow",
  "await_evidence", "verify_remediation", "final_report"];
const SIDE: Record<string, number> = { manual_review: 4.5, record_rejection: 8.5, await_sync_retry: 10.5 };

function position(id: string, horizontal: boolean): { x: number; y: number } {
  const i = MAIN.indexOf(id);
  const main = i >= 0 ? i : SIDE[id] ?? 0;
  const lane = i >= 0 ? 0 : 1;
  return horizontal ? { x: main * 190, y: lane * 130 } : { x: lane * 240, y: main * 92 };
}

const STATUS_STYLE: Record<string, string> = {
  completed: "border-risk-low/60 bg-risk-low/10",
  running: "border-primary bg-primary/15 shadow-[0_0_0_3px_color-mix(in_oklch,var(--primary),transparent_75%)]",
  waiting: "border-risk-medium bg-risk-medium/15",
  failed: "border-risk-critical bg-risk-critical/15",
  retrying: "border-risk-high bg-risk-high/15",
};

const KIND_ICON = { agent: Bot, human: UserCheck, gate: Lock, system: CircleDot } as const;

function AgentNode({ data }: NodeProps<Node<FlowNodeData>>) {
  const { node, state, selected, horizontal } = data;
  const Icon = node.id === "final_report" ? ShieldCheck : KIND_ICON[node.kind];
  const status = state?.status;
  return (
    <div
      className={cn(
        "w-[172px] rounded-lg border bg-card px-2.5 py-2 text-left text-card-foreground transition-colors",
        status ? STATUS_STYLE[status] ?? "" : "border-border opacity-60",
        selected && "ring-2 ring-ring",
      )}
    >
      <Handle type="target" position={horizontal ? Position.Left : Position.Top} className="!size-1.5 !border-0 !bg-muted-foreground" />
      <div className="flex items-center gap-1.5">
        <Icon className={cn("size-3.5 shrink-0", status === "running" ? "animate-pulse text-primary" : "text-muted-foreground")} />
        <span className="truncate text-[11px] font-semibold">{node.label}</span>
      </div>
      <div className="mt-0.5 flex items-center justify-between text-[10px] text-muted-foreground">
        <span className="capitalize">{status ?? (node.kind === "agent" ? "pending" : node.kind)}</span>
        <span className="tabular">
          {state?.attempts && state.attempts > 1 ? `${state.attempts}× · ` : ""}
          {state?.latency_ms !== undefined && state?.latency_ms !== null ? `${state.latency_ms}ms` : ""}
        </span>
      </div>
      <Handle type="source" position={horizontal ? Position.Right : Position.Bottom} className="!size-1.5 !border-0 !bg-muted-foreground" />
    </div>
  );
}

const nodeTypes = { agent: AgentNode };

export function WorkflowGraph({
  topology,
  states,
  selected,
  onSelect,
  horizontal = false,
  className,
}: {
  topology: Topology;
  states: Record<string, NodeState>;
  selected?: string | null;
  onSelect?: (id: string) => void;
  horizontal?: boolean;
  className?: string;
}) {
  const nodes = useMemo<Node<FlowNodeData>[]>(
    () =>
      topology.nodes.map((n) => ({
        id: n.id,
        type: "agent",
        position: position(n.id, horizontal),
        data: { node: n, state: states[n.id], selected: selected === n.id, horizontal },
        draggable: false,
      })),
    [topology, states, selected, horizontal],
  );
  const edges = useMemo<Edge[]>(
    () =>
      topology.edges.map(([source, target, label]) => {
        const traversed = !!states[source] && !!states[target];
        return {
          id: `${source}-${target}-${label}`,
          source,
          target,
          label: label || undefined,
          animated: states[target]?.status === "running",
          markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14 },
          style: { stroke: traversed ? "var(--primary)" : "var(--muted-foreground)", strokeOpacity: traversed ? 0.9 : 0.35, strokeWidth: traversed ? 1.8 : 1 },
          labelStyle: { fontSize: 9, fill: "var(--muted-foreground)" },
          labelBgStyle: { fill: "var(--card)" },
        };
      }),
    [topology, states],
  );
  return (
    <div className={cn("h-full min-h-[420px] w-full", className)}>
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.08 }}
          minZoom={0.2}
          nodesConnectable={false}
          elementsSelectable={false}
          onNodeClick={(_, n) => onSelect?.(n.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={18} size={1} color="var(--border)" />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}
