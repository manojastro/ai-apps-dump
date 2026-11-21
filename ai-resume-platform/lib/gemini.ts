import { GoogleGenerativeAI } from "@google/generative-ai";
import { stripJsonFences } from "./utils";
import type { ResumeData } from "./resumeSchema";
import { JOB_DOMAINS } from "./domains";

function getClient() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error("GEMINI_API_KEY is not configured");
  }
  return new GoogleGenerativeAI(apiKey);
}

function getModel(modelEnv?: string) {
  const client = getClient();
  const modelName =
    modelEnv || process.env.GEMINI_MODEL || "gemini-2.5-flash";
  return client.getGenerativeModel({ model: modelName });
}

const RESUME_SCHEMA_PROMPT = `You are an expert resume writer for Indian job seekers. Return ONLY valid JSON matching this exact schema — no prose, no markdown fences:

{
  "personalInfo": { "fullName": "", "email": "", "phone": "", "location": "", "linkedin": "", "portfolio": "" },
  "targetRole": "",
  "summary": "",
  "experience": [
    { "company": "", "role": "", "location": "", "startDate": "", "endDate": "", "current": false, "bullets": [""] }
  ],
  "education": [
    { "institution": "", "degree": "", "field": "", "startDate": "", "endDate": "" }
  ],
  "skills": { "technical": [""], "soft": [""] },
  "certifications": [{ "name": "", "issuer": "", "date": "" }],
  "projects": [{ "name": "", "description": "", "tech": [""], "link": "" }]
}

Rules:
- Use strong action verbs and active voice
- Quantify impact ONLY with numbers the user actually provided — never invent metrics, employers, titles, or dates
- Trim buzzwords and filler; keep each bullet to one line where possible
- If a target job description was supplied, mirror its real terminology where truthfully applicable
- Never invent skills, experience, or credentials the user did not claim`;

export async function enhanceResume(params: {
  rawText: string;
  targetJobDescription?: string;
  existingResumeJson?: ResumeData;
}): Promise<ResumeData> {
  const { rawText, targetJobDescription, existingResumeJson } = params;
  const client = getClient();
  const modelName = process.env.GEMINI_MODEL || "gemini-2.5-flash";
  const model = client.getGenerativeModel({
    model: modelName,
    systemInstruction: RESUME_SCHEMA_PROMPT,
    generationConfig: {
      temperature: 0.3,
      responseMimeType: "application/json",
    },
  });

  let userPrompt = `Structure and enhance this resume content:\n\n${rawText}`;
  if (targetJobDescription) {
    userPrompt += `\n\nTarget job description (tailor phrasing and keywords truthfully):\n${targetJobDescription}`;
  }
  if (existingResumeJson) {
    userPrompt += `\n\nExisting structured data to merge/improve:\n${JSON.stringify(existingResumeJson)}`;
  }

  const result = await model.generateContent(userPrompt);

  const text = result.response.text();
  const cleaned = stripJsonFences(text);
  return JSON.parse(cleaned) as ResumeData;
}

export async function classifyJobTitles(
  titles: string[]
): Promise<Record<string, string>> {
  const domainList = JOB_DOMAINS.map((d) => `${d.id}: ${d.name}`).join("\n");

  const prompt = `Classify each job title into exactly one domain ID from this list:
${domainList}

Job titles (one per line):
${titles.map((t, i) => `${i + 1}. ${t}`).join("\n")}

Return ONLY valid JSON as an object mapping line number (as string "1", "2", etc.) to domain ID. Example: {"1":"ai-ml","2":"fullstack"}`;

  const client = getClient();
  const classifierModel =
    process.env.GEMINI_CLASSIFIER_MODEL || "gemini-2.5-flash-lite";
  const classifier = client.getGenerativeModel({
    model: classifierModel,
    generationConfig: {
      temperature: 0.1,
      responseMimeType: "application/json",
    },
  });

  const result = await classifier.generateContent(prompt);

  const text = result.response.text();
  const cleaned = stripJsonFences(text);
  const mapping = JSON.parse(cleaned) as Record<string, string>;

  const titleToDomain: Record<string, string> = {};
  titles.forEach((title, i) => {
    titleToDomain[title] = mapping[String(i + 1)] || "fullstack";
  });
  return titleToDomain;
}

export async function generateTrendBlurb(
  domainName: string,
  openingCount: number
): Promise<string> {
  const model = getModel(process.env.GEMINI_CLASSIFIER_MODEL);

  const prompt = `Write a single concise sentence (max 15 words) explaining why "${domainName}" is trending in the Indian job market. Context: there are ${openingCount} current openings. Do NOT invent specific numbers beyond what was given. Return only the sentence, no quotes.`;

  const result = await model.generateContent(prompt);
  return result.response.text().trim();
}