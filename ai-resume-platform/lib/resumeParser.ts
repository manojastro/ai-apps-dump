import {
  createEmptyResume,
  resumeSchema,
  type Certification,
  type Education,
  type Experience,
  type Project,
  type ResumeData,
  type SkillGroup,
} from "./resume";
import {
  DATE_RANGE_RE,
  cleanText,
  isPresentDate,
  normalizeYearMonth,
  readableDate,
  stripBullet,
  stripTrailingPunctuation,
  titleCaseIfShouting,
  uniqueBy,
} from "./text";

type KnownSection =
  | "summary"
  | "experience"
  | "education"
  | "skills"
  | "projects"
  | "certifications"
  | "awards"
  | "additional";

interface SectionChunk {
  key: KnownSection;
  title: string;
  known: boolean;
  lines: string[];
}

export interface ParsedResume {
  resume: ResumeData;
  detectedSections: string[];
  looksLikeResume: boolean;
  hasUsableContent: boolean;
}

const SECTION_SYNONYMS: Record<KnownSection, string[]> = {
  summary: [
    "summary",
    "professional summary",
    "executive summary",
    "career summary",
    "profile",
    "professional profile",
    "personal profile",
    "about me",
    "about",
    "objective",
    "professional objective",
    "career objective",
    "personal statement",
  ],
  experience: [
    "experience",
    "work experience",
    "professional experience",
    "relevant experience",
    "employment history",
    "work history",
    "career history",
    "employment",
    "professional background",
  ],
  education: [
    "education",
    "academic background",
    "academic qualifications",
    "education and training",
    "education & training",
    "qualifications",
    "academic history",
    "training",
  ],
  skills: [
    "skills",
    "technical skills",
    "professional skills",
    "core skills",
    "key skills",
    "core competencies",
    "competencies",
    "areas of expertise",
    "technical expertise",
    "technologies",
    "tools and technologies",
    "technical proficiencies",
    "expertise",
  ],
  projects: [
    "projects",
    "personal projects",
    "selected projects",
    "academic projects",
    "key projects",
    "project experience",
    "side projects",
  ],
  certifications: [
    "certifications",
    "certificates",
    "professional certifications",
    "licenses",
    "licences",
    "certifications and training",
    "certifications & training",
    "licenses & certifications",
    "courses and certifications",
  ],
  awards: [
    "awards",
    "achievements",
    "honors",
    "honours",
    "awards and achievements",
    "awards & achievements",
    "awards and recognition",
    "recognition",
    "accomplishments",
    "key achievements",
  ],
  additional: [
    "languages",
    "interests",
    "hobbies",
    "memberships",
    "professional memberships",
    "affiliations",
    "volunteer experience",
    "volunteering",
    "activities",
    "leadership",
    "publications",
    "patents",
    "speaking",
    "references",
    "additional information",
    "additional",
    "notes",
  ],
};

const ROLE_WORDS =
  /\b(engineer|developer|manager|designer|analyst|consultant|specialist|director|lead|architect|scientist|accountant|assistant|coordinator|administrator|intern|associate|executive|officer|technician|teacher|professor|student|freelancer|founder|owner|president|head|supervisor|strategist|recruiter|marketer|writer|editor|researcher|auditor|advisor|consultant)\b/i;

const DEGREE_RE =
  /\b(bachelor|master|doctorate|ph\.?d|b\.?\s?tech|m\.?\s?tech|b\.?\s?sc|m\.?\s?sc|b\.?\s?e\.?|m\.?\s?e\.?|b\.?\s?com|m\.?\s?com|b\.?a\.?|m\.?a\.?|mba|bba|bca|mca|associate|diploma|high school|secondary|higher secondary|12th|10th)\b/i;

const INSTITUTION_RE =
  /\b(university|college|institute|school|academy|polytechnic|faculty|iit|nit|bits)\b/i;

const LOCATION_COUNTRIES =
  /\b(india|united states|usa|u\.s\.a|uk|united kingdom|canada|australia|germany|france|singapore|uae|united arab emirates|netherlands|ireland|new zealand|south africa|brazil|mexico|spain|italy|japan|china)\b/i;

