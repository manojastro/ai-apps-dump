"use client";

import { X } from "lucide-react";
import Link from "next/link";
import { type ReactNode, createContext, useContext, useEffect, useState } from "react";

import { Button } from "@/components/ui/primitives";
import { ErrorNote, LoadingBlock } from "@/components/shared";
import { api } from "@/lib/api";

const CITATION = /\[([a-z_]+#[A-Za-z0-9_]+)\]/g;

const OpenSource = createContext<(cite: string) => void>(() => undefined);

/** Renders text, turning each [deals#412] marker into a clickable source chip. */
export function CitedText({ text }: { text: string }) {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    const index = match.index ?? 0;
    parts.push(text.slice(last, index));
    parts.push(<CitationChip key={`${index}-${match[1]}`} cite={match[1]} />);
    last = index + match[0].length;
  }
  parts.push(text.slice(last));
  return <span className="whitespace-pre-wrap">{parts}</span>;
}

export function CitationChip({ cite }: { cite: string }) {
  const open = useContext(OpenSource);
  const [table, id] = cite.split("#");
  const base = "mx-0.5 inline-flex items-center rounded border bg-accent px-1 text-[11px] font-medium text-accent-foreground hover:underline";
  if (table === "forecast") {
    return <Link href="/" className={base}>{cite}</Link>;
  }
  return (
    <button type="button" onClick={() => open(cite)} className={base} aria-label={`Open source ${table} ${id}`}>
      {cite}
    </button>
  );
}

export function SourceDrawerProvider({ children }: { children: ReactNode }) {
  const [cite, setCite] = useState<string | null>(null);
  return (
    <OpenSource.Provider value={setCite}>
      {children}
      {cite && <SourceDrawer cite={cite} onClose={() => setCite(null)} />}
    </OpenSource.Provider>
  );
}

function pageFor(table: string, record: Record<string, unknown>, id: string) {
  if (table === "deals") return `/deals/${id}`;
  if (table === "accounts") return `/accounts/${id}`;
  if (typeof record.account_id === "number") return `/accounts/${record.account_id}`;
  if (typeof record.deal_id === "number") return `/deals/${record.deal_id}`;
  return null;
}

function SourceDrawer({ cite, onClose }: { cite: string; onClose: () => void }) {
  const [table, id] = cite.split("#");
  const [record, setRecord] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRecord(null);
    setError(null);
    api<{ record: Record<string, unknown> }>(`/sources/${table}/${id}`)
      .then((result) => setRecord(result.record))
      .catch(() => setError("This source was not found, or you do not have access to it."));
  }, [table, id]);

  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [onClose]);

  const link = record ? pageFor(table, record, id) : null;
  return (
    <aside
      role="dialog"
      aria-label={`Source ${cite}`}
      className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l bg-card shadow-xl"
    >
      <header className="flex items-center justify-between border-b p-3">
        <h2 className="text-sm font-semibold">Source: {cite}</h2>
        <Button variant="ghost" size="icon" aria-label="Close source" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </header>
      <div className="flex-1 overflow-y-auto p-3">
        {error && <ErrorNote message={error} />}
        {!error && !record && <LoadingBlock rows={6} />}
        {record && (
          <dl className="space-y-2 text-sm">
            {Object.entries(record).map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs text-muted-foreground">{key}</dt>
                <dd className="break-words">
                  {value === null ? "-" : typeof value === "object" ? JSON.stringify(value) : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        )}
      </div>
      {link && (
        <footer className="border-t p-3">
          <Button asChild size="sm" variant="outline" onClick={onClose}>
            <Link href={link}>Open full record</Link>
          </Button>
        </footer>
      )}
    </aside>
  );
}
