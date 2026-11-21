"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Bot, Send, Sparkles } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";

interface Ref { type: string; id: string; label: string }
interface Answer {
  answer: string;
  facts: { text: string; refs: Ref[] }[];
  suggestions: string[];
  proposed_actions: { type: string; target_id: string; label: string; requires_confirmation: boolean }[];
  tool_calls: { tool: string; arguments: Record<string, unknown> }[];
  mode: string;
  disclaimer: string;
}
interface Turn { role: "user" | "assistant"; text: string; answer?: Answer }

const EXAMPLES = [
  "What are the five highest-risk vulnerabilities?",
  "Which critical vulnerabilities affect payment systems?",
  "Why was CVE-2021-44228 assigned a risk score of 100?",
  "Which remediation plans are pending approval?",
  "Show vulnerabilities with confirmed known exploitation.",
  "Which findings were verified as resolved this week?",
];

function refHref(ref: Ref): string {
  switch (ref.type) {
    case "finding": return `/vulnerabilities?finding=${ref.id}`;
    case "plan": return `/remediation/${ref.id}`;
    case "approval": return `/approvals?focus=${ref.id}`;
    case "vulnerability": return `/vulnerabilities?cve=${ref.id}`;
    case "workflow": return `/investigations/${ref.id}`;
    default: return "#";
  }
}

export function AssistantPanel({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const params = useParams<{ id?: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const qc = useQueryClient();
  const bottom = useRef<HTMLDivElement>(null);

  const context: Record<string, string> = {};
  if (pathname.startsWith("/remediation/") && params.id) context.plan_id = params.id;

  const ask = useMutation({
    mutationFn: (message: string) => api.post<Answer>("/assistant/chat", { message, context }),
    onSuccess: (answer) => {
      setTurns((t) => [...t, { role: "assistant", text: answer.answer, answer }]);
      setTimeout(() => bottom.current?.scrollIntoView({ behavior: "smooth" }), 50);
    },
    onError: (e: Error) => setTurns((t) => [...t, { role: "assistant", text: `Error: ${e.message}` }]),
  });

  const startInvestigation = useMutation({
    mutationFn: (findingId: string) => api.post<{ workflow_run_id: string }>(`/findings/${findingId}/investigate`),
    onSuccess: (r) => {
      toast.success("Investigation started");
      qc.invalidateQueries();
      onOpenChange(false);
      router.push(`/investigations/${r.workflow_run_id}`);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const send = (text: string) => {
    const message = text.trim();
    if (!message || ask.isPending) return;
    setTurns((t) => [...t, { role: "user", text: message }]);
    setInput("");
    ask.mutate(message);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex w-full flex-col gap-0 p-0 sm:max-w-lg">
        <SheetHeader className="border-b px-4 py-3">
          <SheetTitle className="flex items-center gap-2"><Sparkles className="size-4 text-primary" /> Ask Aegis</SheetTitle>
          <SheetDescription className="text-xs">
            Answers come only from platform data via read-only tools, with your permissions. State changes are proposed, never executed.
          </SheetDescription>
        </SheetHeader>
        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-4 p-4">
            {turns.length === 0 && (
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">Try one of these:</p>
                {EXAMPLES.map((e) => (
                  <button key={e} onClick={() => send(e)} className="block w-full rounded-md border px-3 py-2 text-left text-sm hover:bg-muted">
                    {e}
                  </button>
                ))}
              </div>
            )}
            {turns.map((t, i) =>
              t.role === "user" ? (
                <div key={i} className="ml-8 rounded-lg bg-primary/10 px-3 py-2 text-sm">{t.text}</div>
              ) : (
                <div key={i} className="mr-4 space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <Bot className="mt-0.5 size-4 shrink-0 text-primary" />
                    <p>{t.text}</p>
                  </div>
                  {t.answer && t.answer.facts.length > 0 && (
                    <ul className="ml-6 space-y-1.5">
                      {t.answer.facts.map((f, j) => (
                        <li key={j} className="rounded-md border bg-card px-2.5 py-1.5 text-xs">
                          <span className="mr-1 rounded bg-muted px-1 text-[9px] font-semibold uppercase text-muted-foreground">fact</span>
                          {f.text}
                          {f.refs.map((r) => (
                            <Link key={`${r.type}${r.id}`} href={refHref(r)} onClick={() => onOpenChange(false)} className="ml-1.5 text-primary underline-offset-2 hover:underline">
                              [{r.type}]
                            </Link>
                          ))}
                        </li>
                      ))}
                    </ul>
                  )}
                  {t.answer?.suggestions.map((s, j) => (
                    <p key={j} className="ml-6 text-xs text-muted-foreground">
                      <span className="mr-1 rounded bg-muted px-1 text-[9px] font-semibold uppercase">suggestion</span>{s}
                    </p>
                  ))}
                  {t.answer?.proposed_actions.map((a) =>
                    a.type === "start_investigation" ? (
                      <Button key={a.target_id} size="sm" className="ml-6" disabled={startInvestigation.isPending}
                        onClick={() => window.confirm(`${a.label}? This starts a multi-agent investigation; any resulting plan still needs human approval.`) && startInvestigation.mutate(a.target_id)}>
                        {a.label}
                      </Button>
                    ) : a.type === "open_finding" ? (
                      <Button key={a.target_id} size="sm" variant="outline" className="ml-6" asChild>
                        <Link href={`/vulnerabilities?finding=${a.target_id}`} onClick={() => onOpenChange(false)}>{a.label}</Link>
                      </Button>
                    ) : null,
                  )}
                  {t.answer && t.answer.tool_calls.length > 0 && (
                    <p className="ml-6 font-mono text-[10px] text-muted-foreground">
                      tools: {t.answer.tool_calls.map((c) => c.tool).join(", ")} · mode {t.answer.mode}
                    </p>
                  )}
                </div>
              ),
            )}
            {ask.isPending && <p className="ml-6 animate-pulse text-xs text-muted-foreground">Querying platform tools…</p>}
            <div ref={bottom} />
          </div>
        </ScrollArea>
        <form className="flex gap-2 border-t p-3" onSubmit={(e) => { e.preventDefault(); send(input); }}>
          <Textarea value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about findings, risk, approvals…" rows={2} maxLength={2000}
            className="min-h-0 resize-none text-sm" onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }} />
          <Button type="submit" size="icon" disabled={!input.trim() || ask.isPending} aria-label="Send"><Send /></Button>
        </form>
      </SheetContent>
    </Sheet>
  );
}