const KNOWN_SKILLS = [
  "Python",
  "Java",
  "JavaScript",
  "TypeScript",
  "C++",
  "C#",
  "Rust",
  "Ruby",
  "PHP",
  "Swift",
  "Kotlin",
  "Scala",
  "MATLAB",
  "SQL",
  "HTML",
  "CSS",
  "React",
  "Next.js",
  "Vue",
  "Angular",
  "Node.js",
  "Express",
  "Django",
  "Flask",
  "FastAPI",
  "Spring Boot",
  ".NET",
  "GraphQL",
  "REST APIs",
  "AWS",
  "Azure",
  "GCP",
  "Docker",
  "Kubernetes",
  "Terraform",
  "Jenkins",
  "GitHub Actions",
  "GitLab CI",
  "Linux",
  "Git",
  "PostgreSQL",
  "MySQL",
  "MongoDB",
  "Redis",
  "Elasticsearch",
  "Kafka",
  "RabbitMQ",
  "Airflow",
  "Spark",
  "Hadoop",
  "Snowflake",
  "Databricks",
  "Tableau",
  "Power BI",
  "Excel",
  "Machine Learning",
  "Deep Learning",
  "NLP",
  "Computer Vision",
  "TensorFlow",
  "PyTorch",
  "scikit-learn",
  "Pandas",
  "NumPy",
  "OpenAI",
  "LangChain",
  "RAG",
  "AI Agents",
  "Prompt Engineering",
  "Data Analysis",
  "Data Engineering",
  "ETL",
  "Agile",
  "Scrum",
  "Jira",
  "Figma",
  "Adobe XD",
  "Photoshop",
  "Illustrator",
  "Salesforce",
  "SAP",
  "Oracle",
  "Workday",
  "QuickBooks",
  "Financial Modeling",
  "Forecasting",
  "Auditing",
  "Project Management",
  "Stakeholder Management",
  "Communication",
  "Leadership",
  "Problem Solving",
];

function isBulletLine(line: string): boolean {
  return /^\s*(?:[•▪◦‣●○·*+\-–—]|\d{1,2}[.)])\s+/.test(line);
}

function isPageNoise(line: string): boolean {
  const value = line.trim();
  if (!value) return true;
  if (/^(?:page\s*)?\d+(?:\s*(?:of|\/)\s*\d+)?$/i.test(value)) return true;
  if (/^[–—-]\s*\d+\s*[–—-]$/.test(value)) return true;
  return false;
}

function normalizeHeading(line: string): string {
  return stripBullet(line)
    .replace(/\s*:\s*$/, "")
    .replace(/\s+/g, " ")
    .trim();
}

function headingWords(value: string): number {
  return value.split(/\s+/).filter(Boolean).length;
}

function isMostlyUppercase(value: string): boolean {
  const letters = value.replace(/[^a-z]/gi, "");
  if (letters.length < 3) return false;
  return value.replace(/[^A-Z]/g, "").length / letters.length > 0.8;
}

function matchSection(line: string): {
  key: KnownSection;
  title: string;
} | null {
  const heading = normalizeHeading(line);
  if (!heading || heading.length > 70) return null;
  if (heading.includes(":") || heading.includes("@") || /\d/.test(heading)) {
    return null;
  }
  const lower = heading.toLowerCase();
  if (headingWords(heading) > 6) return null;

  const combined = /\b(?:experience|employment)\b/.test(lower) &&
    /\bprojects?\b/.test(lower);
  if (combined) {
    return { key: "experience", title: heading };
  }

  let best: { key: KnownSection; title: string; length: number } | null = null;
  for (const [key, synonyms] of Object.entries(SECTION_SYNONYMS) as [
    KnownSection,
    string[],
  ][]) {
    for (const synonym of synonyms) {
      if (lower === synonym) {
        if (!best || synonym.length > best.length) {
          best = { key, title: heading, length: synonym.length };
        }
      }
    }
  }
  if (best) return { key: best.key, title: best.title };

  const allCaps = isMostlyUppercase(heading);
  if (
    allCaps &&
    /\b(certification|certificate|education|experience|skill|competenc|project|language|interest|hobb|membership|volunteer|activit|award|achievement|honou?r|publication|patent|reference|summary|profile|objective)\b/i.test(
      lower
    )
  ) {
    if (/certification|certificate|licen[cs]e/.test(lower)) {
      return { key: "certifications", title: heading };
    }
    if (/education|academic|qualification/.test(lower)) {
      return { key: "education", title: heading };
    }
    if (/experience|employment|career history/.test(lower)) {
      return { key: "experience", title: heading };
    }
    if (/skill|competenc|expertise/.test(lower)) {
      return { key: "skills", title: heading };
    }
    if (/project/.test(lower)) {
      return { key: "projects", title: heading };
    }
    if (/award|achievement|honou?r|recognition/.test(lower)) {
      return { key: "awards", title: heading };
    }
    if (/summary|profile|objective|about/.test(lower)) {
      return { key: "summary", title: heading };
    }
    return { key: "additional", title: heading };
  }

  return null;
}

function matchCustomSection(
  line: string,
  previousLine: string,
  nextLine: string,
  blankAbove: boolean
): { key: "additional"; title: string } | null {
  const heading = normalizeHeading(line);
  if (!heading || heading.length > 60) return null;
  if (headingWords(heading) > 5) return null;
  if (heading.includes(":") || heading.includes("@") || /\d/.test(heading)) {
    return null;
  }
  if (!isMostlyUppercase(heading)) return null;
  if (matchSection(line)) return null;
  if (ROLE_WORDS.test(heading)) return null;
  if (looksLikeLocation(heading)) return null;
  if (looksLikeName(heading)) return null;
  if (
    nextLine &&
    !isBulletLine(nextLine) &&
    (ROLE_WORDS.test(nextLine) || DATE_RANGE_RE.test(nextLine))
  ) {
    return null;
  }
  const nextIsBullet = isBulletLine(nextLine);
  if (!blankAbove && !nextIsBullet) return null;
  if (!nextLine.trim()) return null;
  if (previousLine && !blankAbove && !isBulletLine(previousLine)) {
    return null;
  }
  return { key: "additional", title: heading };
}

