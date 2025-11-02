// web/src/main.tsx
import React from "react";
import "./firebase";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
console.log("✅ VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
