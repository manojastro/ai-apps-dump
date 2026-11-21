import { z } from "zod";

function cleanText(value: string): string {
  return value
    .replace(/\u0000/g, "")
    .replace(/\r\n?/g, "\n")
    .replace(/[\u0001-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/ *\n */g, "\n")
    .trim();
}

const text = (max: number) =>
  z
    .string()
    .max(max)
    .default("")
    .transform((value) => cleanText(value));

const textList = (maxItems: number, maxLength: number) =>
  z
    .array(text(maxLength))
    .max(maxItems)
    .default([])
    .transform((items) => items.filter(Boolean));

export const personalInfoSchema = z.object({
  fullName: text(120),
  title: text(160),
  email: text(200),
  phone: text(60),
  location: text(160),
  linkedin: text(300),
  github: text(300),
  website: text(300),
});

export const experienceSchema = z.object({
  company: text(160),
  role: text(160),
  location: text(160),
  startDate: text(80),
  endDate: text(80),
  current: z.boolean().default(false),
  achievements: textList(24, 900),
});

export const educationSchema = z.object({
  institution: text(180),
  degree: text(160),
  field: text(160),
  location: text(160),
  startDate: text(80),
  endDate: text(80),
  details: textList(12, 500),
});

export const skillGroupSchema = z.object({
  category: text(80),
  items: textList(40, 120),
});

export const projectSchema = z.object({
  name: text(160),
  description: text(1200),
  tech: textList(20, 80),
  link: text(300),
  achievements: textList(12, 600),
});

export const certificationSchema = z.object({
  name: text(200),
  issuer: text(160),
  date: text(80),
});

export const additionalSectionSchema = z.object({
  title: text(100),
  items: textList(30, 800),
});

export const resumeSchema = z.object({
  personal: personalInfoSchema.default({
    fullName: "",
    title: "",
    email: "",
    phone: "",
    location: "",
    linkedin: "",
    github: "",
    website: "",
  }),
  summary: text(5000),
  experience: z.array(experienceSchema).max(25).default([]),
  education: z.array(educationSchema).max(15).default([]),
  skills: z.array(skillGroupSchema).max(15).default([]),
  projects: z.array(projectSchema).max(20).default([]),
  certifications: z.array(certificationSchema).max(25).default([]),
  awards: textList(25, 600),
  additionalSections: z.array(additionalSectionSchema).max(12).default([]),
});

export const aiEditResponseSchema = z.object({
  resume: resumeSchema,
  message: text(500),
});

export type PersonalInfo = z.infer<typeof personalInfoSchema>;
export type Experience = z.infer<typeof experienceSchema>;
export type Education = z.infer<typeof educationSchema>;
export type SkillGroup = z.infer<typeof skillGroupSchema>;
export type Project = z.infer<typeof projectSchema>;
export type Certification = z.infer<typeof certificationSchema>;
export type AdditionalSection = z.infer<typeof additionalSectionSchema>;
export type ResumeData = z.infer<typeof resumeSchema>;

export function createEmptyResume(): ResumeData {
  return {
    personal: {
      fullName: "",
      title: "",
      email: "",
      phone: "",
      location: "",
      linkedin: "",
      github: "",
      website: "",
    },
    summary: "",
    experience: [],
    education: [],
    skills: [],
    projects: [],
    certifications: [],
    awards: [],
    additionalSections: [],
  };
}

export function cloneResume(resume: ResumeData): ResumeData {
  return structuredClone(resume);
}

export function hasResumeContent(resume: ResumeData): boolean {
  return Boolean(
    resume.personal.fullName.trim() ||
      resume.summary.trim() ||
      resume.experience.length ||
      resume.education.length ||
      resume.skills.some((group) => group.items.length) ||
      resume.projects.length ||
      resume.certifications.length ||
      resume.awards.length ||
      resume.additionalSections.length
  );
}

export function isResumeDownloadable(resume: ResumeData): boolean {
  const hasName = resume.personal.fullName.trim().length > 0;
  const hasContent =
    resume.summary.trim().length > 0 ||
    resume.experience.length > 0 ||
    resume.education.length > 0 ||
    resume.skills.some((group) => group.items.length > 0) ||
    resume.projects.length > 0;
  return hasName && hasContent;
}

export function getSectionCounts(resume: ResumeData) {
  return {
    experience: resume.experience.length,
    education: resume.education.length,
    skills: resume.skills.reduce((sum, group) => sum + group.items.length, 0),
    projects: resume.projects.length,
    certifications: resume.certifications.length,
    awards: resume.awards.length,
    additionalSections: resume.additionalSections.length,
  };
}

export function resumesEqual(a: ResumeData, b: ResumeData): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function createEmptyExperience(): Experience {
  return {
    company: "",
    role: "",
    location: "",
    startDate: "",
    endDate: "",
    current: false,
    achievements: [],
  };
}

export function createEmptyEducation(): Education {
  return {
    institution: "",
    degree: "",
    field: "",
    location: "",
    startDate: "",
    endDate: "",
    details: [],
  };
}

export function createEmptyProject(): Project {
  return {
    name: "",
    description: "",
    tech: [],
    link: "",
    achievements: [],
  };
}

export function createEmptyCertification(): Certification {
  return { name: "", issuer: "", date: "" };
}

export function createEmptySkillGroup(): SkillGroup {
  return { category: "", items: [] };
}

export function createEmptyAdditionalSection(): AdditionalSection {
  return { title: "", items: [] };
}
