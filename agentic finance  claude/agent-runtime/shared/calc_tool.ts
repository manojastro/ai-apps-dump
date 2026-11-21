import { defineTool } from "eve/tools";
import { z } from "zod";
import { engineGet } from "./engine";
import { scopeField } from "./scope";

export const getCalculation = defineTool({
  description:
    "Read a stored deterministic calculation record (rule or metric): expression, expected, observed, exact difference, tolerance, inputs.",
  inputSchema: z.object({ tool_scope: scopeField, calculation_id: z.string().min(8) }),
  label: { start: () => "Read calculation record" },
  async execute({ tool_scope, calculation_id }) {
    return engineGet(`/internal/tools/calculations/${encodeURIComponent(calculation_id)}`, tool_scope);
  },
});
