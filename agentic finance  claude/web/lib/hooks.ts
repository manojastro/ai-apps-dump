"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, errorText } from "./api";

export function useApi<T>(path: string | null, pollMs?: number | ((data: T | undefined) => number | undefined)) {
  const [data, setData] = useState<T | undefined>();
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const dataRef = useRef<T | undefined>(undefined);
  const load = useCallback(async () => {
    if (!path) return;
    try {
      const d = await api<T>(path);
      dataRef.current = d;
      setData(d);
      setError(undefined);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  }, [path]);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    let stopped = false;
    const tick = async () => {
      await load();
      const ms = typeof pollMs === "function" ? pollMs(dataRef.current) : pollMs;
      if (!stopped && ms) timer = setTimeout(tick, ms);
    };
    void tick();
    return () => { stopped = true; if (timer) clearTimeout(timer); };
  }, [load, pollMs]);
  return { data, error, loading, reload: load };
}
