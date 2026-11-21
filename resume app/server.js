import "dotenv/config";
import express from "express";
import multer from "multer";
import mammoth from "mammoth";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { getClient, askStructured, streamText, toHttpError, MODEL } from "./lib/llm.js";
import { buildDemoResume, demoChatReply } from "./lib/demo.js";
import { aiLimit, LIMITS } from "./lib/limits.js";
import { OPENAI_BASE_URL, OPENAI_MODEL, oaStructured, oaStream, pdfToText } from "./lib/openai-compat.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const jobs = JSON.parse(readFileSync(path.join(__dirname, "data", "jobs.json"), "utf8"));

const app = express();
app.set("trust proxy", 1); // real visitor IP behind Cloud Run / a reverse proxy (used by rate limits)
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });

app.use(express.json({ limit: "1mb" }));
app.use(express.static(path.join(__dirname, "public")));

const serverKeyAllowed = !LIMITS.requireUserKey;

// ---------- AI provider selection ----------
// "anthropic" = Claude via the Anthropic API. "openai" = any OpenAI-compatible API at
// OPENAI_BASE_URL (default: APInex, serving DeepSeek). The base URL is fixed server-side so
// visitors can't point the server at arbitrary hosts.
const SERVER_KEYS = { anthropic: process.env.ANTHROPIC_API_KEY || "", openai: process.env.OPENAI_API_KEY || "" };
const DEFAULT_PROVIDER = ["anthropic", "openai"].includes(process.env.AI_PROVIDER)
  ? process.env.AI_PROVIDER
  : SERVER_KEYS.openai && !SERVER_KEYS.anthropic ? "openai" : "anthropic";

function resolveAI(req, _res, next) {
  const userKey = (req.get("x-api-key") || "").trim();
  let provider = (req.get("x-provider") || "").toLowerCase();
  if (!["anthropic", "openai"].includes(provider)) provider = userKey.startsWith("sk-apx") ? "openai" : DEFAULT_PROVIDER;
  const key = userKey || (serverKeyAllowed ? SERVER_KEYS[provider] : "");
  const wanted = (req.get("x-model") || "").trim();
  const model = provider === "openai" ? (/^[\w.:/-]{1,80}$/.test(wanted) ? wanted : OPENAI_MODEL) : MODEL;
  req.ai = { provider, key, model, usingServerKey: !userKey && Boolean(key) };
  next();
}

// ---------- Config & data ----------
app.get("/api/config", (_req, res) => {
  res.json({
    defaultProvider: DEFAULT_PROVIDER,
    serverKeys: {
      anthropic: Boolean(SERVER_KEYS.anthropic) && serverKeyAllowed,
      openai: Boolean(SERVER_KEYS.openai) && serverKeyAllowed,
    },
    requireUserKey: LIMITS.requireUserKey,
    models: { anthropic: MODEL, openai: OPENAI_MODEL },
    openaiHost: new URL(OPENAI_BASE_URL).host,
    limits: { resumePerHour: LIMITS.resumePerHour, chatPerHour: LIMITS.chatPerHour },
  });
});

app.get("/api/jobs", (_req, res) => res.json(jobs));

// ---------- Resume generation ----------
const str = { type: "string" };
const strArr = { type: "array", items: str };
const obj = (properties) => ({ type: "object", properties, required: Object.keys(properties), additionalProperties: false });

// The API constrains Claude's reply to exactly this shape (structured outputs)
const RESUME_SCHEMA = obj({
  name: str,
  title: str,
  contact: obj({ email: str, phone: str, location: str, linkedin: str, github: str, portfolio: str }),
  summary: str,
  skills: { type: "array", items: obj({ category: str, items: strArr }) },
  experience: { type: "array", items: obj({ role: str, company: str, location: str, start: str, end: str, bullets: strArr }) },
  projects: { type: "array", items: obj({ name: str, tech: str, bullets: strArr }) },
  education: { type: "array", items: obj({ degree: str, institution: str, year: str, details: str }) },
  certifications: strArr,
  achievements: strArr,
  ats: obj({ score: { type: "integer" }, matchedKeywords: strArr, missingKeywords: strArr, tips: strArr }),
});

