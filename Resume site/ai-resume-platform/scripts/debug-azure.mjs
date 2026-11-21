// TEMPORARY diagnostic — probe auth variations. Delete before commit.
import fs from "node:fs";

function loadEnv(path) {
  const env = {};
  const text = fs.readFileSync(path, "utf8");
  for (const line of text.split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!m) continue;
    env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
  return env;
}

const env = loadEnv(new URL("../.env.local", import.meta.url));
const base = (env.AZURE_FOUNDRY_BASE_URL || "").replace(/\/+$/, "");
const key = env.AZURE_FOUNDRY_API_KEY || "";
const model = env.AZURE_FOUNDRY_MODEL || "";

async function call(label, url, headers, body) {
  const t0 = Date.now();
  try {
    const res = await fetch(url, {
      method: body ? "POST" : "GET",
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(120_000),
    });
    const text = await res.text();
    console.log(`\n=== [${label}] status=${res.status} ms=${Date.now() - t0}`);
    console.log(text.slice(0, 1200));
  } catch (e) {
    console.log(`\n=== [${label}] THREW ms=${Date.now() - t0}:`, e?.message);
  }
}

const bearerHeaders = {
  "Content-Type": "application/json",
  Authorization: `Bearer ${key}`,
};
const apiKeyHeaders = {
  "Content-Type": "application/json",
  "api-key": key,
};

// A: models list via Bearer
await call("GET models bearer", `${base}/models`, bearerHeaders);

// B: models list via api-key header
await call("GET models api-key", `${base}/models`, apiKeyHeaders);

// C: chat completions via api-key header
await call("chat api-key", `${base}/chat/completions`, apiKeyHeaders, {
  model,
  messages: [{ role: "user", content: "Reply with exactly: OK" }],
});

// D: legacy deployment-style URL (api-version query)
const host = new URL(base).origin;
await call(
  "legacy deployments URL",
  `${host}/openai/deployments/${model}/chat/completions?api-version=2024-10-21`,
  { ...bearerHeaders },
  { messages: [{ role: "user", content: "Reply with exactly: OK" }] }
);
