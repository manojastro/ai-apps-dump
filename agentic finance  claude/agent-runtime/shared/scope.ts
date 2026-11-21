import { z } from "zod";

// Every tool takes the signed scope token the coordinator put in the turn's client context (`tool_scope`).
export const scopeField = z
  .string()
  .min(20)
  .describe("The tool_scope value from the client context, passed through unchanged.");
