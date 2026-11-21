import type { ResumeData } from "./resumeSchema";

const STOP_WORDS = new Set([
  "the", "and", "for", "with", "this", "that", "from", "will", "have",
  "been", "are", "was", "our", "your", "you", "all", "can", "able",
  "work", "team", "role", "job", "experience", "years", "required",
]);

export interface KeywordMatchResult {
  matchPercent: number;
  matched: string[];
  missing: string[];
  total: number;
}

function extractKeywords(text: string): string[] {
  return [
    ...new Set(
      text
        .toLowerCase()
        .replace(/[^a-z0-9+#.\s-]/g, " ")
        .split(/\s+/)
        .filter((w) => w.length > 2 && !STOP_WORDS.has(w))
    ),
  ];
}

function resumeToText(data: ResumeData): string {
  const parts = [
    data.targetRole,
    data.summary,
    ...data.experience.flatMap((e) => [e.role, e.company, ...e.bullets]),
    ...data.skills.technical,
    ...data.skills.soft,
    ...data.education.map((e) => `${e.degree} ${e.field}`),
    ...data.projects.map((p) => `${p.name} ${p.description} ${p.tech.join(" ")}`),
  ];
  return parts.filter(Boolean).join(" ").toLowerCase();
}

export function analyzeKeywordMatch(
  resume: ResumeData,
  jobDescription: string
): KeywordMatchResult | null {
  if (!jobDescription.trim()) return null;

  const jobKeywords = extractKeywords(jobDescription).slice(0, 40);
  if (jobKeywords.length === 0) return null;

  const resumeText = resumeToText(resume);
  const matched: string[] = [];
  const missing: string[] = [];

  for (const kw of jobKeywords) {
    if (resumeText.includes(kw)) matched.push(kw);
    else missing.push(kw);
  }

  const matchPercent = Math.round((matched.length / jobKeywords.length) * 100);

  return {
    matchPercent,
    matched: matched.slice(0, 12),
    missing: missing.slice(0, 8),
    total: jobKeywords.length,
  };
}