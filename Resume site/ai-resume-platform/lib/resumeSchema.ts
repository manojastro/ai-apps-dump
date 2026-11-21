export interface PersonalInfo {
  fullName: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  portfolio: string;
}

export interface Experience {
  company: string;
  role: string;
  location: string;
  startDate: string;
  endDate: string;
  current: boolean;
  bullets: string[];
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  startDate: string;
  endDate: string;
}

export interface Certification {
  name: string;
  issuer: string;
  date: string;
}

export interface Project {
  name: string;
  description: string;
  tech: string[];
  link: string;
}

export interface ResumeData {
  personalInfo: PersonalInfo;
  targetRole: string;
  summary: string;
  experience: Experience[];
  education: Education[];
  skills: { technical: string[]; soft: string[] };
  certifications: Certification[];
  projects: Project[];
}

export type TemplateId =
  | "blue-clean"
  | "tech-pro"
  | "ats-friendly"
  | "modern-bw"
  | "corporate-minimal";

export interface TemplateStyleTokens {
  id: TemplateId;
  name: string;
  description: string;
  sourcePdf: string;
  fontFamily: string;
  headingFontFamily: string;
  accentColor: string;
  textColor: string;
  mutedColor: string;
  headingSize: string;
  bodySize: string;
  sectionSpacing: string;
  bulletStyle: "disc" | "dash";
  layout: "centered" | "left" | "ats";
}

export const emptyResume: ResumeData = {
  personalInfo: {
    fullName: "",
    email: "",
    phone: "",
    location: "",
    linkedin: "",
    portfolio: "",
  },
  targetRole: "",
  summary: "",
  experience: [],
  education: [],
  skills: { technical: [], soft: [] },
  certifications: [],
  projects: [],
};

export function isResumeDownloadable(data: ResumeData): boolean {
  const hasContact =
    data.personalInfo.fullName.trim() !== "" &&
    (data.personalInfo.email.trim() !== "" ||
      data.personalInfo.phone.trim() !== "");
  const hasContent =
    data.experience.length > 0 || data.education.length > 0;
  return hasContact && hasContent;
}

export function mergeResume(
  existing: ResumeData,
  incoming: Partial<ResumeData>
): ResumeData {
  return {
    personalInfo: { ...existing.personalInfo, ...incoming.personalInfo },
    targetRole: incoming.targetRole ?? existing.targetRole,
    summary: incoming.summary ?? existing.summary,
    experience: incoming.experience?.length
      ? incoming.experience
      : existing.experience,
    education: incoming.education?.length
      ? incoming.education
      : existing.education,
    skills: incoming.skills ?? existing.skills,
    certifications: incoming.certifications?.length
      ? incoming.certifications
      : existing.certifications,
    projects: incoming.projects?.length
      ? incoming.projects
      : existing.projects,
  };
}

export const LEGACY_TEMPLATE_MAP: Record<string, TemplateId> = {
  modern: "blue-clean",
  classic: "ats-friendly",
  minimal: "corporate-minimal",
};

export function normalizeTemplateId(id: string): TemplateId {
  if (id in LEGACY_TEMPLATE_MAP) return LEGACY_TEMPLATE_MAP[id];
  const valid: TemplateId[] = [
    "blue-clean",
    "tech-pro",
    "ats-friendly",
    "modern-bw",
    "corporate-minimal",
  ];
  return valid.includes(id as TemplateId) ? (id as TemplateId) : "blue-clean";
}