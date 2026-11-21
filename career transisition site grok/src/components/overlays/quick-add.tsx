"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/field";
import { SKILL_CATEGORIES, TARGET_ROLE_NAMES } from "@/lib/constants";
import {
  newContact,
  newEvidence,
  newJob,
  newProject,
  newQuestion,
  newResearch,
  newSkill,
  newStar,
  newTask,
} from "@/lib/factories";
import { useCareerStore } from "@/store/career-store";

const TYPES = ["Skill", "Project", "Job", "Contact", "Evidence", "STAR Story", "Research Topic", "Interview Question", "Task"] as const;

export function QuickAddDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const [type, setType] = useState<(typeof TYPES)[number]>("Skill");
  const store = useCareerStore();
  const [form, setForm] = useState<Record<string, string>>({});
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const save = () => {
    if (type === "Skill") {
      if (!form.name) return toast.error("Name required");
      store.addSkill(newSkill({ name: form.name, category: (form.category as never) || "agents", summary: form.summary ?? "", mappedRoles: form.role ? [form.role] : [] }));
    } else if (type === "Project") {
      if (!form.title) return toast.error("Title required");
      store.addProject(newProject({ title: form.title, category: (form.category as never) || "Agents", useCase: form.summary ?? "", targetRole: form.role || TARGET_ROLE_NAMES[0] }));
    } else if (type === "Job") {
      if (!form.company || !form.role) return toast.error("Company and role required");
      store.addApplication(newJob({ company: form.company, role: form.role, platform: form.platform || "LinkedIn" }));
    } else if (type === "Contact") {
      if (!form.name) return toast.error("Name required");
      store.addContact(newContact({ name: form.name, company: form.company ?? "", designation: form.role ?? "" }));
    } else if (type === "Evidence") {
      if (!form.title) return toast.error("Title required");
      store.addEvidence(newEvidence({ title: form.title, description: form.summary ?? "", url: form.url }));
    } else if (type === "STAR Story") {
      if (!form.title) return toast.error("Title required");
      store.addStarStory(newStar({ title: form.title, situation: form.summary ?? "" }));
    } else if (type === "Research Topic") {
      if (!form.title) return toast.error("Title required");
      store.addResearchTopic(newResearch({ title: form.title, coreConcept: form.summary ?? "" }));
    } else if (type === "Interview Question") {
      if (!form.title) return toast.error("Question required");
      store.addInterviewQuestion(newQuestion({ question: form.title, answer: form.summary ?? "" }));
    } else {
      if (!form.title) return toast.error("Title required");
      store.addTask(newTask({ title: form.title }));
    }
    toast.success(`${type} added`);
    setForm({});
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title="Quick Add" description="Create a record without leaving the current view.">
        <div className="flex flex-wrap gap-1.5">
          {TYPES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setType(t)}
              className={`rounded-md px-2 py-1 text-[12px] ${type === t ? "bg-cyan-500/20 text-cyan-200" : "bg-white/5 text-slate-400"}`}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="mt-4 grid gap-3">
          {type === "Skill" || type === "Project" ? (
            <Field label={type === "Skill" ? "Category" : "Category"}>
              {type === "Skill" ? (
                <Select value={form.category ?? "agents"} onChange={(e) => set("category", e.target.value)}>
                  {SKILL_CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </Select>
              ) : (
                <Select value={form.category ?? "Agents"} onChange={(e) => set("category", e.target.value)}>
                  {["AIOps", "RAG", "Agents", "Security_LLMOps", "FullStack_SaaS"].map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </Select>
              )}
            </Field>
          ) : null}
          <Field label={type === "Job" ? "Company" : type === "Skill" ? "Skill name" : type === "Interview Question" ? "Question" : "Title / Name"}>
            <Input value={form.name ?? form.title ?? form.company ?? ""} onChange={(e) => {
              if (type === "Job") set("company", e.target.value);
              else if (type === "Skill" || type === "Contact") set("name", e.target.value);
              else set("title", e.target.value);
            }} />
          </Field>
          {type === "Job" || type === "Project" || type === "Skill" ? (
            <Field label="Target role">
              <Select value={form.role ?? TARGET_ROLE_NAMES[0]} onChange={(e) => set("role", e.target.value)}>
                {TARGET_ROLE_NAMES.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </Select>
            </Field>
          ) : null}
          {type === "Job" ? (
            <Field label="Platform">
              <Input value={form.platform ?? ""} onChange={(e) => set("platform", e.target.value)} placeholder="LinkedIn, Naukri, Referral…" />
            </Field>
          ) : null}
          {type === "Evidence" ? (
            <Field label="URL">
              <Input value={form.url ?? ""} onChange={(e) => set("url", e.target.value)} />
            </Field>
          ) : null}
          <Field label="Notes / summary">
            <Textarea value={form.summary ?? ""} onChange={(e) => set("summary", e.target.value)} />
          </Field>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={save}>Save</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
