// src/App.tsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/login";
import GoogleCallback from "./pages/GoogleCallback";
import DashboardLayout from "./pages/DashboardLayout"; // ✅ use the new unified layout
import ChatPage from "./pages/ChatPage";

const App: React.FC = () => {
  const isLoggedIn = !!localStorage.getItem("token");

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={isLoggedIn ? <Navigate to="/dashboard" /> : <Login />}
        />
        <Route path="/login" element={<Login />} />
        <Route path="/google/callback" element={<GoogleCallback />} />

        {/* ✅ New unified dashboard with sidebar, chat, classify, etc. */}
        <Route path="/dashboard" element={<DashboardLayout />} />

        {/* Chat route (optional standalone access) */}
        <Route path="/chat" element={<ChatPage />} />

        {/* Default fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
