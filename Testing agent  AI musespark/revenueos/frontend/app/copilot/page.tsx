"use client";

import { AlertTriangle, Send } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";

import { CitedText } from "@/components/citations";
import { ErrorNote, PageHeader } from "@/components/shared";
import { Button, Card, CardContent, Input } from "@/components/ui/primitives";
import { ApiError, api, useApi } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";
import { titleCase } from "@/lib/utils";

interface Turn {
  role: "user" | "assistant";
  content: string;
  meta?: ChatResponse;
}

const SUGGESTIONS = [
  "Which deals are most at risk this quarter, and why?",
  "What changed in the forecast since last week?",
  "How much ARR is at risk, and which accounts drive it?",
  "Summarise recent SSO tickets.",
];

export default function CopilotPage() {
  const status = useApi<{ configured: boolean; model: string }>("/copilot/status");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => end.current?.scrollIntoView({ behavior: "smooth" }), [turns, busy]);

  const ask = async (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    setInput("");
    const history = turns.slice(-6).map(({ role, content }) => ({ role, content }));
    setTurns((current) => [...current, { role: "user", content: text }]);
    try {
      const reply = await api<ChatResponse>("/copilot/chat", {
        method: "POST",
        body: JSON.stringify({ question: text, history }),
      });
      setTurns((current) => [...current, { role: "assistant", content: reply.answer, meta: reply }]);
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "The copilot request failed.");
    } finally {
      setBusy(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void ask(input);
  };

  const unavailable = status.data?.configured === false;

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col">
      <PageHeader title="Copilot" description="Answers come only from your data, with a source for every claim. It cannot send anything." />
      {unavailable && (
        <div className="mb-3">
          <ErrorNote message="Copilot is not configured. Set ANTHROPIC_API_KEY on the server to enable it." />
        </div>
      )}
      <Card className="flex min-h-0 flex-1 flex-col">
        <CardContent className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4" aria-live="polite">
          {turns.length === 0 && (
            <div className="mx-auto max-w-xl pt-8">
              <p className="mb-3 text-center text-sm text-muted-foreground">Try one of these</p>
              <div className="grid gap-2 sm:grid-cols-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    disabled={unavailable}
                    onClick={() => void ask(suggestion)}
                    className="rounded-md border bg-card p-3 text-left text-sm hover:bg-muted disabled:opacity-50"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          {turns.map((turn, index) => (
            <div key={index} className={turn.role === "user" ? "flex justify-end" : ""}>
              <div className={turn.role === "user" ? "max-w-xl rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground" : "max-w-3xl text-sm leading-relaxed"}>
                {turn.role === "assistant" ? <CitedText text={turn.content} /> : turn.content}
                {turn.meta && <TurnFooter meta={turn.meta} />}
              </div>
            </div>
          ))}
          {busy && <p className="text-sm text-muted-foreground">Checking your data...</p>}
          {error && <ErrorNote message={error} />}
          <div ref={end} />
        </CardContent>
        <form onSubmit={submit} className="flex gap-2 border-t p-3">
          <Input
            aria-label="Ask the copilot"
            placeholder="Ask about deals, the forecast or retention"
            value={input}
            maxLength={2000}
            disabled={unavailable}
            onChange={(e) => setInput(e.target.value)}
          />
          <Button type="submit" disabled={busy || unavailable || !input.trim()} aria-label="Send">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}

function TurnFooter({ meta }: { meta: ChatResponse }) {
  const flagged = meta.ungrounded_numbers.length > 0 || meta.invalid_citations.length > 0;
  return (
    <div className="mt-2 space-y-1 text-xs text-muted-foreground">
      {flagged && (
        <p className="flex items-center gap-1">
          <AlertTriangle className="h-3.5 w-3.5" style={{ color: "var(--status-warning)" }} aria-hidden />
          Check this answer: {meta.ungrounded_numbers.length} number(s) did not match a source.
        </p>
      )}
      {meta.tools_called.length > 0 && <p>Sources used: {[...new Set(meta.tools_called.map((t) => titleCase(t.name)))].join(", ")}</p>}
    </div>
  );
}
