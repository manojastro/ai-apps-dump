import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const api = process.env.PROCNAV_API ?? "http://127.0.0.1:8300";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5273,
    strictPort: true,
    proxy: { "/api": { target: api, changeOrigin: false } },
  },
  build: { outDir: "dist", sourcemap: false },
});
