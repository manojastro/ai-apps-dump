import { defineAgent } from "eve";
import { configuredModel } from "../../../shared/model";

// Model: $SPREADLENS_EVE_MODEL_DOCUMENT_UNDERSTANDING or $SPREADLENS_EVE_MODEL (Vercel AI Gateway id); default anthropic/claude-sonnet-5.
// defaultTools: false -> no shell, file, web or sub-agent tools: these agents read untrusted documents.
export default defineAgent({
  defaultTools: false,
  model: configuredModel("SPREADLENS_EVE_MODEL_DOCUMENT_UNDERSTANDING"),
});
