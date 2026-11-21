import { defineTool } from "eve/tools";
import { z } from "zod";
import { engineGet } from "../../../../shared/engine";
import { scopeField } from "../../../../shared/scope";

export default defineTool({
  description: "Read a supporting note (e.g. note 8 Borrowings) of the document a row came from.",
  inputSchema: z.object({
    tool_scope: scopeField,
    document_version_id: z.string().min(8),
    note_ref: z.string().min(1).max(10),
  }),
  label: { start: ({ note_ref }) => `Read note ${note_ref}` },
  async execute({ tool_scope, document_version_id, note_ref }) {
    return engineGet(`/internal/tools/notes/${encodeURIComponent(document_version_id)}/${encodeURIComponent(note_ref)}`, tool_scope);
  },
});
