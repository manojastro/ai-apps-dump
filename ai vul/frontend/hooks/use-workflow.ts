"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import type { WorkflowDetail } from "@/lib/types";

const TERMINAL = new Set(["completed", "rejected", "failed", "blocked", "cancelled"]);

/**
 * Workflow detail + live updates. Uses Server-Sent Events backed by the durable event table;
 * if the stream is unavailable (proxy buffering, network) it falls back to polling.
 */
export function useWorkflow(runId: string) {
  const qc = useQueryClient();
  const [live, setLive] = useState<"connecting" | "streaming" | "polling" | "idle">("connecting");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const query = useQuery({
    queryKey: ["workflow", runId],
    queryFn: () => api.get<WorkflowDetail>(`/workflows/${runId}`),
    refetchInterval: (q) => {
      const status = q.state.data?.run.status;
      if (!status || TERMINAL.has(status)) return false;
      return live === "streaming" ? 15_000 : 3_000;
    },
  });
  const status = query.data?.run.status;
  const terminal = !!status && TERMINAL.has(status);

  useEffect(() => {
    if (terminal || typeof EventSource === "undefined") return; // "idle" is derived below
    const source = new EventSource(`/api/workflows/${runId}/stream`);
    const refresh = () => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => {
        qc.invalidateQueries({ queryKey: ["workflow", runId] });
        qc.invalidateQueries({ queryKey: ["dashboard"] });
      }, 250);
    };
    source.onopen = () => setLive("streaming");
    source.addEventListener("workflow", refresh);
    source.addEventListener("status", refresh);
    source.onerror = () => {
      setLive("polling");
      source.close();
    };
    return () => {
      source.close();
      if (timer.current) clearTimeout(timer.current);
    };
  }, [runId, terminal, qc]);

  return { ...query, live: terminal ? "idle" : live };
}
