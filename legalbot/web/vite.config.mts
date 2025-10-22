import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ mode }) => {
  // ✅ Load environment variables based on mode (dev/prod)
  const env = loadEnv(mode, process.cwd(), "VITE_");

  const isRender = process.env.RENDER === "true";

  console.log("🌍 Vite build mode:", mode);
  console.log("✅ Loaded API base:", env.VITE_API_BASE_URL);
  console.log("✅ Loaded Frontend URL:", env.VITE_FRONTEND_URL);
  console.log("✅ Loaded Google Redirect:", env.VITE_GOOGLE_REDIRECT_URI);
  console.log("✅ Loaded Google Client ID:", env.VITE_GOOGLE_CLIENT_ID);

  return {
    plugins: [react()],
    define: {
      "process.env": process.env,
    },
    server: {
      port: 8602,
      strictPort: true,
      host: isRender ? "0.0.0.0" : "localhost",
    },
    preview: {
      port: 8602,
      host: "0.0.0.0",
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  };
});
