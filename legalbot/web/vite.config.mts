import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 8602,
    strictPort: true, // ✅ Force use of this port, don’t auto-increment
    host: "localhost",
  },
});