const RESUME_SYSTEM = `You are an expert resume writer and ATS (Applicant Tracking System) specialist.
Rewrite the candidate's information into a modern, ATS-friendly resume.

Rules:
- Use strong action verbs and quantified impact (numbers, %, scale) wherever the source supports it. Never invent employers, degrees, dates or certifications that are not in the input; you may sharpen wording and infer reasonable impact phrasing.
- Skills may be written as free text ("I know Python and SQL..."). Extract clean, individual skills and group them into 2-5 sensible categories.
- If the candidate has little experience, lead with projects and skills.
- Weave in relevant keywords for the target role naturally.
- Keep bullets to one line where possible (max ~22 words), 3-5 bullets per role.
- Use empty strings or empty arrays for anything unknown.
- "ats.score" is your 0-100 estimate of how well the final resume would parse and match the target role. "ats.tips" are 2-4 short, specific improvements.`;

async function fileToContent(file, provider) {
  if (!file) return null;
  const name = file.originalname.toLowerCase();
  if (file.mimetype === "application/pdf" || name.endsWith(".pdf")) {
    if (provider === "openai") {
      // text-only models: extract the PDF's text on the server
      const text = await pdfToText(file.buffer);
      if (text.length < 40) {
        const e = new Error("Couldn't read text from this PDF (it may be a scanned image). Try a DOCX or text version.");
        e.status = 400;
        throw e;
      }
      return { type: "text", text: `OLD RESUME (from PDF):\n${text}` };
    }
    // Claude reads PDFs natively (text + layout)
    return {
      type: "document",
      source: { type: "base64", media_type: "application/pdf", data: file.buffer.toString("base64") },
    };
  }
  if (name.endsWith(".docx")) {
    const { value } = await mammoth.extractRawText({ buffer: file.buffer });
    return { type: "text", text: `OLD RESUME (from DOCX):\n${value}` };
  }
  if (name.endsWith(".txt") || name.endsWith(".md")) {
    return { type: "text", text: `OLD RESUME:\n${file.buffer.toString("utf8")}` };
  }
  const e = new Error("Unsupported file type. Upload a PDF, DOCX or TXT resume.");
  e.status = 400;
  throw e;
}

// One log line per AI request: provider, model, outcome and timing only.
// Never log keys or what people typed (resumes hold personal data).
function logAI(kind, ai, started, outcome) {
  console.log(`[ai] ${kind} provider=${ai.provider} model=${ai.model} key=${ai.key ? (ai.usingServerKey ? "server" : "visitor") : "none"} ${outcome} ${Date.now() - started}ms`);
}

app.post("/api/resume", upload.single("resume"), resolveAI, aiLimit("resume"), async (req, res) => {
  const t0 = Date.now();
  try {
    const f = req.body || {};
    const { ai } = req;

    if (!ai.key) {
      if (req.file) {
        return res.status(400).json({
          error: "Uploading an old resume needs an API key. Add one in Settings, or use Enter skills for a demo.",
        });
      }
      return res.json({ resume: buildDemoResume(f), demo: true });
    }

    const details = `CANDIDATE DETAILS (from form):
Name: ${f.name || ""}
Email: ${f.email || ""}
Phone: ${f.phone || ""}
Location: ${f.location || ""}
LinkedIn: ${f.linkedin || ""}
GitHub/Portfolio: ${f.github || ""}
Target role: ${f.targetRole || ""}
Experience level: ${f.level || ""}
Skills: ${f.skills || ""}
Experience / projects / education notes:
${f.notes || ""}
${f.jobDescription ? `\nTARGET JOB DESCRIPTION (tailor keywords to this):\n${f.jobDescription}` : ""}`;

    const fileBlock = await fileToContent(req.file, ai.provider);
    const instruction = `${details}\n\n${fileBlock ? "Use the old resume as the main source; form fields override it where given." : ""}\nWrite the resume now.`;

    let resume;
    if (ai.provider === "openai") {
      resume = await oaStructured(ai, {
        system: RESUME_SYSTEM,
        userText: fileBlock ? `${fileBlock.text}\n\n${instruction}` : instruction,
        schema: RESUME_SCHEMA,
        effort: "medium",
      });
    } else {
      const content = fileBlock ? [fileBlock, { type: "text", text: instruction }] : [{ type: "text", text: instruction }];
      resume = await askStructured(getClient(ai.key), {
        system: RESUME_SYSTEM,
        messages: [{ role: "user", content }],
        schema: RESUME_SCHEMA,
        effort: "medium",
      });
    }
    resume.ats.score = Math.max(0, Math.min(100, Math.round(resume.ats.score)));
    logAI("resume", ai, t0, `ok file=${req.file ? "yes" : "no"} experience=${resume.experience.length} skills=${resume.skills.length} ats=${resume.ats.score}`);
    res.json({ resume, demo: false });
  } catch (err) {
    const { status, message } = toHttpError(err);
    if (req.ai?.key) logAI("resume", req.ai, t0, `error status=${status} msg="${message}"`);
    res.status(status).json({ error: message });
  }
});

