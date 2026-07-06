import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// `base` is empty in dev and set to the public base path (e.g. /gptl/) at build time
// so assets resolve when the SPA is served behind the /gptl reverse proxy in production.
export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:8099", changeOrigin: true },
    },
  },
});
