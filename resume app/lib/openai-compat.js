// OpenAI-compatible provider (e.g. APInex serving DeepSeek V4 Flash).
// Uses the standard /chat/completions endpoint over fetch, no extra SDK.

export const OPENAI_BASE_URL = (process.env.OPENAI_BASE_URL || "https://api.apinex.bond/v1").replace(/\/+$/, "");
export const OPENAI_MODEL = process.env.OPENAI_MODEL || "deepseek-v4-flash";

function httpError(status, message) {
  const e = new Error(message);
  e.status = status;
  return e;
}

async function post(key, body, signal) {
  let res;
  try {
    res = await fetch(`${OPENAI_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw httpError(502, `Could not reach the AI service (${new URL(OPENAI_BASE_URL).host}).`);
  }
  if (res.ok) return res;

  let detail = "";
  try {
    const j = await res.json();
    detail = j.error?.message || j.message || "";
  } catch { /* not JSON */ }
  if (res.status === 401 || res.status === 403) throw httpError(401, "Invalid API key. Check the key in Settings.");
  if (res.status === 402 || /balance|insufficient|quota|credit/i.test(detail))
    throw httpError(402, "Your AI provider balance is too low. Top up your account or use another key.");
  if (res.status === 429) throw httpError(429, "Rate limited by the AI provider. Try again in a moment.");
  if (res.status === 404 && /model/i.test(detail)) throw httpError(400, `Model not found: ${body.model}. Check the model name in Settings.`);
  throw httpError(res.status >= 500 ? 502 : res.status, detail || `AI provider error (${res.status}).`);
}

/** Pull the first JSON object out of a reply (tolerates ```json fences and stray text). */
function extractJson(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const raw = fenced ? fenced[1] : text;
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start === -1 || end <= start) throw new Error("no JSON object");
  return JSON.parse(raw.slice(start, end + 1));
}

/** Coerce a parsed value to the JSON schema: fill missing fields, fix types, drop extras. */
function conform(schema, v) {
  switch (schema.type) {
    case "object": {
      const src = v && typeof v === "object" && !Array.isArray(v) ? v : {};
      return Object.fromEntries(Object.entries(schema.properties).map(([k, s]) => [k, conform(s, src[k])]));
    }
    case "array":
      return Array.isArray(v) ? v.map((x) => conform(schema.items, x)) : [];
    case "integer":
    case "number": {
      const n = Number(v);
      return Number.isFinite(n) ? (schema.type === "integer" ? Math.round(n) : n) : 0;
    }
    default:
      return v == null ? "" : typeof v === "string" ? v : Array.isArray(v) ? v.join(", ") : String(v);
  }
}

/**
 * JSON reply matching `schema`. The provider can't enforce a schema, so we ask for JSON
 * mode, describe the schema in the prompt, then validate and repair the result ourselves.
 */
export async function oaStructured({ key, model }, { system, userText, schema, effort = "medium", maxTokens = 8000 }) {
  const messages = [
    { role: "system", content: `${system}\n\nReply with ONLY a JSON object (no markdown, no commentary) that matches this JSON Schema exactly:\n${JSON.stringify(schema)}` },
    { role: "user", content: userText },
  ];
  const body = { model, messages, max_tokens: maxTokens, reasoning_effort: effort, response_format: { type: "json_object" } };

  let lastErr;
  for (let attempt = 0; attempt < 2; attempt++) {
    let res;
    try {
      res = await post(key, body);
    } catch (err) {
      // some upstreams reject json mode; retry once without it
      if (err.status === 400 && /response_format|json/i.test(err.message) && body.response_format) {
        delete body.response_format;
        res = await post(key, body);
      } else throw err;
    }
    const data = await res.json();
    const choice = data.choices?.[0];
    if (choice?.finish_reason === "content_filter") throw httpError(422, "The AI declined this request. Try rephrasing it.");
    try {
      return conform(schema, extractJson(choice?.message?.content || ""));
    } catch (err) {
      lastErr = err; // malformed or cut-off JSON: try once more
    }
  }
  throw httpError(502, `The AI returned an incomplete resume (${lastErr?.message || "bad JSON"}). Please try again.`);
}

/** Streamed text reply via server-sent events. Calls onText(chunk) as text arrives. */
export async function oaStream({ key, model }, { system, messages, onText, effort = "low", maxTokens = 4000, signal }) {
  const res = await post(key, {
    model,
    messages: [{ role: "system", content: system }, ...messages],
    max_tokens: maxTokens,
    reasoning_effort: effort,
    stream: true,
  }, signal);

  const decoder = new TextDecoder();
  let buf = "";
  let gotText = false;
  for await (const chunk of res.body) {
    buf += decoder.decode(chunk, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop();
    for (const line of lines) {
      const s = line.trim();
      if (!s.startsWith("data:")) continue;
      const payload = s.slice(5).trim();
      if (payload === "[DONE]") return;
      let evt;
      try { evt = JSON.parse(payload); } catch { continue; }
      if (evt.error) throw httpError(502, evt.error.message || "AI provider error.");
      const choice = evt.choices?.[0];
      const text = choice?.delta?.content; // reasoning_content (thinking) is deliberately not shown
      if (text) { gotText = true; onText(text); }
      if (choice?.finish_reason === "content_filter" && !gotText) throw httpError(422, "The AI declined this request. Try rephrasing it.");
    }
  }
}

/** Extract plain text from a PDF buffer (DeepSeek can't read PDFs directly). */
export async function pdfToText(buffer) {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
  const doc = await pdfjs.getDocument({ data: new Uint8Array(buffer), isEvalSupported: false, useSystemFonts: true }).promise;
  const pages = [];
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i);
    const tc = await page.getTextContent();
    let line = "", out = "", lastY = null;
    for (const it of tc.items) {
      const y = it.transform?.[5];
      if (lastY !== null && Math.abs(y - lastY) > 2) { out += line.trim() + "\n"; line = ""; }
      line += it.str + (it.hasEOL ? "\n" : " ");
      lastY = y;
    }
    pages.push(out + line.trim());
  }
  await doc.destroy();
  return pages.join("\n\n").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}