// ---------- Career chatbot (streamed) ----------
const CHAT_SYSTEM = `You are "CareerPilot", a friendly, sharp career advisor inside a job-trends portal for job seekers (freshers and experienced).
Help users decide which domain/role to pursue using the market snapshot below plus your general knowledge.
- Be concise: short paragraphs, bullets, and small markdown tables when comparing.
- Salaries are in INR LPA (lakhs per annum) unless the user asks otherwise.
- When you quote numbers from the snapshot, say they are from the portal's indicative snapshot.
- Give practical next steps (skills to learn, projects to build, certifications) when relevant.

MARKET SNAPSHOT (JSON):
${JSON.stringify(jobs)}`;

// Reply format: newline-delimited JSON, one object per line:
//   {"t":"text chunk"} ... then {"done":true,"demo":false}  or  {"error":"message"}
app.post("/api/chat", resolveAI, aiLimit("chat"), async (req, res) => {
  const history = Array.isArray(req.body?.messages) ? req.body.messages.slice(-20) : [];
  const messages = history
    .filter((m) => (m.role === "user" || m.role === "assistant") && typeof m.content === "string" && m.content.trim())
    .map((m) => ({ role: m.role, content: m.content.slice(0, 4000) }));
  if (!messages.length || messages[messages.length - 1].role !== "user") {
    return res.status(400).json({ error: "Send at least one user message." });
  }

  const send = (o) => res.write(JSON.stringify(o) + "\n");
  const startStream = () => {
    res.status(200).set({ "Content-Type": "application/x-ndjson; charset=utf-8", "Cache-Control": "no-cache", "X-Accel-Buffering": "no" });
    res.flushHeaders();
  };

  const { ai } = req;
  if (!ai.key) {
    startStream();
    send({ t: demoChatReply(messages[messages.length - 1].content, jobs) });
    send({ done: true, demo: true });
    return res.end();
  }

  // stop generating (and billing) if the visitor closes the page
  const abort = new AbortController();
  res.on("close", () => { if (!res.writableEnded) abort.abort(); });

  let started = false;
  let chars = 0, chunks = 0;
  const t0 = Date.now();
  let firstMs = 0;
  const onText = (t) => {
    if (!started) { startStream(); started = true; firstMs = Date.now() - t0; }
    chars += t.length; chunks++;
    send({ t });
  };
  try {
    if (ai.provider === "openai") {
      await oaStream(ai, { system: CHAT_SYSTEM, messages, onText, signal: abort.signal });
    } else {
      await streamText(getClient(ai.key), { system: CHAT_SYSTEM, messages, signal: abort.signal, onText });
    }
    if (!started) startStream();
    logAI("chat", ai, t0, `ok chunks=${chunks} chars=${chars} first_text=${firstMs}ms`);
    send({ done: true, demo: false });
    res.end();
  } catch (err) {
    if (abort.signal.aborted) return logAI("chat", ai, t0, "aborted by visitor");
    const { status, message } = toHttpError(err);
    logAI("chat", ai, t0, `error status=${status} msg="${message}" chunks_sent=${chunks}`);
    if (!started) return res.status(status).json({ error: message });
    send({ error: message });
    res.end();
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`CareerForge AI running on http://localhost:${PORT}`));
