import type { ResumeData } from "./resumeSchema";

export interface ResumeScore {
  overall: number;
  sections: { label: string; score: number; tip?: string }[];
  tips: string[];
}

export function calculateResumeScore(data: ResumeData): ResumeScore {
  const sections: ResumeScore["sections"] = [];
  const tips: string[] = [];

  const nameScore = data.personalInfo.fullName.trim() ? 100 : 0;
  sections.push({
    label: "Contact",
    score: nameScore,
    tip: nameScore < 100 ? "Add your full name" : undefined,
  });

  const contactFields = [
    data.personalInfo.email,
    data.personalInfo.phone,
    data.personalInfo.location,
  ].filter((f) => f.trim()).length;
  const contactScore = Math.round((contactFields / 3) * 100);
  if (contactScore < 100) tips.push("Add email, phone, and location for recruiter reachability");

  const expScore =
    data.experience.length > 0
      ? Math.min(
          100,
          data.experience.reduce((acc, e) => {
            let s = e.company && e.role ? 50 : 20;
            if (e.bullets.filter(Boolean).length >= 3) s += 50;
            else if (e.bullets.filter(Boolean).length > 0) s += 25;
            return acc + s;
          }, 0) / data.experience.length
        )
      : 0;
  sections.push({
    label: "Experience",
    score: expScore,
    tip: expScore < 60 ? "Add 3–5 achievement bullets per role" : undefined,
  });

  const summaryScore = data.summary.trim().length > 50 ? 100 : data.summary.trim() ? 50 : 0;
  sections.push({
    label: "Summary",
    score: summaryScore,
    tip: summaryScore < 100 ? "Write a 2–3 line professional summary" : undefined,
  });

  const skillCount =
    data.skills.technical.filter(Boolean).length +
    data.skills.soft.filter(Boolean).length;
  const skillsScore = skillCount >= 8 ? 100 : skillCount >= 4 ? 70 : skillCount > 0 ? 40 : 0;
  sections.push({
    label: "Skills",
    score: skillsScore,
    tip: skillsScore < 70 ? "List 8+ relevant technical and soft skills" : undefined,
  });

  const eduScore = data.education.length > 0 ? 100 : 0;
  sections.push({
    label: "Education",
    score: eduScore,
    tip: eduScore < 100 ? "Add at least one education entry" : undefined,
  });

  sections.forEach((s) => {
    if (s.tip) tips.push(s.tip);
  });

  const overall = Math.round(
    sections.reduce((sum, s) => sum + s.score, 0) / sections.length
  );

  return { overall, sections, tips: tips.slice(0, 3) };
}