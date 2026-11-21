import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07080c",
          900: "#0b0d14",
          800: "#12141c",
          700: "#1a1d27",
          600: "#242834",
        },
        line: "#2a3040",
        cyan: {
          DEFAULT: "#5eead4",
          dim: "#2dd4bf",
        },
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "ui-sans-serif", "system-ui"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(45, 212, 191, 0.08)",
      },
    },
  },
  plugins: [],
};
export default config;