function splitIntoLines(raw: string): string[] {
  const normalized = cleanText(raw).replace(/\r\n?/g, "\n");
  const initial = normalized.split("\n").map((line) => line.replace(/\s+$/g, ""));
  const joined: string[] = [];
  for (let i = 0; i < initial.length; i++) {
    const line = initial[i];
    const next = initial[i + 1] ?? "";
    if (
      /[a-z]-$/i.test(line) &&
      /^[a-z]/.test(next.trim()) &&
      line.trim().length > 2
    ) {
      joined.push(line.replace(/-$/, "") + next.trim());
      i++;
    } else {
      joined.push(line);
    }
  }

  const result: string[] = [];
  for (const line of joined) {
    if (isPageNoise(line)) {
      if (result.length && result[result.length - 1] !== "") result.push("");
      continue;
    }
    result.push(line.replace(/\u00a0/g, " ").trimEnd());
  }
  return result;
}

function findEmail(text: string): string {
  return text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0] ?? "";
}

function findPhone(text: string): string {
  const candidates =
    text.match(
      /(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(?:[\s.-]?\d{2,4})?/g
    ) ?? [];
  for (const candidate of candidates) {
    const digits = candidate.replace(/\D/g, "");
    if (digits.length < 7 || digits.length > 15) continue;
    if (/^\d{4}\s*[-–—]\s*\d{4}$/.test(candidate.trim())) continue;
    if (/^(?:19|20)\d{2}$/.test(digits)) continue;
    const matchIndex = text.indexOf(candidate);
    const before = text.slice(Math.max(0, matchIndex - 1), matchIndex);
    const after = text.slice(
      matchIndex + candidate.length,
      matchIndex + candidate.length + 1
    );
    if (before && /[A-Za-z/]/.test(before)) continue;
    if (after && /[A-Za-z/]/.test(after)) continue;
    return candidate.trim();
  }
  return "";
}

function extractUrls(text: string): string[] {
  const matches =
    text.match(
      /(?:https?:\/\/)?(?:www\.)?[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+(?:\/[^\s|,;()]*)?/gi
    ) ?? [];
  return matches
    .map((url) => url.replace(/[.,;:)]+$/g, "").trim())
    .filter((url) => url.length > 3);
}

function parseContact(text: string) {
  const email = findEmail(text);
  const phone = findPhone(text);
  const urls = extractUrls(text.replaceAll(email, " "));
  let linkedin = "";
  let github = "";
  let website = "";

  for (const raw of urls) {
    const lower = raw.toLowerCase();
    if (!linkedin && lower.includes("linkedin.com/")) {
      linkedin = raw;
    } else if (!github && lower.includes("github.com/")) {
      github = raw;
    } else if (
      !website &&
      !lower.includes("linkedin.com/") &&
      !lower.includes("github.com/") &&
      !lower.match(/\.(pdf|docx?)(?:$|\?)/i)
    ) {
      website = raw;
    }
  }

  return { email, phone, linkedin, github, website };
}

function looksLikeLocation(line: string): boolean {
  const value = line.trim();
  if (!value || value.length > 90) return false;
  if (findEmail(value) || /\d{4}/.test(value)) return false;
  if (/^(remote|hybrid|on-?site)$/i.test(value)) return true;
  if (LOCATION_COUNTRIES.test(value)) return true;
  if (/^[A-Za-z .'-]+,\s*[A-Z]{2}$/.test(value)) return true;
  if (/^[A-Za-z .'-]+,\s*[A-Za-z .'-]{2,}$/.test(value)) return true;
  return false;
}

function looksLikeName(line: string): boolean {
  const value = line.replace(/\s+/g, " ").trim();
  if (!value || value.length > 70) return false;
  if (findEmail(value) || /https?:|www\.|@/i.test(value)) return false;
  if (/[|]/.test(value)) return false;
  if (/\d/.test(value)) return false;
  if (matchSection(value)) return false;
  if (/^(curriculum vitae|resume|cv|profile)$/i.test(value)) return false;
  if (/^(i|my|we|our|he|she|they)\b/i.test(value)) return false;
  if (isMostlyUppercase(value) && headingWords(value) > 5) return false;
  const words = value.split(/\s+/).filter(Boolean);
  if (words.length < 1 || words.length > 5) return false;
  if (!/^[A-Za-zÀ-ÿ.'’\-\s]+$/.test(value)) return false;
  if (/\b(engineer|manager|developer|designer|analyst|accountant|consultant)\b/i.test(value)) {
    return false;
  }
  if (!isMostlyUppercase(value)) {
    const nameLike = words.every(
      (word) =>
        /^[A-ZÀ-Ý]/.test(word) ||
        /^(de|van|von|da|bin|al|el)$/i.test(word)
    );
    if (!nameLike) return false;
  }
  return true;
}

function looksLikeRole(line: string): boolean {
  const value = line.trim();
  if (!value || value.length > 100) return false;
  return ROLE_WORDS.test(value);
}

function splitHeadingParts(value: string): string[] {
  return value
    .split(/\s+(?:\||—|–|·)\s+|\s+-\s+|\s+at\s+/i)
    .map((part) => part.trim())
    .filter(Boolean);
}

function parseRoleCompany(
  heading: string,
  bodyLines: string[]
): {
  role: string;
  company: string;
  location: string;
  remaining: string[];
} {
  let clean = heading
    .replace(/^\s*(?:role|position|title)\s*:\s*/i, "")
    .replace(/\s+,/g, ",")
    .trim();
  let parts = splitHeadingParts(clean).map((part) =>
    part.replace(/^\s*(?:company|employer)\s*:\s*/i, "").trim()
  );

  let role = "";
  let company = "";
  let location = "";

  if (parts.length >= 2) {
    if (looksLikeRole(parts[1]) && !looksLikeRole(parts[0])) {
      role = parts[1];
      company = parts[0];
      location = parts[2] ?? "";
    } else {
      role = parts[0];
      company = parts[1];
      location = parts[2] ?? "";
    }
  } else if (parts.length === 1) {
    const value = parts[0];
    if (value.includes(",")) {
      const [before, ...rest] = value.split(",");
      role = before.trim();
      const tail = rest.join(",").trim();
      if (looksLikeLocation(tail)) location = tail;
      else if (!company) company = tail;
    } else {
      role = value;
    }
  }

  const remaining: string[] = [];
  for (const raw of bodyLines) {
    const line = raw.trim();
    if (!line) continue;
    if (!role && looksLikeRole(line)) {
      role = line;
      continue;
    }
    if (!company && !location && looksLikeLocation(line)) {
      location = line;
      continue;
    }
    if (!company && !isBulletLine(raw) && line.length <= 120) {
      company = line;
      continue;
    }
    remaining.push(raw);
  }

  if (!role && company) {
    role = "";
  }
  if (!role && !company && clean) {
    role = clean;
  }

  return {
    role: stripTrailingPunctuation(role),
    company: stripTrailingPunctuation(company),
    location: stripTrailingPunctuation(location),
    remaining,
  };
}

function joinContinuation(lines: string[]): string[] {
  const result: string[] = [];
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    if (!result.length) {
      result.push(line);
      continue;
    }
    const previous = result[result.length - 1];
    if (
      !isBulletLine(raw) &&
      !/[.!?;:]$/.test(previous) &&
      /^[a-z(]/.test(line) &&
      previous.length > 20
    ) {
      result[result.length - 1] = `${previous} ${line}`;
    } else {
      result.push(line);
    }
  }
  return result;
}

function mergeSectionLines(chunks: SectionChunk[], key: KnownSection): string[] {
  return chunks
    .filter((chunk) => chunk.key === key)
    .flatMap((chunk) => [...chunk.lines, ""]);
}

function parseExperience(lines: string[]): Experience[] {
  const entries: Array<{
    heading: string;
    start: string;
    end: string;
    current: boolean;
    body: string[];
  }> = [];
  const pending: string[] = [];
  const consumed = new Set<number>();

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    const match = line.match(DATE_RANGE_RE);
    if (match && line.length <= 220) {
      const before = line
        .slice(0, match.index)
        .replace(/[\s|,;:/\\-–—]+$/g, "")
        .trim();
      const after = line
        .slice((match.index ?? 0) + match[0].length)
        .replace(/^[\s|,;:/\\-–—]+/g, "")
        .trim();
      let heading = before;
      const previousIndex = i - 1;
      const previous =
        previousIndex >= 0 && !consumed.has(previousIndex)
          ? lines[previousIndex]?.trim() ?? ""
          : "";
      if (!heading && previous && !isBulletLine(previous)) {
        heading = previous;
        consumed.add(previousIndex);
      } else if (
        heading &&
        previous &&
        !consumed.has(previousIndex) &&
        !isBulletLine(previous) &&
        !DATE_RANGE_RE.test(previous) &&
        !looksLikeRole(heading) &&
        looksLikeRole(previous)
      ) {
        heading = `${previous} | ${heading}`;
        consumed.add(previousIndex);
      }
      const entry = {
        heading,
        start: match[1],
        end: match[2],
        current: isPresentDate(match[2]),
        body: after ? [after] : [],
      };
      if (!heading && pending.length) {
        const last = pending[pending.length - 1];
        entry.heading = last;
        pending.pop();
      }
      pending.length = 0;
      entries.push(entry);
      continue;
    }

    if (!entries.length) {
      pending.push(line);
    } else {
      entries[entries.length - 1].body.push(line);
    }
  }

  if (!entries.length) {
    const blocks = splitBlocks(lines);
    for (const block of blocks) {
      const nonEmpty = block.filter((line) => line.trim());
      if (!nonEmpty.length) continue;
      const heading = nonEmpty[0].replace(/^[\s|,;:/\\-–—]+|\s+$/g, "");
      const body = nonEmpty.slice(1);
      const range = block.join(" ").match(DATE_RANGE_RE);
      entries.push({
        heading,
        start: range?.[1] ?? "",
        end: range?.[2] ?? "",
        current: range ? isPresentDate(range[2]) : false,
        body,
      });
    }
  }

  return entries
    .map((entry) => {
      const body = entry.body.filter((line) => line.trim());
      const parsed = parseRoleCompany(entry.heading, body);
      const bulletLines = parsed.remaining.filter(isBulletLine);
      const looseLines = parsed.remaining.filter(
        (line) => !isBulletLine(line) && line.trim()
      );
      const achievements = joinContinuation([
        ...bulletLines,
        ...looseLines,
      ]).map(stripBullet);

      return {
        company: parsed.company,
        role: parsed.role,
        location: parsed.location,
        startDate: readableDate(entry.start),
        endDate: entry.current ? "" : readableDate(entry.end),
        current: entry.current,
        achievements: uniqueBy(achievements, (item) => item),
      };
    })
    .filter(
      (entry) =>
        entry.company ||
        entry.role ||
        entry.achievements.length > 0 ||
        entry.startDate
    )
    .slice(0, 25);
}

function splitBlocks(lines: string[]): string[][] {
  const blocks: string[][] = [];
  let current: string[] = [];
  for (const line of lines) {
    if (!line.trim()) {
      if (current.length) {
        blocks.push(current);
        current = [];
      }
    } else {
      current.push(line);
    }
  }
  if (current.length) blocks.push(current);
  return blocks.length ? blocks : [lines];
}

function extractDegree(value: string): { degree: string; field: string } {
  const clean = value.replace(/\s+/g, " ").trim();
  const inMatch = clean.match(/^(.+?)\s+in\s+([^,|]+)$/i);
  if (inMatch && DEGREE_RE.test(inMatch[1])) {
    return { degree: inMatch[1].trim(), field: inMatch[2].trim() };
  }
  return { degree: clean, field: "" };
}

function extractInstitution(value: string): string {
  const parts = value
    .split(/\s*(?:,|\||—|–)\s*/)
    .map((part) => part.trim())
    .filter(Boolean);
  return (
    parts.find((part) => INSTITUTION_RE.test(part)) ??
    (INSTITUTION_RE.test(value) ? value.trim() : "")
  );
}

function parseEducation(lines: string[]): Education[] {
  const blocks = splitBlocks(lines);
  const results: Education[] = [];

  for (const block of blocks) {
    const nonEmpty = block.map((line) => line.trim()).filter(Boolean);
    if (!nonEmpty.length) continue;

    let dateStart = "";
    let dateEnd = "";
    const contentLines: string[] = [];

    for (const line of nonEmpty) {
      const match = line.match(DATE_RANGE_RE);
      if (match) {
        if (!dateStart) {
          dateStart = match[1];
          dateEnd = match[2];
        }
        const text = `${line.slice(0, match.index)} ${line.slice(
          (match.index ?? 0) + match[0].length
        )}`.trim();
        if (text) contentLines.push(text);
      } else if (/^\d{4}$/.test(line) && !dateStart) {
        dateStart = line;
      } else {
        contentLines.push(line);
      }
    }

    const degreeLineIndex = contentLines.findIndex((line) => DEGREE_RE.test(line));
    const institutionLineIndex = contentLines.findIndex((line) =>
      INSTITUTION_RE.test(line)
    );

    let degree = "";
    let field = "";
    let institution = "";
    let location = "";

    if (degreeLineIndex >= 0) {
      const parsedDegree = extractDegree(contentLines[degreeLineIndex]);
      degree = parsedDegree.degree;
      field = parsedDegree.field;
    }

    for (let i = 0; i < contentLines.length; i++) {
      const line = contentLines[i];
      if (i === degreeLineIndex) {
        const parts = splitHeadingParts(line);
        if (parts.length > 1) {
          const other = parts.find(
            (part) => !DEGREE_RE.test(part) && INSTITUTION_RE.test(part)
          );
          if (other) institution = other;
        }
        continue;
      }
      if (i === institutionLineIndex || INSTITUTION_RE.test(line)) {
        const instPart = extractInstitution(line);
        if (!institution && instPart) institution = instPart;
        continue;
      }
      if (!institution && looksLikeLocation(line)) {
        location = line;
      }
    }

    if (!institution) {
      const candidate = contentLines.find(
        (line) =>
          !DEGREE_RE.test(line) &&
          !looksLikeLocation(line) &&
          !/gpa|cgpa|coursework|thesis|major/i.test(line)
      );
      if (candidate) institution = candidate;
    }

    if (!degree) {
      const candidate = contentLines.find((line) => line !== institution);
      if (candidate) degree = candidate;
    }

    if (!degree && !institution) continue;

    const details = contentLines
      .filter(
        (line) =>
          line !== degree &&
          line !== institution &&
          line !== location &&
          line !== contentLines[degreeLineIndex] &&
          line !== contentLines[institutionLineIndex] &&
          !looksLikeLocation(line)
      )
      .map(stripBullet)
      .filter(Boolean);

    results.push({
      institution: stripTrailingPunctuation(institution),
      degree: stripTrailingPunctuation(degree),
      field: stripTrailingPunctuation(field),
      location: stripTrailingPunctuation(location),
      startDate: readableDate(dateStart),
      endDate: isPresentDate(dateEnd) ? "" : readableDate(dateEnd),
      details: uniqueBy(details, (item) => item),
    });
  }

  return results.slice(0, 15);
}

function parseSkills(lines: string[], fullText: string): SkillGroup[] {
  const groups: SkillGroup[] = [];
  let currentCategory = "Skills";

  const addGroup = (category: string, rawItems: string[]) => {
    const items = uniqueBy(
      rawItems
        .map((item) => stripTrailingPunctuation(stripBullet(item)))
        .filter((item) => item.length > 0 && item.length <= 120),
      (item) => item
    );
    if (!items.length) return;
    const label = category.trim() || currentCategory;
    const existing = groups.find(
      (group) => group.category.toLowerCase() === label.toLowerCase()
    );
    if (existing) {
      existing.items = uniqueBy([...existing.items, ...items], (item) => item);
    } else {
      groups.push({ category: label, items });
    }
  };

  for (const raw of lines) {
    const line = stripBullet(raw).replace(/\s{3,}/g, "   ");
    if (!line) continue;
    const colon = line.indexOf(":");
    if (colon > 0 && colon <= 60) {
      const category = line.slice(0, colon).trim();
      const rest = line.slice(colon + 1).trim();
      if (/^[A-Za-z][A-Za-z &/+-]*$/.test(category)) {
        currentCategory = category;
        addGroup(category, rest.split(/[,;|•·]|\s{3,}/));
        continue;
      }
    }
    const items = line.split(/[,;|•·]|\s{3,}/);
    addGroup(currentCategory, items);
  }

  if (!groups.length) {
    const detected: string[] = [];
    for (const skill of KNOWN_SKILLS) {
      if (skill.length < 2) continue;
      const escaped = skill.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const pattern = new RegExp(
        `(^|[^A-Za-z0-9])${escaped}([^A-Za-z0-9]|$)`,
        "i"
      );
      if (pattern.test(fullText)) detected.push(skill);
    }
    if (detected.length) {
      groups.push({ category: "Skills", items: detected });
    }
  }

  return groups.slice(0, 15);
}

function parseProjects(lines: string[]): Project[] {
  const results: Project[] = [];
  const blocks = splitBlocks(lines);

  const pushProject = (block: string[]) => {
    const nonEmpty = block.map((line) => line.trim()).filter(Boolean);
    if (!nonEmpty.length) return;

    const titleLineIndex = nonEmpty.findIndex((line) => !isBulletLine(line));
    if (titleLineIndex < 0) return;
    const titleLine = nonEmpty[titleLineIndex];
    const link = titleLine.match(/https?:\/\/[^\s|,;]+/i)?.[0] ?? "";
    let titleText = titleLine.replace(link, "").trim();
    let tech: string[] = [];

    const parts = splitHeadingParts(titleText);
    const techPart = titleText.match(/^(.*?)\s*[|–—]\s*(?:tech(?:nologies)?\s*:\s*)?(.+)$/i);
    if (techPart) {
      titleText = techPart[1];
      tech = techPart[2]
        .split(/[,;·|]/)
        .map((item) => item.trim())
        .filter(Boolean);
    } else if (parts.length > 1) {
      titleText = parts[0];
      tech = parts.slice(1).join(", ").split(/[,;·]/).map((s) => s.trim()).filter(Boolean);
    }
    const labeledTech = titleText.match(/^(.*?)\s*Tech(?:nologies)?\s*:\s*(.+)$/i);
    if (labeledTech) {
      titleText = labeledTech[1];
      tech = labeledTech[2].split(/[,;·]/).map((s) => s.trim()).filter(Boolean);
    }

    const achievementLines = nonEmpty
      .slice(titleLineIndex + 1)
      .filter((line) => isBulletLine(line));
    const descriptionLines = nonEmpty
      .slice(titleLineIndex + 1)
      .filter((line) => !isBulletLine(line));

    const name = stripTrailingPunctuation(titleText);
    if (!name && !achievementLines.length) return;

    results.push({
      name,
      description: joinContinuation(descriptionLines).join(" ").trim(),
      tech: uniqueBy(tech, (item) => item),
      link,
      achievements: joinContinuation(achievementLines).map(stripBullet),
    });
  };

  for (const block of blocks) pushProject(block);

  if (!results.length && lines.some((line) => line.trim())) {
    pushProject(lines);
  }

  return results.slice(0, 20);
}

function parseCertifications(lines: string[]): Certification[] {
  const results: Certification[] = [];
  let pending = "";

  for (const raw of lines) {
    const line = stripBullet(raw);
    if (!line) continue;
    if (/^[a-z]/.test(line) && pending) {
      pending = `${pending} ${line}`;
      continue;
    }
    if (pending) {
      const cert = parseCertificationLine(pending);
      if (cert) results.push(cert);
    }
    pending = line;
  }
  if (pending) {
    const cert = parseCertificationLine(pending);
    if (cert) results.push(cert);
  }

  return uniqueBy(results, (cert) => `${cert.name}|${cert.issuer}|${cert.date}`).slice(
    0,
    25
  );
}

function parseCertificationLine(value: string): Certification | null {
  let text = value
    .replace(/^certifications?\s*:\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!text) return null;

  let date = "";
  const yearMatch = text.match(
    /\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)?\.?\s*\d{4}\b/i
  );
  if (yearMatch) {
    date = readableDate(yearMatch[0]);
    text = `${text.slice(0, yearMatch.index)} ${text.slice(
      (yearMatch.index ?? 0) + yearMatch[0].length
    )}`.replace(/\s+/g, " ").trim();
  }

  const parts = text.split(/\s+(?:—|–|\||-)\s+|\s+from\s+/i);
  const name = stripTrailingPunctuation(parts[0] ?? text);
  const issuer = stripTrailingPunctuation(parts.slice(1).join(", "));

  if (!name) return null;
  return { name, issuer, date };
}

function parseAwards(lines: string[]): string[] {
  const items = joinContinuation(
    lines.map(stripBullet).filter(Boolean)
  );
  return uniqueBy(
    items
      .flatMap((item) => item.split(/\s*;\s*/))
      .map(stripTrailingPunctuation)
      .filter(Boolean),
    (item) => item
  ).slice(0, 25);
}

function parseAdditional(section: SectionChunk): {
  title: string;
  items: string[];
} {
  const items = joinContinuation(
    section.lines.map(stripBullet).filter(Boolean)
  ).map(stripTrailingPunctuation);
  return {
    title: titleCaseIfShouting(section.title),
    items: uniqueBy(items, (item) => item).slice(0, 30),
  };
}

function parseHeader(preSectionLines: string[]) {
  const lines = preSectionLines
    .map((line) => line.trim())
    .filter((line) => line && !isPageNoise(line));
  const text = lines.join("\n");
  const contact = parseContact(text);

  let name = "";
  let nameIndex = -1;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].replace(/\s+/g, " ").trim();
    if (
      findEmail(line) ||
      findPhone(line) ||
      /https?:\/\/|www\.|linkedin\.com|github\.com/i.test(line)
    ) {
      continue;
    }
    if (looksLikeName(line)) {
      name = line;
      nameIndex = i;
      break;
    }
    if (line.includes("|")) {
      const [first, second] = line.split("|").map((part) => part.trim());
      if (looksLikeName(first)) {
        name = first;
        nameIndex = i;
        if (second) {
          const rest = line.slice(line.indexOf("|") + 1).trim();
          if (rest) {
            lines[i] = rest;
            nameIndex = i;
          }
        }
        break;
      }
    }
  }

  let title = "";
  const candidateIndexes = lines
    .map((line, index) => ({ line, index }))
    .filter(({ index }) => index !== nameIndex);
  for (const { line, index } of candidateIndexes) {
    if (index < nameIndex) continue;
    if (findEmail(line) || findPhone(line) || /https?:\/\/|www\./i.test(line)) {
      continue;
    }
    if (matchSection(line)) continue;
    if (line.length > 100) continue;
    if (headingWords(line) > 12) continue;
    if (looksLikeLocation(line) && !ROLE_WORDS.test(line)) continue;
    if (ROLE_WORDS.test(line) || isMostlyUppercase(line)) {
      title = line;
      break;
    }
  }

  let location = "";
  const remappedLines = lines.filter((line, index) => index !== nameIndex);
  for (const line of remappedLines) {
    if (line === title) continue;
    if (findEmail(line) || findPhone(line) || /https?:\/\//i.test(line)) {
      continue;
    }
    if (looksLikeLocation(line)) {
      location = line;
      break;
    }
  }

  const summaryCandidates = lines.filter((line, index) => {
    if (index === nameIndex) return false;
    if (line === title) return false;
    if (findEmail(line) || findPhone(line) || /https?:\/\/|www\./i.test(line)) {
      return false;
    }
    if (looksLikeLocation(line)) return false;
    return line.length > 40;
  });

  return {
    personal: {
      fullName: name,
      title,
      email: contact.email,
      phone: contact.phone,
      location,
      linkedin: contact.linkedin,
      github: contact.github,
      website: contact.website,
    },
    summaryFallback: summaryCandidates.join(" ").trim(),
    headerLines: lines,
  };
}

export function looksLikeResumeText(raw: string): boolean {
  const lines = splitIntoLines(raw).filter((line) => line.trim());
  if (!lines.length) return false;
  const headings = lines.filter((line) => matchSection(line)).length;
  const contacts =
    Number(Boolean(findEmail(raw))) +
    Number(Boolean(findPhone(raw))) +
    Number(/https?:\/\/|www\./i.test(raw));
  const bullets = lines.filter(isBulletLine).length;
  const dateRanges = lines.filter((line) => DATE_RANGE_RE.test(line)).length;
  return (
    headings >= 2 ||
    (contacts >= 1 && (headings >= 1 || bullets >= 3)) ||
    (bullets >= 4 && dateRanges >= 1) ||
    (lines.length > 12 && headings >= 1)
  );
}

export function parseResumeText(raw: string): ParsedResume {
  const text = cleanText(raw);
  const lines = splitIntoLines(text);
  const chunks: SectionChunk[] = [];
  let preSection: string[] = [];
  let current: SectionChunk | null = null;

  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const section = line.trim() ? matchSection(line) : null;
    if (section) {
      current = {
        key: section.key,
        title: section.title,
        known: section.key !== "additional",
        lines: [],
      };
      chunks.push(current);
      continue;
    }

    const previousImmediate = lines[index - 1] ?? "";
    let previousNonEmpty = "";
    for (let i = index - 1; i >= 0; i--) {
      if (lines[i].trim()) {
        previousNonEmpty = lines[i].trim();
        break;
      }
    }
    let nextNonEmpty = "";
    for (let i = index + 1; i < lines.length; i++) {
      if (lines[i].trim()) {
        nextNonEmpty = lines[i].trim();
        break;
      }
    }
    const custom =
      line.trim()
        ? matchCustomSection(
            line,
            previousNonEmpty,
            nextNonEmpty,
            !previousImmediate.trim()
          )
        : null;
    if (custom) {
      current = {
        key: "additional",
        title: custom.title,
        known: false,
        lines: [],
      };
      chunks.push(current);
      continue;
    }

    if (current) {
      current.lines.push(line);
    } else {
      preSection.push(line);
    }
  }

  const header = parseHeader(preSection);
  const fullText = lines.join("\n");
  const resume = createEmptyResume();
  resume.personal = header.personal;
  resume.summary =
    mergeSectionLines(chunks, "summary")
      .join("\n")
      .replace(/\n{2,}/g, "\n")
      .trim() || header.summaryFallback;

  resume.experience = parseExperience(mergeSectionLines(chunks, "experience"));
  resume.education = parseEducation(mergeSectionLines(chunks, "education"));
  resume.skills = parseSkills(
    mergeSectionLines(chunks, "skills"),
    fullText
  );
  resume.projects = parseProjects(mergeSectionLines(chunks, "projects"));
  resume.certifications = parseCertifications(
    mergeSectionLines(chunks, "certifications")
  );
  resume.awards = parseAwards(mergeSectionLines(chunks, "awards"));

  const additionalChunks = chunks.filter(
    (chunk) =>
      chunk.key === "additional" &&
      (chunk.lines.some((line) => line.trim()) || chunk.title)
  );
  resume.additionalSections = uniqueBy(
    additionalChunks
      .map(parseAdditional)
      .filter((section) => section.title && section.items.length),
    (section) => section.title
  ).slice(0, 12);

  const detectedSections: string[] = [];
  if (resume.summary) detectedSections.push("summary");
  if (resume.experience.length) detectedSections.push("experience");
  if (resume.education.length) detectedSections.push("education");
  if (resume.skills.length) detectedSections.push("skills");
  if (resume.projects.length) detectedSections.push("projects");
  if (resume.certifications.length) detectedSections.push("certifications");
  if (resume.awards.length) detectedSections.push("awards");
  for (const section of resume.additionalSections) {
    detectedSections.push(section.title.toLowerCase());
  }

  const parsed = resumeSchema.parse(resume);
  const hasUsableContent = Boolean(
    parsed.personal.fullName ||
      parsed.personal.email ||
      parsed.personal.phone ||
      parsed.summary ||
      parsed.experience.length ||
      parsed.education.length ||
      parsed.skills.length ||
      parsed.projects.length
  );

  return {
    resume: parsed,
    detectedSections,
    looksLikeResume: looksLikeResumeText(text),
    hasUsableContent,
  };
}

