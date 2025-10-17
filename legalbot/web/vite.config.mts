import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Detect Render or local environment
const isRender = process.env.RENDER === "true";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8602,
    strictPort: true,
    host: isRender ? "0.0.0.0" : "localhost", // ✅ allow external access
  },
  preview: {
    port: 8602,
    host: "0.0.0.0", // ✅ required for Docker/Render previews
  },
});
