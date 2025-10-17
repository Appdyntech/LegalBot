// src/App.tsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import GoogleCallback from "./pages/GoogleCallback";
import DashboardLayout from "./pages/DashboardLayout";
import ChatPage from "./pages/ChatPage";

const App: React.FC = () => {
  // ✅ Simple auth check (token presence)
  const isLoggedIn = !!localStorage.getItem("token");

  return (
    <BrowserRouter>
      <Routes>
        {/* 🔹 Root route — redirect if logged in, else go to login */}
        <Route
          path="/"
          element={isLoggedIn ? <Navigate to="/dashboard" replace /> : <Login />}
        />

        {/* 🔹 Login page */}
        <Route
          path="/login"
          element={isLoggedIn ? <Navigate to="/dashboard" replace /> : <Login />}
        />

        {/* 🔹 Google OAuth callback handler */}
        <Route path="/google/callback" element={<GoogleCallback />} />

        {/* 🔹 Unified dashboard (main app layout after login) */}
        <Route
          path="/dashboard"
          element={
            isLoggedIn ? <DashboardLayout /> : <Navigate to="/login" replace />
          }
        />

        {/* 🔹 Optional direct chat route */}
        <Route
          path="/chat"
          element={isLoggedIn ? <ChatPage /> : <Navigate to="/login" replace />}
        />

        {/* 🔹 Catch-all fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
