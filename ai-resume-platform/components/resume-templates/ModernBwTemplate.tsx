"use client";

import type { ResumeData, TemplateStyleTokens } from "@/lib/resumeSchema";
import { Section, BulletList, formatContact, formatDateRange } from "./shared";

interface Props {
  data: ResumeData;
  style: TemplateStyleTokens;
}

export function ModernBwTemplate({ data, style }: Props) {
  const { personalInfo } = data;
  const contact = formatContact(personalInfo, "  |  ");

  return (
    <div
      className="p-8 bg-white"
      style={{ fontFamily: style.fontFamily, color: style.textColor, fontSize: style.bodySize }}
    >
      <div className="text-center border-b border-black pb-4 mb-6">
        <h1 className="font-bold tracking-wider uppercase" style={{ fontSize: style.headingSize }}>
          {personalInfo.fullName || "Your Name"}
        </h1>
        {data.targetRole && (
          <p className="text-sm font-medium mt-1 tracking-wide uppercase">{data.targetRole}</p>
        )}
        {contact && <p className="text-xs mt-2">{contact}</p>}
      </div>

      {data.summary && (
        <p className="text-sm leading-relaxed mb-6 text-center italic">{data.summary}</p>
      )}

      {data.experience.length > 0 && (
        <Section title="Professional Experience" style={style} variant="bw">
          {data.experience.map((exp, i) => (
            <div key={i} className="mb-4">
              <div className="flex justify-between items-baseline">
                <p className="font-bold text-sm">{exp.role} — {exp.company}</p>
                <p className="text-xs">
                  {formatDateRange(exp.startDate, exp.endDate, exp.current)}
                </p>
              </div>
              {exp.location && <p className="text-xs italic">{exp.location}</p>}
              <BulletList items={exp.bullets} style={style} />
            </div>
          ))}
        </Section>
      )}

      {data.education.length > 0 && (
        <Section title="Education" style={style} variant="bw">
          {data.education.map((edu, i) => (
            <div key={i} className="mb-2">
              <p className="font-bold text-sm">
                {edu.degree}{edu.field ? ` in ${edu.field}` : ""}
              </p>
              <p className="text-xs">{edu.institution} · {edu.startDate} – {edu.endDate}</p>
            </div>
          ))}
        </Section>
      )}

      {(data.skills.technical.length > 0 || data.certifications.length > 0 || data.projects.length > 0) && (
        <Section title="Additional Information" style={style} variant="bw">
          {data.skills.technical.length > 0 && (
            <p className="text-sm mb-1">
              <span className="font-bold">Skills: </span>
              {[...data.skills.technical, ...data.skills.soft].join(", ")}
            </p>
          )}
          {data.certifications.map((c, i) => (
            <p key={i} className="text-sm">
              Certifications: {c.name}
            </p>
          ))}
          {data.projects.map((p, i) => (
            <p key={i} className="text-sm">{p.name}: {p.description}</p>
          ))}
        </Section>
      )}
    </div>
  );
}