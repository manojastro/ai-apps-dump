"use client";

import type { ResumeData, TemplateStyleTokens } from "@/lib/resumeSchema";
import { BlueCleanTemplate } from "./BlueCleanTemplate";
import { TechProTemplate } from "./TechProTemplate";
import { AtsFriendlyTemplate } from "./AtsFriendlyTemplate";
import { ModernBwTemplate } from "./ModernBwTemplate";
import { CorporateMinimalTemplate } from "./CorporateMinimalTemplate";

interface TemplateRendererProps {
  data: ResumeData;
  style: TemplateStyleTokens;
}

export function TemplateRenderer({ data, style }: TemplateRendererProps) {
  switch (style.id) {
    case "tech-pro":
      return <TechProTemplate data={data} style={style} />;
    case "ats-friendly":
      return <AtsFriendlyTemplate data={data} style={style} />;
    case "modern-bw":
      return <ModernBwTemplate data={data} style={style} />;
    case "corporate-minimal":
      return <CorporateMinimalTemplate data={data} style={style} />;
    default:
      return <BlueCleanTemplate data={data} style={style} />;
  }
}