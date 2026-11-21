"use client";

import type { ResumeData, TemplateStyleTokens } from "@/lib/resumeSchema";
import { Section, BulletList, formatContact, formatDateRange } from "./shared";

interface Props {
  data: ResumeData;
  style: TemplateStyleTokens;
}

export function TechProTemplate({ data, style }: Props) {
  const { personalInfo } = data;
  const contact = formatContact(personalInfo, "  ·  ");

  return (
    <div
      className="p-8 bg-white"
      style={{ fontFamily: style.fontFamily, color: style.textColor, fontSize: style.bodySize }}
    >
      <div className="border-b-2 border-[#0f172a] pb-4 mb-6">
        <h1 className="font-black tracking-tight" style={{ fontSize: "2rem" }}>
          {personalInfo.fullName || "Your Name"}
        </h1>
        {data.targetRole && (
          <p className="font-medium text-base mt-1" style={{ color: style.mutedColor }}>
            {data.targetRole}
          </p>
        )}
        {contact && <p className="text-xs mt-2 font-mono" style={{ color: style.mutedColor }}>{contact}</p>}
      </div>

      {data.summary && (
        <p className="text-sm leading-relaxed mb-6" style={{ color: style.mutedColor }}>
          {data.summary}
        </p>
      )}

      {data.experience.length > 0 && (
        <Section title="Experience" style={style} variant="tech">
          {data.experience.map((exp, i) => (
            <div key={i} className="mb-4">
              <p className="font-bold text-sm">{exp.role}</p>
              <p className="text-xs font-medium" style={{ color: style.mutedColor }}>
                {exp.company} · {formatDateRange(exp.startDate, exp.endDate, exp.current)}
              </p>
              <BulletList items={exp.bullets} style={style} />
            </div>
          ))}
        </Section>
      )}

      {data.education.length > 0 && (
        <Section title="Education" style={style} variant="tech">
          {data.education.map((edu, i) => (
            <div key={i} className="mb-2">
              <p className="font-bold text-sm">{edu.degree}</p>
              <p className="text-xs" style={{ color: style.mutedColor }}>
                {edu.institution} · {edu.startDate} – {edu.endDate}
              </p>
            </div>
          ))}
        </Section>
      )}

      {(data.skills.technical.length > 0 || data.skills.soft.length > 0) && (
        <div className="mt-4 p-3 bg-[#f8fafc] rounded">
          <p className="text-xs font-bold uppercase mb-1">Skills</p>
          <p className="text-sm font-mono">
            {[...data.skills.technical, ...data.skills.soft].join(" · ")}
          </p>
        </div>
      )}
    </div>
  );
}