import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  BorderStyle,
} from "docx";
import type { ResumeData } from "./resumeSchema";
import type { TemplateStyleTokens } from "./resumeSchema";

function sectionHeading(text: string, style: TemplateStyleTokens): Paragraph {
  const useBorder = style.layout === "ats" || style.layout === "centered";
  return new Paragraph({
    spacing: { before: 240, after: 120 },
    border: useBorder
      ? { bottom: { style: BorderStyle.SINGLE, size: 1, color: "000000" } }
      : undefined,
    children: [
      new TextRun({
        text: text.toUpperCase(),
        bold: true,
        size: useBorder ? 22 : 24,
        color: style.accentColor.replace("#", ""),
        font: style.headingFontFamily.split(",")[0].replace(/'/g, ""),
      }),
    ],
  });
}

function bulletParagraph(text: string, style: TemplateStyleTokens): Paragraph {
  const bullet = style.bulletStyle === "dash" ? "– " : "• ";
  return new Paragraph({
    spacing: { after: 60 },
    indent: { left: 360 },
    children: [
      new TextRun({
        text: `${bullet}${text}`,
        size: 20,
        font: style.fontFamily.split(",")[0].replace(/'/g, ""),
      }),
    ],
  });
}

function bodyText(text: string, style: TemplateStyleTokens, bold = false): Paragraph {
  return new Paragraph({
    spacing: { after: 80 },
    children: [
      new TextRun({
        text,
        bold,
        size: 20,
        font: style.fontFamily.split(",")[0].replace(/'/g, ""),
      }),
    ],
  });
}

export async function generateDocx(
  data: ResumeData,
  style: TemplateStyleTokens
): Promise<Buffer> {
  const { personalInfo } = data;
  const children: Paragraph[] = [];

  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 80 },
      children: [
        new TextRun({
          text: personalInfo.fullName || "Resume",
          bold: true,
          size: 36,
          color: style.accentColor.replace("#", ""),
          font: style.headingFontFamily.split(",")[0].replace(/'/g, ""),
        }),
      ],
    })
  );

  if (data.targetRole) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [
          new TextRun({
            text: data.targetRole,
            size: 22,
            italics: style.layout === "centered",
            color: style.mutedColor.replace("#", ""),
          }),
        ],
      })
    );
  }

  const contactParts = [
    personalInfo.email,
    personalInfo.phone,
    personalInfo.location,
    personalInfo.linkedin,
    personalInfo.portfolio,
  ].filter(Boolean);

  if (contactParts.length > 0) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [
          new TextRun({
            text: contactParts.join("  |  "),
            size: 18,
            color: style.mutedColor.replace("#", ""),
          }),
        ],
      })
    );
  }

  if (data.summary) {
    children.push(sectionHeading("Professional Summary", style));
    children.push(bodyText(data.summary, style));
  }

  if (data.experience.length > 0) {
    children.push(sectionHeading("Experience", style));
    for (const exp of data.experience) {
      const dateRange = exp.current
        ? `${exp.startDate} – Present`
        : `${exp.startDate} – ${exp.endDate}`;
      children.push(
        bodyText(`${exp.role} — ${exp.company}`, style, true)
      );
      children.push(
        bodyText(`${dateRange}${exp.location ? `  |  ${exp.location}` : ""}`, style)
      );
      for (const bullet of exp.bullets) {
        if (bullet.trim()) children.push(bulletParagraph(bullet, style));
      }
    }
  }

  if (data.education.length > 0) {
    children.push(sectionHeading("Education", style));
    for (const edu of data.education) {
      children.push(
        bodyText(
          `${edu.degree}${edu.field ? ` in ${edu.field}` : ""} — ${edu.institution}`,
          style,
          true
        )
      );
      children.push(
        bodyText(`${edu.startDate} – ${edu.endDate}`, style)
      );
    }
  }

  const allSkills = [
    ...data.skills.technical,
    ...data.skills.soft,
  ].filter(Boolean);
  if (allSkills.length > 0) {
    children.push(sectionHeading("Skills", style));
    children.push(bodyText(allSkills.join("  •  "), style));
  }

  if (data.certifications.length > 0) {
    children.push(sectionHeading("Certifications", style));
    for (const cert of data.certifications) {
      children.push(
        bodyText(
          `${cert.name}${cert.issuer ? ` — ${cert.issuer}` : ""}${cert.date ? ` (${cert.date})` : ""}`,
          style
        )
      );
    }
  }

  if (data.projects.length > 0) {
    children.push(sectionHeading("Projects", style));
    for (const proj of data.projects) {
      children.push(bodyText(proj.name, style, true));
      if (proj.description) children.push(bodyText(proj.description, style));
      if (proj.tech.length > 0) {
        children.push(bodyText(`Tech: ${proj.tech.join(", ")}`, style));
      }
    }
  }

  const doc = new Document({
    sections: [{ properties: {}, children }],
  });

  return Buffer.from(await Packer.toBuffer(doc));
}