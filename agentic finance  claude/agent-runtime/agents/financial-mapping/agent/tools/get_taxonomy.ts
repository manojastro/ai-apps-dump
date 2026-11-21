import { defineTool } from "eve/tools";
import { z } from "zod";
import { engineGet } from "../../../../shared/engine";
import { scopeField } from "../../../../shared/scope";

export default defineTool({
  description: "List the canonical line items (code, label, section, total flag, unit) for one statement type.",
  inputSchema: z.object({
    tool_scope: scopeField,
    statement_type: z.enum(["balance_sheet", "income_statement", "cash_flow"]),
  }),
  label: { start: ({ statement_type }) => `Read taxonomy: ${statement_type}` },
  async execute({ tool_scope, statement_type }) {
    return engineGet(`/internal/tools/taxonomy/${statement_type}`, tool_scope);
  },
});
