"use client";

import type { ResumeData, TemplateStyleTokens } from "@/lib/resumeSchema";
import { Section, BulletList, formatContact, formatDateRange } from "./shared";

interface Props {
  data: ResumeData;
  style: TemplateStyleTokens;
}

export function CorporateMinimalTemplate({ data, style }: Props) {
  const { personalInfo } = data;
  const contact = formatContact(personalInfo, " | ");

  return (
    <div
      className="p-10 bg-white"
      style={{ fontFamily: style.fontFamily, color: style.textColor, fontSize: style.bodySize }}
    >
      <div className="mb-10">
        <h1
          className="font-semibold tracking-tight"
          style={{ fontSize: "1.75rem", color: style.accentColor }}
        >
          {personalInfo.fullName || "Your Name"}
        </h1>
        {data.targetRole && (
          <p className="text-base mt-1 font-medium">{data.targetRole}</p>
        )}
        {contact && (
          <p className="text-xs mt-3" style={{ color: style.mutedColor }}>{contact}</p>
        )}
      </div>

      {data.summary && (
        <Section title="Summary" style={style} variant="minimal">
          <p className="text-sm leading-loose font-light" style={{ color: style.mutedColor }}>
            {data.summary}
          </p>
        </Section>
      )}

      {data.experience.length > 0 && (
        <Section title="Work Experience" style={style} variant="minimal">
          {data.experience.map((exp, i) => (
            <div key={i} className="mb-6">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium text-sm">{exp.role}</p>
                  <p className="text-xs" style={{ color: style.mutedColor }}>{exp.company}</p>
                </div>
                <p className="text-xs whitespace-nowrap ml-4" style={{ color: style.mutedColor }}>
                  {formatDateRange(exp.startDate, exp.endDate, exp.current)}
                </p>
              </div>
              <BulletList items={exp.bullets} style={style} />
            </div>
          ))}
        </Section>
      )}

      {data.education.length > 0 && (
        <Section title="Education" style={style} variant="minimal">
          {data.education.map((edu, i) => (
            <div key={i} className="mb-3">
              <p className="text-sm">{edu.degree}{edu.field ? `, ${edu.field}` : ""}</p>
              <p className="text-xs" style={{ color: style.mutedColor }}>
                {edu.institution} · {edu.startDate} – {edu.endDate}
              </p>
            </div>
          ))}
        </Section>
      )}

      {(data.skills.technical.length > 0 || data.skills.soft.length > 0) && (
        <Section title="Skills" style={style} variant="minimal">
          <p className="text-sm font-light" style={{ color: style.mutedColor }}>
            {[...data.skills.technical, ...data.skills.soft].join(" · ")}
          </p>
        </Section>
      )}
    </div>
  );
}