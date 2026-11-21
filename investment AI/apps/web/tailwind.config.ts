import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#121A24",
        navy: "#16324F",
        "navy-deep": "#0E1C2E",
        paper: "#F4F0E6",
        raised: "#FFFBF3",
        brass: "#9A7348",
        rule: "#D6CDB8",
        seal: "#8B3A3A",
        moss: "#2F5D50",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-ui)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        ledger: "0 1px 0 #D6CDB8",
      },
    },
  },
  plugins: [],
};

export default config;
