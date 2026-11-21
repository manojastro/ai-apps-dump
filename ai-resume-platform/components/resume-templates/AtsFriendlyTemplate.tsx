"use client";

import type { ResumeData, TemplateStyleTokens } from "@/lib/resumeSchema";
import { Section, BulletList, formatContact, formatDateRange } from "./shared";

interface Props {
  data: ResumeData;
  style: TemplateStyleTokens;
}

export function AtsFriendlyTemplate({ data, style }: Props) {
  const { personalInfo } = data;
  const contact = formatContact(personalInfo);

  return (
    <div
      className="p-8 bg-white"
      style={{ fontFamily: style.fontFamily, color: style.textColor, fontSize: style.bodySize }}
    >
      <div className="text-center mb-5">
        <h1 className="font-bold uppercase" style={{ fontSize: style.headingSize }}>
          {personalInfo.fullName || "Your Name"}
        </h1>
        {data.targetRole && (
          <p className="font-semibold text-sm mt-1">{data.targetRole}</p>
        )}
        {contact && <p className="text-xs mt-2">{contact}</p>}
      </div>

      {data.summary && (
        <Section title="Professional Objective" style={style} variant="ats">
          <p className="text-sm leading-relaxed">{data.summary}</p>
        </Section>
      )}

      {data.experience.length > 0 && (
        <Section title="Professional Experience" style={style} variant="ats">
          {data.experience.map((exp, i) => (
            <div key={i} className="mb-3">
              <p className="font-bold text-sm">{exp.role}</p>
              <p className="text-xs">
                {exp.company}
                {exp.location ? ` | ${exp.location}` : ""} | {formatDateRange(exp.startDate, exp.endDate, exp.current)}
              </p>
              <BulletList items={exp.bullets} style={style} />
            </div>
          ))}
        </Section>
      )}

      {data.education.length > 0 && (
        <Section title="Education" style={style} variant="ats">
          {data.education.map((edu, i) => (
            <div key={i} className="mb-2">
              <p className="font-bold text-sm">
                {edu.degree}{edu.field ? ` in ${edu.field}` : ""}
              </p>
              <p className="text-xs">
                {edu.institution} | {edu.startDate} – {edu.endDate}
              </p>
            </div>
          ))}
        </Section>
      )}

      {(data.skills.technical.length > 0 || data.skills.soft.length > 0) && (
        <Section title="Technical Skills" style={style} variant="ats">
          {data.skills.technical.length > 0 && (
            <p className="text-sm mb-1">
              <span className="font-bold">Core Competencies: </span>
              {data.skills.technical.join(", ")}
            </p>
          )}
          {data.skills.soft.length > 0 && (
            <p className="text-sm">
              <span className="font-bold">Soft Skills: </span>
              {data.skills.soft.join(", ")}
            </p>
          )}
        </Section>
      )}

      {data.certifications.length > 0 && (
        <Section title="Certifications & Additional Information" style={style} variant="ats">
          {data.certifications.map((c, i) => (
            <p key={i} className="text-sm">
              {c.name}{c.issuer ? ` — ${c.issuer}` : ""}{c.date ? ` (${c.date})` : ""}
            </p>
          ))}
        </Section>
      )}
    </div>
  );
}