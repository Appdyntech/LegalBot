// src/pages/ChatPage.tsx
import React from "react";
import ChatBox from "../components/ChatBox";

const ChatPage: React.FC = () => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="p-4 bg-blue-600 text-white text-center shadow-md">
        <h2 className="text-2xl font-semibold">
          ⚖️ LegalBOT - AI Legal Assistant
        </h2>
        <p className="text-sm text-blue-100">
          Welcome, {user.name || "Guest"} ({user.email || "Anonymous"})
        </p>
      </header>

      {/* Chat UI */}
      <main className="flex-1 p-4">
        <ChatBox />
      </main>
    </div>
  );
};

export default ChatPage;
