"use client";

import { TEMPLATE_LIST } from "@/lib/templates";
import { useResumeStore } from "@/store/resumeStore";
import { cn } from "@/lib/utils";
import type { TemplateId } from "@/lib/resumeSchema";
import { ExternalLink } from "lucide-react";

const PREVIEW_COLORS: Record<string, string> = {
  "blue-clean": "#1d4ed8",
  "tech-pro": "#0f172a",
  "ats-friendly": "#000000",
  "modern-bw": "#171717",
  "corporate-minimal": "#2563eb",
};

export function TemplatePicker() {
  const { templateId, setTemplateId } = useResumeStore();
  const active = TEMPLATE_LIST.find((t) => t.id === templateId);

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <p className="section-label">Template</p>
        {active && (
          <a
            href={`/templates/${encodeURIComponent(active.sourcePdf)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] text-[#0071e3] hover:opacity-60 transition-opacity"
          >
            View original <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
        {TEMPLATE_LIST.map((t) => {
          const color = PREVIEW_COLORS[t.id] || "#1d4ed8";
          const isActive = templateId === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTemplateId(t.id as TemplateId)}
              className={cn(
                "shrink-0 w-[100px] rounded-2xl p-3 text-center transition-all duration-300",
                isActive
                  ? "bg-white shadow-[0_4px_24px_rgba(0,0,0,0.1)] ring-2 ring-[#0071e3]/30"
                  : "bg-[#1d1d1f]/[0.03] hover:bg-[#1d1d1f]/[0.06]"
              )}
              aria-pressed={isActive}
              title={t.description}
            >
              <div className="aspect-[3/4] rounded-lg bg-white shadow-sm p-1.5 mb-2 overflow-hidden border border-black/[0.04]">
                <div className="h-1.5 w-6 rounded-sm mx-auto mb-1" style={{ backgroundColor: color }} />
                <div className="h-0.5 w-4 rounded-sm mx-auto mb-2 opacity-30" style={{ backgroundColor: color }} />
                <div className="h-0.5 w-full rounded-sm mb-0.5 bg-black/[0.06]" />
                <div className="h-0.5 w-4/5 rounded-sm mb-0.5 bg-black/[0.06]" />
                <div className="h-0.5 w-full rounded-sm bg-black/[0.04]" />
              </div>
              <p className={cn(
                "text-[11px] font-medium leading-tight",
                isActive ? "text-[#1d1d1f]" : "text-[#6e6e73]"
              )}>
                {t.name}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}