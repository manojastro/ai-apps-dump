import Anthropic from "@anthropic-ai/sdk";
import { betaJSONSchemaOutputFormat } from "@anthropic-ai/sdk/helpers/beta/json-schema";

export const MODEL = process.env.ANTHROPIC_MODEL || "claude-opus-5-5";

// Server-side refusal fallbacks (beta): if the model declines, the API retries on a
// suitable model. Some accounts may reject the beta; we then retry without it.
const FALLBACK = { betas: ["server-side-fallback-2026-07-01"], fallbacks: "default" };
const isFallbackRejection = (err) =>
  err instanceof Anthropic.BadRequestError && /fallback|server-side-fallback/i.test(err.message || "");

/** Build a client from the visitor's key, or the server's .env key when allowed. */
export function getClient(userKey, allowServerKey = true) {
  const apiKey = (userKey && userKey.trim()) || (allowServerKey ? process.env.ANTHROPIC_API_KEY : "");
  if (!apiKey) return null;
  return new Anthropic({ apiKey });
}

function refusalError(message) {
  const e = new Error(message?.stop_details?.explanation || "The AI declined this request. Try rephrasing it.");
  e.status = 422;
  return e;
}

/**
 * Structured output: the API constrains the reply to `schema`, so we get valid JSON
 * that matches the resume shape instead of hunting for JSON in free text.
 */
export async function askStructured(client, { system, messages, schema, maxTokens = 16000, effort = "medium" }) {
  const params = {
    model: MODEL,
    max_tokens: maxTokens,
    system,
    messages,
    output_config: { effort, format: betaJSONSchemaOutputFormat(schema) },
  };

  let response;
  try {
    response = await client.beta.messages.parse({ ...params, ...FALLBACK });
  } catch (err) {
    if (!isFallbackRejection(err)) throw err;
    response = await client.beta.messages.parse(params);
  }

  if (response.stop_reason === "refusal") throw refusalError(response);
  if (response.stop_reason === "max_tokens" || !response.parsed_output) {
    const e = new Error("The AI's answer was cut off before it finished. Please try again.");
    e.status = 502;
    throw e;
  }
  return response.parsed_output;
}

/**
 * Streamed text reply. Calls onText(chunk) as words arrive; resolves when finished.
 * With refusal fallbacks the retry happens on the same stream, so already-sent text stays
 * valid and the stream simply continues.
 */
export async function streamText(client, { system, messages, onText, maxTokens = 4000, effort = "low", signal }) {
  const params = { model: MODEL, max_tokens: maxTokens, system, messages, output_config: { effort } };

  const run = async (extra) => {
    const stream = client.beta.messages.stream({ ...params, ...extra }, { signal });
    for await (const event of stream) {
      if (event.type === "content_block_delta" && event.delta.type === "text_delta") onText(event.delta.text);
    }
    return stream.finalMessage();
  };

  let message;
  try {
    message = await run(FALLBACK);
  } catch (err) {
    // the beta is rejected before any text is produced, so retrying is safe
    if (!isFallbackRejection(err)) throw err;
    message = await run({});
  }
  if (message.stop_reason === "refusal") throw refusalError(message);
  return message;
}

/** Map SDK errors to friendly HTTP responses. */
export function toHttpError(err) {
  if (err instanceof Anthropic.AuthenticationError)
    return { status: 401, message: "Invalid API key. Check the key in Settings." };
  if (err instanceof Anthropic.RateLimitError)
    return { status: 429, message: "Rate limited by the AI provider. Try again in a moment." };
  if (err instanceof Anthropic.APIConnectionError)
    return { status: 502, message: "Could not reach the AI service. Check your network." };
  if (err instanceof Anthropic.APIError)
    return { status: err.status || 500, message: err.message };
  return { status: err.status || 500, message: err.message || "Unexpected error" };
}