export function createDraftFromPastedInformation(raw: string): ParsedResume {
  const text = cleanText(raw);
  const lines = splitIntoLines(text).filter((line) => line.trim());
  const header = parseHeader(lines);
  const draft = createEmptyResume();
  draft.personal = header.personal;
  if (!draft.personal.fullName) {
    const nameLike = lines.find((line) => looksLikeName(line));
    if (nameLike) draft.personal.fullName = nameLike;
  }
  if (!draft.personal.title) {
    const roleLike = lines.find((line) => looksLikeRole(line));
    if (roleLike) draft.personal.title = roleLike;
  }
  draft.skills = parseSkills([], text);
  draft.summary = text
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n\n")
    .slice(0, 5000);

  return {
    resume: resumeSchema.parse(draft),
    detectedSections: draft.skills.length ? ["summary", "skills"] : ["summary"],
    looksLikeResume: false,
    hasUsableContent: Boolean(
      draft.personal.fullName ||
        draft.personal.email ||
        draft.personal.phone ||
        draft.summary
    ),
  };
}

export function parseUploadedText(raw: string): ParsedResume {
  if (looksLikeResumeText(raw)) {
    return parseResumeText(raw);
  }
  const parsed = parseResumeText(raw);
  if (parsed.hasUsableContent && parsed.resume.experience.length + parsed.resume.education.length > 0) {
    return parsed;
  }
  return createDraftFromPastedInformation(raw);
}

