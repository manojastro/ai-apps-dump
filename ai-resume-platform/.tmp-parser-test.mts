import fs from "node:fs";
import path from "node:path";
import { extractPdfText } from "./lib/pdfParse.ts";
import {
  parseUploadedText,
  looksLikeResumeText,
} from "./lib/resumeParser.ts";

const files = [
  "Best 1.pdf",
  "Best%202.pdf",
  "Black and White Minimalist Accountant Resume.pdf",
  "Black and White Simple Infographic Resume.pdf",
  "Black White Corporate Finance Resume.pdf",
  "public/templates/Black and White Modern Professional Resume (1).pdf",
  "public/templates/Black and White Professional ATS Friendly Resume.pdf",
  "public/templates/White and Black Tech Professional Resume (1).pdf",
];

for (const rel of files) {
  const file = path.resolve(rel);
  if (!fs.existsSync(file)) {
    console.log(`MISSING ${rel}`);
    continue;
  }
  const buffer = fs.readFileSync(file);
  const text = await extractPdfText(buffer);
  const parsed = parseUploadedText(text);
  const r = parsed.resume;
  console.log(`\n=== ${rel}`);
  console.log(
    JSON.stringify({
      looksLikeResume: parsed.looksLikeResume,
      detected: parsed.detectedSections,
      personal: r.personal,
      summaryLength: r.summary.length,
      experience: r.experience.map((e) => ({
        company: e.company,
        role: e.role,
        start: e.startDate,
        end: e.endDate,
        achievements: e.achievements.length,
      })),
      education: r.education,
      skills: r.skills,
      projects: r.projects.map((p) => ({
        name: p.name,
        tech: p.tech,
        achievements: p.achievements.length,
        description: p.description.slice(0, 80),
      })),
      certifications: r.certifications,
      awards: r.awards,
      additional: r.additionalSections,
    })
  );
  const out = path.resolve(
    "C:/Users/manoj/AppData/Local/Temp/opencode",
    `${path.basename(rel, ".pdf").replace(/[^a-z0-9]+/gi, "-")}.json`
  );
  fs.writeFileSync(
    out,
    JSON.stringify({ text, parsed }, null, 2),
    "utf8"
  );
}
