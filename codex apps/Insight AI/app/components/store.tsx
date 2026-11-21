"use client";
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from "react";
import { api, setCsrf } from "@/lib/productionlens/api";
import {
  Incident,
  Run,
  Evaluation,
  Integrations,
  User,
  Demo,
  Evidence,
} from "@/lib/productionlens/types";

function useStore() {
  const [user, setUser] = useState<User | null>(null),
    [ready, setReady] = useState(false),
    [page, setPage] = useState("Overview"),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const [incidents, setIncidents] = useState<Incident[]>([]),
    [runs, setRuns] = useState<Run[]>([]),
    [evaluations, setEvaluations] = useState<Evaluation[]>([]),
    [integrations, setIntegrations] = useState<Integrations | null>(null),
    [demo, setDemo] = useState<Demo | null>(null);
  const [run, setRun] = useState<Run | null>(null),
    [evaluation, setEvaluation] = useState<Evaluation | null>(null),
    [evidence, setEvidence] = useState<Evidence | null>(null),
    [creating, setCreating] = useState(false);
  const refresh = useCallback(async () => {
    const [i, r, e, h, d] = await Promise.all([
      api<Incident[]>("/incidents"),
      api<Run[]>("/investigations"),
      api<Evaluation[]>("/evaluations"),
      api<Integrations>("/integrations"),
      api<Demo>("/demo"),
    ]);
    setIncidents(i);
    setRuns(r);
    setEvaluations(e);
    setIntegrations(h);
    setDemo(d);
  }, []);
  useEffect(() => {
    api<User>("/auth/me")
      .then((u) => {
        setUser(u);
        setCsrf(u.csrf);
      })
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);
  useEffect(() => {
    if (!user) return;
    const tick = () => refresh().catch((e) => setError(e.message));
    tick();
    const id = setInterval(tick, 3500);
    return () => clearInterval(id);
  }, [user, refresh]);
  useEffect(() => {
    if (!run?.id) return;
    const id = run.id;
    const update = () =>
      api<Run>(`/investigations/${id}`)
        .then(setRun)
        .catch((e) => setError(e.message));
    const events = new EventSource(`/api/investigations/${id}/events`);
    events.onmessage = update;
    const timer = setInterval(update, 3000);
    return () => {
      events.close();
      clearInterval(timer);
    };
  }, [run?.id]);
  useEffect(() => {
    if (
      !evaluation?.id ||
      ["completed", "cancelled", "failed"].includes(evaluation.status)
    )
      return;
    const id = setInterval(
      () =>
        api<Evaluation>(`/evaluations/${evaluation.id}`)
          .then(setEvaluation)
          .catch((e) => setError(e.message)),
      1800,
    );
    return () => clearInterval(id);
  }, [evaluation?.id, evaluation?.status]);
  async function act(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  async function openRun(id: string) {
    await act(async () => {
      setRun(await api<Run>(`/investigations/${id}`));
      setPage("Investigations");
    });
  }
  async function start(incident: Incident) {
    await act(async () => {
      const r = await api<Run>("/investigations", { incident_id: incident.id });
      setRun(await api<Run>(`/investigations/${r.id}`));
      setPage("Investigations");
    });
  }
  function navigate(name: string) {
    setPage(name);
    if (name !== "Investigations" && name !== "Action review") setRun(null);
  }
  return {
    user,
    setUser,
    ready,
    page,
    setPage,
    navigate,
    error,
    setError,
    notice,
    setNotice,
    busy,
    incidents,
    runs,
    evaluations,
    integrations,
    demo,
    setDemo,
    run,
    setRun,
    evaluation,
    setEvaluation,
    evidence,
    setEvidence,
    creating,
    setCreating,
    refresh,
    act,
    openRun,
    start,
  };
}
const Context = createContext<ReturnType<typeof useStore> | null>(null);
export function Store({ children }: { children: ReactNode }) {
  const store = useStore();
  return <Context.Provider value={store}>{children}</Context.Provider>;
}
export function useLens() {
  const context = useContext(Context);
  if (!context) throw new Error("ProductionLens store missing");
  return context;
}
