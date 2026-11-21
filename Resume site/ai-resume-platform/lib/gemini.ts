/**
 * AI helpers for ResumeAI.
 *
 * Historically backed by Google Gemini. The app now uses Azure Foundry Grok
 * (AZURE_FOUNDRY_*) exclusively — no GEMINI_API_KEY required.
 *
 * This module re-exports the same function names so existing imports keep working.
 */

export {
  enhanceResume,
  classifyJobTitles,
  generateTrendBlurb,
  isAzureFoundryConfigured,
} from "./azureFoundryModel";
