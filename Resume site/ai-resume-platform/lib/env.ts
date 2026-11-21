/**
 * Safe environment helpers. Never log or return secret values.
 */

const PLACEHOLDER_RE =
  /^(paste_your|your[_-]?|xxx+|changeme|todo|replace|<.*>|\[.*\])$/i;

/**
 * Returns true only when the env var is present, non-empty, and not a known placeholder.
 */
export function isEnvConfigured(name: string): boolean {
  const raw = process.env[name];
  if (raw === undefined || raw === null) return false;
  const value = String(raw).trim();
  if (!value) return false;
  if (PLACEHOLDER_RE.test(value)) return false;
  if (/^PASTE_YOUR/i.test(value)) return false;
  if (/^<.*>$/.test(value)) return false;
  return true;
}

export function getEnv(name: string): string | undefined {
  if (!isEnvConfigured(name)) return undefined;
  return process.env[name]!.trim();
}

/**
 * Provider readiness for health + setup banner.
 * LLM features use Azure Foundry only (not Gemini).
 */
export function healthStatus() {
  const azureFoundry =
    isEnvConfigured("AZURE_FOUNDRY_API_KEY") &&
    isEnvConfigured("AZURE_FOUNDRY_BASE_URL") &&
    isEnvConfigured("AZURE_FOUNDRY_MODEL");

  return {
    /** @deprecated Gemini is no longer used — alias of azureFoundry for older clients */
    gemini: azureFoundry,
    /** Primary LLM (resume enhance, classify, live-search answers) */
    llm: azureFoundry,
    azureFoundry,
    adzuna:
      isEnvConfigured("ADZUNA_APP_ID") && isEnvConfigured("ADZUNA_APP_KEY"),
    exa: isEnvConfigured("EXA_API_KEY"),
  };
}
