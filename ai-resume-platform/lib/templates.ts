export type TemplateId =
  | "classic"
  | "entry-level"
  | "ats-simple"
  | "minimalist"
  | "infographic"
  | "corporate"
  | "modern"
  | "technical";

export type SectionKey =
  | "summary"
  | "experience"
  | "education"
  | "skills"
  | "projects"
  | "certifications"
  | "awards"
  | "additional";

export type HeaderVariant = "left" | "centered" | "split";
export type HeadingVariant =
  | "rule"
  | "underline"
  | "pill"
  | "side-label"
  | "minimal-line"
  | "accent-rule";
export type SkillsLayout = "grouped" | "columns" | "labeled";
export type ExperienceStyle = "classic" | "ats" | "minimal" | "corporate";
export type EducationStyle = "classic" | "minimal";
export type HeaderRule = "none" | "single" | "double" | "thick-pair";

export interface TemplateConfig {
  id: TemplateId;
  name: string;
  description: string;
  source: string;
  header: HeaderVariant;
  heading: HeadingVariant;
  headingItalic?: boolean;
  accent: string;
  ink: string;
  muted: string;
  rule: string;
  fontFamily: string;
  pdfFont: "helvetica" | "times";
  nameSize: number;
  titleSize: number;
  contactSize: number;
  bodySize: number;
  sectionSize: number;
  metaSize: number;
  lineHeight: number;
  paddingX: number;
  paddingY: number;
  sectionGap: number;
  itemGap: number;
  nameWeight: number;
  nameTracking: number;
  nameTransform: "uppercase" | "none";
  titleTransform: "uppercase" | "none";
  titleWeight: number;
  contactSeparator: string;
  headerRule: HeaderRule;
  headerRuleColor: "ink" | "accent" | "muted";
  skillsLayout: SkillsLayout;
  skillsColumns: 2 | 3;
  experienceStyle: ExperienceStyle;
  educationStyle: EducationStyle;
  bulletChar: string;
  sectionOrder: SectionKey[];
  sectionLabels: Record<SectionKey, string>;
  sideLabelWidth?: number;
}

const labels = (
  overrides: Partial<Record<SectionKey, string>> = {}
): Record<SectionKey, string> => ({
  summary: "Summary",
  experience: "Experience",
  education: "Education",
  skills: "Skills",
  projects: "Projects",
  certifications: "Certifications",
  awards: "Awards",
  additional: "Additional information",
  ...overrides,
});

