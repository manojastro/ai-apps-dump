"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/field";
import { SectionHeader } from "@/components/shared/empty-state";
import { newQuestion, newResearch, newSkill, newTask } from "@/lib/factories";
import { createId, timestamps } from "@/lib/ids";
import { active } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";


export default function ResearchPage() {
  const state = useCareerStore((s) => s.state);
  const add = useCareerStore((s) => s.addResearchTopic);
  const update = useCareerStore((s) => s.updateResearchTopic);
  const addSource = useCareerStore((s) => s.addResearchSource);
  const addSkill = useCareerStore((s) => s.addSkill);
  const addTask = useCareerStore((s) => s.addTask);
  const addQ = useCareerStore((s) => s.addInterviewQuestion);
  const topics = active(state.researchTopics);
  const [id, setId] = useState(topics[0]?.id);
  const t = topics.find((x) => x.id === id) ?? topics[0];
  const sources = t ? state.researchSources.filter((s) => s.researchTopicId === t.id && !s.archivedAt) : [];

  return (
    <div>
      <SectionHeader
        title="Research Lab"
        description="Concepts, math, trade-offs, talking points. Convert notes into skills, tasks, and questions."
        actions={<Button onClick={() => add(newResearch({ title: "New topic" }))}>Add topic</Button>}
      />
      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <aside className="card p-2">
          {topics.map((topic) => (
            <button key={topic.id} type="button" onClick={() => setId(topic.id)} className={`block w-full rounded-md px-2 py-2 text-left text-[13px] ${topic.id === t?.id ? "bg-white/10" : "text-slate-400"}`}>
              {topic.title} {topic.isMastered ? "✓" : ""}
            </button>
          ))}
        </aside>
        {t ? (
          <div className="space-y-3">
            <Field label="Title"><Input value={t.title} onChange={(e) => update({ ...t, title: e.target.value })} /></Field>
            <Field label="Core concept"><Textarea value={t.coreConcept} onChange={(e) => update({ ...t, coreConcept: e.target.value })} /></Field>
            <Field label="Math / formula"><Textarea value={t.mathOrFormula} onChange={(e) => update({ ...t, mathOrFormula: e.target.value })} /></Field>
            <Field label="Trade-offs"><Textarea value={t.tradeOffs} onChange={(e) => update({ ...t, tradeOffs: e.target.value })} /></Field>
            <Field label="Interview talking points"><Textarea value={t.interviewTalkingPoints} onChange={(e) => update({ ...t, interviewTalkingPoints: e.target.value })} /></Field>
            <label className="flex items-center gap-2 text-[13px]">
              <input type="checkbox" checked={t.isMastered} onChange={(e) => update({ ...t, isMastered: e.target.checked })} />
              Mastered
            </label>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline" onClick={() => addSkill(newSkill({ name: t.title, summary: t.coreConcept }))}>→ Skill</Button>
              <Button size="sm" variant="outline" onClick={() => addTask(newTask({ title: `Apply research: ${t.title}`, category: "Research" }))}>→ Task</Button>
              <Button size="sm" variant="outline" onClick={() => addQ(newQuestion({ question: `Explain ${t.title}`, answer: t.interviewTalkingPoints }))}>→ Interview Q</Button>
            </div>
            <section className="card p-3">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold">Sources</h3>
                <Button size="sm" variant="outline" onClick={() => addSource({ id: createId("src"), ...timestamps(), researchTopicId: t.id, title: "Source", sourceType: "Article", credibility: "Community", takeaway: "" })}>
                  Add source
                </Button>
              </div>
              {sources.map((s) => (
                <p key={s.id} className="text-[13px] text-slate-300">
                  {s.title} <Badge>{s.credibility}</Badge>
                </p>
              ))}
            </section>
          </div>
        ) : <p className="text-slate-500">Add a research topic.</p>}
      </div>
    </div>
  );
}
