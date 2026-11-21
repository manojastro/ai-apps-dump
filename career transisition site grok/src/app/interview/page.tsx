"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { SectionHeader } from "@/components/shared/empty-state";
import { newQuestion, newStar, nextReviewForConfidence } from "@/lib/factories";
import { textDepth } from "@/lib/evidence";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";
import type { StarStory } from "@/types/career";

const CATS = ["Python", "LLM", "RAG", "Agents", "System Design", "Cloud", "MLOps", "Behavioral", "Backend", "Security", "Observability", "Evaluation"] as const;

export default function InterviewPage() {
  const state = useCareerStore((s) => s.state);
  const addQ = useCareerStore((s) => s.addInterviewQuestion);
  const updateQ = useCareerStore((s) => s.updateInterviewQuestion);
  const addStar = useCareerStore((s) => s.addStarStory);
  const updateStar = useCareerStore((s) => s.updateStarStory);
  const saveNarrative = useCareerStore((s) => s.saveNarrative);
  const [tab, setTab] = useState<"bank" | "practice" | "star" | "narrative">("bank");
  const questions = active(state.interviewQuestions);
  const heatmap = useMemo(() => {
    return CATS.map((c) => {
      const qs = questions.filter((q) => q.category === c);
      const avg = qs.length ? qs.reduce((s, q) => s + q.confidence, 0) / qs.length : 0;
      return { c, avg, n: qs.length };
    });
  }, [questions]);

  const [practiceId, setPracticeId] = useState<string | null>(questions[0]?.id ?? null);
  const [reveal, setReveal] = useState(false);
  const [rating, setRating] = useState<1 | 2 | 3 | 4 | 5>(3);
  const current = questions.find((q) => q.id === practiceId);
  const narrative = active(state.transitionNarratives)[0];

  return (
    <div>
      <SectionHeader title="Interview Prep" description="Practice loops beat static question lists. Weak areas return sooner." />
      <div className="mb-4 flex flex-wrap gap-1">
        {(["bank", "practice", "star", "narrative"] as const).map((t) => (
          <button key={t} type="button" onClick={() => setTab(t)} className={`rounded-md px-3 py-1.5 text-[13px] ${tab === t ? "bg-white/10" : "text-slate-400"}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === "bank" ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            {heatmap.map((h) => (
              <div key={h.c} className="card p-3">
                <p className="text-[12px] text-slate-400">{h.c}</p>
                <p className="tabular text-lg">{h.avg ? h.avg.toFixed(1) : "—"}</p>
                <p className="text-[11px] text-slate-500">{h.n} questions</p>
              </div>
            ))}
          </div>
          <Button size="sm" onClick={() => addQ(newQuestion({ question: "New question" }))}>Add question</Button>
          <div className="space-y-2">
            {questions.map((q) => (
              <div key={q.id} className="card p-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[13px] font-medium">{q.question}</p>
                  <Badge>{q.category}</Badge>
                </div>
                <p className="mt-1 text-[12px] text-slate-400">Confidence {q.confidence}/5 {q.mastered ? "· mastered" : ""}</p>
                <Button size="sm" variant="ghost" onClick={() => { setPracticeId(q.id); setTab("practice"); setReveal(false); }}>Practice</Button>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {tab === "practice" && current ? (
        <div className="card max-w-2xl p-5">
          <p className="text-[12px] text-slate-500">{current.category}</p>
          <h2 className="mt-1 text-base font-semibold">{current.question}</h2>
          {!reveal ? (
            <Button className="mt-4" onClick={() => setReveal(true)}>Reveal stored answer</Button>
          ) : (
            <p className="mt-4 whitespace-pre-wrap text-[13px] text-slate-300">{current.answer || "No stored answer yet."}</p>
          )}
          {reveal ? (
            <div className="mt-4 space-y-3">
              <Field label="Self-rate 1–5">
                <Select value={String(rating)} onChange={(e) => setRating(Number(e.target.value) as 1 | 2 | 3 | 4 | 5)}>
                  {[1, 2, 3, 4, 5].map((n) => <option key={n}>{n}</option>)}
                </Select>
              </Field>
              <Button
                onClick={() => {
                  updateQ({
                    ...current,
                    confidence: rating,
                    lastPracticed: new Date().toISOString(),
                    nextReviewDate: nextReviewForConfidence(rating),
                    mastered: rating >= 5,
                  });
                  const next = questions.find((q) => q.id !== current.id && (q.confidence <= 3 || !q.lastPracticed)) ?? questions.find((q) => q.id !== current.id);
                  setPracticeId(next?.id ?? current.id);
                  setReveal(false);
                }}
              >
                Record session
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}

      {tab === "star" ? (
        <StarPanel stories={active(state.starStories)} onAdd={() => addStar(newStar({ title: "New STAR" }))} onChange={updateStar} />
      ) : null}

      {tab === "narrative" ? (
        <div className="grid gap-3">
          <p className="text-[13px] text-slate-400">30s intro, 90s transition story, why AI, why now, why senior, how 8.5 years of operations strengthens AI engineering.</p>
          {(["intro30s", "story90s", "whyAI", "whyNow", "whySenior", "howOpsStrengthens"] as const).map((k) => (
            <Field key={k} label={k}>
              <Textarea
                value={narrative?.[k] ?? ""}
                onChange={(e) =>
                  saveNarrative({
                    id: narrative?.id ?? crypto.randomUUID(),
                    createdAt: narrative?.createdAt ?? new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                    intro30s: narrative?.intro30s ?? "",
                    story90s: narrative?.story90s ?? "",
                    whyAI: narrative?.whyAI ?? "",
                    whyNow: narrative?.whyNow ?? "",
                    whySenior: narrative?.whySenior ?? "",
                    howOpsStrengthens: narrative?.howOpsStrengthens ?? "",
                    evidenceIds: narrative?.evidenceIds ?? [],
                    [k]: e.target.value,
                  })
                }
              />
            </Field>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function StarPanel({
  stories,
  onAdd,
  onChange,
}: {
  stories: StarStory[];
  onAdd: () => void;
  onChange: (s: StarStory) => void;
}) {
  const [id, setId] = useState(stories[0]?.id);
  const s = stories.find((x) => x.id === id) ?? stories[0];
  return (
    <div>
      <div className="mb-3 flex gap-2">
        <Button size="sm" onClick={onAdd}>Add STAR</Button>
        {stories.map((st) => (
          <button key={st.id} type="button" className="rounded-md bg-white/5 px-2 py-1 text-[12px]" onClick={() => setId(st.id)}>
            {st.title || "Untitled"}
          </button>
        ))}
      </div>
      {s ? (
        <div className="grid gap-3">
          <Field label="Title"><Input value={s.title} onChange={(e) => onChange({ ...s, title: e.target.value })} /></Field>
          <Field label="Category">
            <Select value={s.category} onChange={(e) => onChange({ ...s, category: e.target.value as StarStory["category"] })}>
              {["Outage/RCA", "System Architecture", "Automation Impact", "Conflict/Governance", "LLM Trade-Offs"].map((c) => <option key={c}>{c}</option>)}
            </Select>
          </Field>
          {(["situation", "task", "action", "result", "techNotes"] as const).map((k) => (
            <Field key={k} label={k}>
              <Textarea value={s[k]} onChange={(e) => onChange({ ...s, [k]: e.target.value })} />
            </Field>
          ))}
          <p className="text-[13px] text-slate-400">
            Completeness {Math.round(([s.situation, s.task, s.action, s.result].filter((x) => textDepth(x) >= 0.4).length / 4) * 100)}%
            {/\d/.test(s.result) ? "" : " · Quantification Missing"}
          </p>
        </div>
      ) : null}
    </div>
  );
}
