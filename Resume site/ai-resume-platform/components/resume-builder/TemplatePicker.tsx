"use client";

import { TEMPLATE_LIST } from "@/lib/templates";
import { useResumeStore } from "@/store/resumeStore";
import { cn } from "@/lib/utils";
import type { TemplateId } from "@/lib/resumeSchema";

const PREVIEW_COLORS: Record<string, string> = {
  "blue-clean": "#1d4ed8",
  "tech-pro": "#0f172a",
  "ats-friendly": "#000000",
  "modern-bw": "#171717",
  "corporate-minimal": "#2563eb",
};

export function TemplatePicker() {
  const { templateId, setTemplateId } = useResumeStore();

  return (
    <div>
      <p className="section-label mb-3">Template</p>
      <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-2">
        {TEMPLATE_LIST.map((t) => {
          const color = PREVIEW_COLORS[t.id] || "#1d4ed8";
          const isActive = templateId === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTemplateId(t.id as TemplateId)}
              className={cn(
                "w-[92px] shrink-0 rounded-2xl p-2.5 text-center transition-colors duration-200 focus-ring",
                isActive
                  ? "bg-white shadow-[0_4px_20px_rgba(0,0,0,0.08)] ring-2 ring-[#0071e3]/30"
                  : "bg-[#1d1d1f]/[0.03] hover:bg-[#1d1d1f]/[0.06]"
              )}
              aria-pressed={isActive}
              title={t.description}
            >
              <div className="mb-2 aspect-[3/4] overflow-hidden rounded-lg border border-black/[0.04] bg-white p-1.5 shadow-sm">
                <div
                  className="mx-auto mb-1 h-1.5 w-6 rounded-sm"
                  style={{ backgroundColor: color }}
                />
                <div
                  className="mx-auto mb-2 h-0.5 w-4 rounded-sm opacity-30"
                  style={{ backgroundColor: color }}
                />
                <div className="mb-0.5 h-0.5 w-full rounded-sm bg-black/[0.06]" />
                <div className="mb-0.5 h-0.5 w-4/5 rounded-sm bg-black/[0.06]" />
                <div className="h-0.5 w-full rounded-sm bg-black/[0.04]" />
              </div>
              <p
                className={cn(
                  "text-[11px] font-medium leading-tight",
                  isActive ? "text-[#1d1d1f]" : "text-[#6e6e73]"
                )}
              >
                {t.name}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
