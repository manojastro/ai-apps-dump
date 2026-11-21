import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
export default defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    ".next/**",
    "node_modules/**",
    ".venv/**",
    "app/insight/**",
    "lib/analytics/**",
  ]),
  { rules: { "react-hooks/set-state-in-effect": "off" } },
]);