export const TEMPLATES: Record<TemplateId, TemplateConfig> = {
  classic: {
    id: "classic",
    name: "Classic",
    description: "Left aligned. Editorial calm.",
    source: "Best 1.pdf",
    header: "left",
    heading: "rule",
    accent: "#141412",
    ink: "#171715",
    muted: "#5f5e58",
    rule: "#1c1c19",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 35,
    titleSize: 14,
    contactSize: 10.5,
    bodySize: 13,
    sectionSize: 12.5,
    metaSize: 10.5,
    lineHeight: 1.52,
    paddingX: 60,
    paddingY: 54,
    sectionGap: 25,
    itemGap: 14,
    nameWeight: 700,
    nameTracking: -0.025,
    nameTransform: "uppercase",
    titleTransform: "uppercase",
    titleWeight: 500,
    contactSeparator: "  |  ",
    headerRule: "single",
    headerRuleColor: "ink",
    skillsLayout: "grouped",
    skillsColumns: 2,
    experienceStyle: "classic",
    educationStyle: "classic",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "experience",
      "education",
      "skills",
      "projects",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "Profile",
      experience: "Professional experience",
      skills: "Professional skills",
      additional: "Additional information",
    }),
  },
  "entry-level": {
    id: "entry-level",
    name: "Entry level",
    description: "Centred. Built for early careers.",
    source: "Best 2.pdf",
    header: "centered",
    heading: "underline",
    accent: "#111110",
    ink: "#161614",
    muted: "#4f4e49",
    rule: "#1a1a17",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 31,
    titleSize: 12,
    contactSize: 10.5,
    bodySize: 12.8,
    sectionSize: 12,
    metaSize: 10.5,
    lineHeight: 1.5,
    paddingX: 58,
    paddingY: 52,
    sectionGap: 22,
    itemGap: 13,
    nameWeight: 700,
    nameTracking: -0.015,
    nameTransform: "none",
    titleTransform: "uppercase",
    titleWeight: 500,
    contactSeparator: "  |  ",
    headerRule: "none",
    headerRuleColor: "ink",
    skillsLayout: "labeled",
    skillsColumns: 2,
    experienceStyle: "ats",
    educationStyle: "classic",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "education",
      "skills",
      "projects",
      "experience",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "Summary",
      skills: "Technical skills",
      experience: "Experience",
    }),
  },
  "ats-simple": {
    id: "ats-simple",
    name: "ATS simple",
    description: "Single column. Plain, standard headings.",
    source: "Black and White Professional ATS Friendly Resume.pdf",
    header: "centered",
    heading: "underline",
    headingItalic: true,
    accent: "#111110",
    ink: "#171715",
    muted: "#4e4d48",
    rule: "#1b1b18",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 32,
    titleSize: 13,
    contactSize: 10.5,
    bodySize: 13,
    sectionSize: 12.5,
    metaSize: 10.5,
    lineHeight: 1.5,
    paddingX: 60,
    paddingY: 52,
    sectionGap: 20,
    itemGap: 13,
    nameWeight: 700,
    nameTracking: -0.01,
    nameTransform: "uppercase",
    titleTransform: "uppercase",
    titleWeight: 600,
    contactSeparator: "  |  ",
    headerRule: "none",
    headerRuleColor: "ink",
    skillsLayout: "labeled",
    skillsColumns: 2,
    experienceStyle: "ats",
    educationStyle: "classic",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "skills",
      "experience",
      "projects",
      "education",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "Professional objective",
      skills: "Technical skills",
      experience: "Professional experience",
      awards: "Awards & leadership",
    }),
  },
  minimalist: {
    id: "minimalist",
    name: "Minimalist",
    description: "Quiet type. Generous spacing.",
    source: "Black and White Minimalist Accountant Resume.pdf",
    header: "centered",
    heading: "minimal-line",
    accent: "#1c1c1a",
    ink: "#242420",
    muted: "#737169",
    rule: "#c9c7bf",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 33,
    titleSize: 18,
    contactSize: 10.5,
    bodySize: 13,
    sectionSize: 12,
    metaSize: 10.5,
    lineHeight: 1.65,
    paddingX: 62,
    paddingY: 58,
    sectionGap: 28,
    itemGap: 16,
    nameWeight: 700,
    nameTracking: -0.02,
    nameTransform: "uppercase",
    titleTransform: "none",
    titleWeight: 400,
    contactSeparator: "     ",
    headerRule: "single",
    headerRuleColor: "muted",
    skillsLayout: "columns",
    skillsColumns: 2,
    experienceStyle: "minimal",
    educationStyle: "minimal",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "education",
      "experience",
      "skills",
      "projects",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "About me",
      experience: "Work experience",
      additional: "Additional information",
    }),
  },
  infographic: {
    id: "infographic",
    name: "Infographic",
    description: "Soft section bars. Two-column skills.",
    source: "Black and White Simple Infographic Resume.pdf",
    header: "left",
    heading: "pill",
    headingItalic: true,
    accent: "#171715",
    ink: "#1e1e1b",
    muted: "#5d5c56",
    rule: "#e4e3de",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 34,
    titleSize: 14,
    contactSize: 10.5,
    bodySize: 13,
    sectionSize: 11.5,
    metaSize: 10.5,
    lineHeight: 1.52,
    paddingX: 58,
    paddingY: 56,
    sectionGap: 23,
    itemGap: 14,
    nameWeight: 700,
    nameTracking: -0.02,
    nameTransform: "uppercase",
    titleTransform: "uppercase",
    titleWeight: 600,
    contactSeparator: "  |  ",
    headerRule: "none",
    headerRuleColor: "ink",
    skillsLayout: "columns",
    skillsColumns: 3,
    experienceStyle: "classic",
    educationStyle: "classic",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "skills",
      "experience",
      "education",
      "projects",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "Summary",
      skills: "Technical skills",
      experience: "Professional experience",
      additional: "Additional information",
    }),
  },
  corporate: {
    id: "corporate",
    name: "Corporate",
    description: "Label-led layout. Compact and formal.",
    source: "Black White Corporate Finance Resume.pdf",
    header: "split",
    heading: "side-label",
    accent: "#111110",
    ink: "#191917",
    muted: "#55544e",
    rule: "#bebcb4",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 33,
    titleSize: 12.5,
    contactSize: 10,
    bodySize: 12.3,
    sectionSize: 10.5,
    metaSize: 10,
    lineHeight: 1.5,
    paddingX: 56,
    paddingY: 52,
    sectionGap: 0,
    itemGap: 13,
    nameWeight: 700,
    nameTracking: -0.02,
    nameTransform: "uppercase",
    titleTransform: "none",
    titleWeight: 600,
    contactSeparator: "   ",
    headerRule: "thick-pair",
    headerRuleColor: "ink",
    skillsLayout: "columns",
    skillsColumns: 2,
    experienceStyle: "corporate",
    educationStyle: "minimal",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "skills",
      "experience",
      "education",
      "projects",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "About me",
      skills: "Core skills",
      experience: "Experience",
      awards: "Recognition",
      additional: "Additional",
    }),
    sideLabelWidth: 132,
  },
  modern: {
    id: "modern",
    name: "Modern",
    description: "Warm accent. Clean and current.",
    source: "Black and White Modern Professional Resume (1).pdf",
    header: "left",
    heading: "accent-rule",
    accent: "#b7762b",
    ink: "#1b1a17",
    muted: "#5e5c55",
    rule: "#d8a35f",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 34,
    titleSize: 13,
    contactSize: 10.5,
    bodySize: 13,
    sectionSize: 12.5,
    metaSize: 10.5,
    lineHeight: 1.54,
    paddingX: 58,
    paddingY: 54,
    sectionGap: 23,
    itemGap: 14,
    nameWeight: 700,
    nameTracking: -0.02,
    nameTransform: "uppercase",
    titleTransform: "uppercase",
    titleWeight: 500,
    contactSeparator: "  |  ",
    headerRule: "single",
    headerRuleColor: "accent",
    skillsLayout: "columns",
    skillsColumns: 2,
    experienceStyle: "classic",
    educationStyle: "classic",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "skills",
      "experience",
      "projects",
      "education",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "Summary",
      skills: "Professional skills",
      experience: "Professional experience",
      additional: "Additional information",
    }),
  },
  technical: {
    id: "technical",
    name: "Technical",
    description: "Blue rules. Crisp technical feel.",
    source: "White and Black Tech Professional Resume (1).pdf",
    header: "centered",
    heading: "accent-rule",
    accent: "#24479b",
    ink: "#1c1c1a",
    muted: "#5b5a54",
    rule: "#24479b",
    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
    pdfFont: "helvetica",
    nameSize: 33,
    titleSize: 13,
    contactSize: 10.5,
    bodySize: 13,
    sectionSize: 12.5,
    metaSize: 10.5,
    lineHeight: 1.52,
    paddingX: 58,
    paddingY: 52,
    sectionGap: 22,
    itemGap: 14,
    nameWeight: 700,
    nameTracking: -0.015,
    nameTransform: "uppercase",
    titleTransform: "uppercase",
    titleWeight: 600,
    contactSeparator: "  |  ",
    headerRule: "double",
    headerRuleColor: "muted",
    skillsLayout: "columns",
    skillsColumns: 3,
    experienceStyle: "ats",
    educationStyle: "classic",
    bulletChar: "•",
    sectionOrder: [
      "summary",
      "experience",
      "education",
      "skills",
      "projects",
      "certifications",
      "awards",
      "additional",
    ],
    sectionLabels: labels({
      summary: "Summary",
      skills: "Skills",
      additional: "Additional information",
    }),
  },
};

export const TEMPLATE_LIST = Object.values(TEMPLATES);
export const DEFAULT_TEMPLATE_ID: TemplateId = "classic";

export function getTemplate(id: string): TemplateConfig {
  return TEMPLATES[id as TemplateId] ?? TEMPLATES[DEFAULT_TEMPLATE_ID];
}

export function isTemplateId(id: string): id is TemplateId {
  return id in TEMPLATES;
}
