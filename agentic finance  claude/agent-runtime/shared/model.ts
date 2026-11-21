// Model configuration through environment variables; Vercel AI Gateway model identifiers by default.
import { defineDynamic } from "eve/models";

export const DEFAULT_MODEL = "anthropic/claude-sonnet-5";

export function configuredModel(envVar: string) {
  return defineDynamic(() => process.env[envVar] || process.env.SPREADLENS_EVE_MODEL || DEFAULT_MODEL);
}
