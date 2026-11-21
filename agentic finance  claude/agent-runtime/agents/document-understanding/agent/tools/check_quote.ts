import { defineTool } from "eve/tools";
import { z } from "zod";
import { enginePost } from "../../../../shared/engine";
import { scopeField } from "../../../../shared/scope";

export default defineTool({
  description:
    "Check whether an exact evidence quote occurs in the uploaded document's extracted text. Use before citing evidence.",
  inputSchema: z.object({
    tool_scope: scopeField,
    document_version_id: z.string().min(8),
    quote: z.string().min(2).max(300),
  }),
  outputSchema: z.object({ found: z.boolean() }),
  label: { start: () => "Verify evidence quote" },
  async execute({ tool_scope, document_version_id, quote }) {
    return (await enginePost("/internal/tools/quotes/check", tool_scope, { document_version_id, quote })) as { found: boolean };
  },
});
