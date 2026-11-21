"use client";

import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { searchState } from "@/lib/search";
import { prettyState } from "@/lib/storage";
import { downloadText } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";

export function useCommandPalette() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return { open, setOpen };
}

export function CommandPalette({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const router = useRouter();
  const state = useCareerStore((s) => s.state);
  const [q, setQ] = useState("");
  const hits = useMemo(() => searchState(state, q), [state, q]);

  const go = (href: string) => {
    onOpenChange(false);
    router.push(href);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 p-4 backdrop-blur-sm" onClick={() => onOpenChange(false)}>
      <Command
        className="card mx-auto mt-[14vh] w-full max-w-xl overflow-hidden shadow-[0_24px_80px_rgb(0_0_0_/_0.45)]"
        onClick={(e) => e.stopPropagation()}
        label="Command palette"
      >
        <Command.Input
          value={q}
          onValueChange={setQ}
          placeholder="Search the OS or run a command…"
          className="h-12 w-full border-b border-white/10 bg-transparent px-4 text-[14px] outline-none"
        />
        <Command.List className="max-h-80 overflow-y-auto p-2 scrollbar-thin">
          <Command.Empty className="px-3 py-6 text-[13px] text-slate-500">No results.</Command.Empty>
          <Command.Group heading="Commands" className="px-1 text-[10px] tracking-[0.14em] text-slate-500 uppercase">
            <Item onSelect={() => go("/today")}>Open Today's Priorities</Item>
            <Item onSelect={() => go("/jobs")}>Open Active Applications</Item>
            <Item
              onSelect={() => {
                downloadText(`ai-career-os-${new Date().toISOString().slice(0, 10)}.json`, prettyState(state));
                onOpenChange(false);
              }}
            >
              Export State
            </Item>
            <Item onSelect={() => go("/skills")}>Add Skill</Item>
            <Item onSelect={() => go("/projects")}>Add Project</Item>
            <Item onSelect={() => go("/jobs")}>Add Job</Item>
            <Item onSelect={() => go("/network")}>Add Contact</Item>
            <Item onSelect={() => go("/evidence")}>Add Evidence</Item>
            <Item onSelect={() => go("/interview")}>Add STAR Story</Item>
            <Item onSelect={() => go("/research")}>Add Research Topic</Item>
            <Item onSelect={() => go("/interview")}>Add Interview Question</Item>
            <Item onSelect={() => go("/execution")}>Add Task</Item>
          </Command.Group>
          {hits.length > 0 ? (
            <Command.Group heading="Search" className="px-1 text-[10px] tracking-[0.14em] text-slate-500 uppercase">
              {hits.map((h) => (
                <Item key={`${h.entity}-${h.id}`} onSelect={() => go(h.href)}>
                  <span className="w-16 shrink-0 text-[11px] tracking-wide text-slate-500 uppercase">{h.entity}</span>
                  {h.title}
                </Item>
              ))}
            </Command.Group>
          ) : null}
        </Command.List>
      </Command>
    </div>
  );
}

function Item({ children, onSelect }: { children: import("react").ReactNode; onSelect: () => void }) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-[13px] text-slate-200 data-[selected=true]:bg-cyan-400/10 data-[selected=true]:text-white"
    >
      {children}
    </Command.Item>
  );
}
