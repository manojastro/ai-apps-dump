import { defineTool } from "eve/tools";
import { z } from "zod";
import { engineGet } from "./engine";
import { scopeField } from "./scope";

// Shared definition reused by several agents' tools/get_row_context.ts files.
export const getRowContext = defineTool({
  description:
    "Get an extracted row's original label, section path, total flag, note reference, raw cells and neighbouring rows.",
  inputSchema: z.object({ tool_scope: scopeField, row_id: z.string().min(8) }),
  label: { start: () => "Read row context" },
  async execute({ tool_scope, row_id }) {
    return engineGet(`/internal/tools/rows/${encodeURIComponent(row_id)}`, tool_scope);
  },
});
