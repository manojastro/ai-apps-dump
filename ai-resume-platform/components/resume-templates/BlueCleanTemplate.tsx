"use client";

import type { ResumeData, TemplateStyleTokens } from "@/lib/resumeSchema";
import { Section, BulletList, formatContact, formatDateRange } from "./shared";

interface Props {
  data: ResumeData;
  style: TemplateStyleTokens;
}

export function BlueCleanTemplate({ data, style }: Props) {
  const { personalInfo } = data;
  const contact = formatContact(personalInfo);

  return (
    <div
      className="p-8 bg-white"
      style={{ fontFamily: style.fontFamily, color: style.textColor, fontSize: style.bodySize }}
    >
      <div className="mb-6">
        <h1
          className="font-bold uppercase tracking-wide"
          style={{ fontSize: style.headingSize, color: style.accentColor }}
        >
          {personalInfo.fullName || "Your Name"}
        </h1>
        {data.targetRole && (
          <p className="font-semibold text-sm mt-1 uppercase" style={{ color: style.textColor }}>
            {data.targetRole}
          </p>
        )}
        {contact && (
          <p className="text-xs mt-2" style={{ color: style.mutedColor }}>{contact}</p>
        )}
      </div>

      {data.summary && (
        <Section title="Summary" style={style} variant="blue">
          <p className="text-sm leading-relaxed">{data.summary}</p>
        </Section>
      )}

      {data.experience.length > 0 && (
        <Section title="Work Experience" style={style} variant="blue">
          {data.experience.map((exp, i) => (
            <div key={i} className="mb-4">
              <div className="flex justify-between items-baseline flex-wrap gap-1">
                <p className="font-semibold text-sm">
                  {exp.role}{exp.company ? `, ${exp.company}` : ""}
                </p>
                <p className="text-xs" style={{ color: style.mutedColor }}>
                  {formatDateRange(exp.startDate, exp.endDate, exp.current)}
                </p>
              </div>
              <BulletList items={exp.bullets} style={style} />
            </div>
          ))}
        </Section>
      )}

      {data.education.length > 0 && (
        <Section title="Education" style={style} variant="blue">
          {data.education.map((edu, i) => (
            <div key={i} className="mb-2">
              <p className="font-semibold text-sm">
                {edu.degree}{edu.field ? ` in ${edu.field}` : ""}
              </p>
              <p className="text-xs" style={{ color: style.mutedColor }}>
                {edu.institution} · {edu.startDate} – {edu.endDate}
              </p>
            </div>
          ))}
        </Section>
      )}

      {(data.skills.technical.length > 0 || data.certifications.length > 0) && (
        <Section title="Additional Information" style={style} variant="blue">
          {data.skills.technical.length > 0 && (
            <p className="text-sm mb-2">
              <span className="font-semibold">Technical Skills: </span>
              {data.skills.technical.join(", ")}
            </p>
          )}
          {data.skills.soft.length > 0 && (
            <p className="text-sm mb-2">
              <span className="font-semibold">Soft Skills: </span>
              {data.skills.soft.join(", ")}
            </p>
          )}
          {data.certifications.map((c, i) => (
            <p key={i} className="text-sm">
              {c.name}{c.issuer ? ` — ${c.issuer}` : ""}
            </p>
          ))}
        </Section>
      )}
    </div>
  );
}