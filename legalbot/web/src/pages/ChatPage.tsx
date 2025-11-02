// src/pages/ChatPage.tsx
import React, { useState, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import { signInWithGoogle, logout } from "../firebase";

const ChatPage: React.FC = () => {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Load user info from localStorage (if already signed in)
    const savedUser = JSON.parse(localStorage.getItem("user") || "null");
    if (savedUser) setUser(savedUser);
  }, []);

  const handleLogin = async () => {
    try {
      const user = await signInWithGoogle();
      setUser({
        name: user.displayName,
        email: user.email,
        picture: user.photoURL,
      });
      window.location.reload(); // refresh to show user info + start chat
    } catch (error) {
      console.error("❌ Login failed:", error);
    }
  };

  const handleLogout = async () => {
    await logout();
    setUser(null);
    window.location.reload();
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="p-4 bg-blue-600 text-white text-center shadow-md flex flex-col items-center gap-2">
        <h2 className="text-2xl font-semibold">⚖️ LegalBOT - AI Legal Assistant</h2>

        {user ? (
          <>
            <div className="flex items-center gap-3">
              <img
                src={user.picture}
                alt="Profile"
                className="w-10 h-10 rounded-full border-2 border-white"
              />
              <p className="text-sm text-blue-100">
                Welcome, <span className="font-semibold">{user.name}</span>{" "}
                ({user.email})
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm mt-1"
            >
              Logout
            </button>
          </>
        ) : (
          <button
            onClick={handleLogin}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md text-sm mt-2"
          >
            Sign in with Google
          </button>
        )}
      </header>

      {/* Chat UI */}
      <main className="flex-1 p-4">
        {user ? (
          <ChatBox />
        ) : (
          <div className="text-center text-gray-600 mt-10">
            <p className="text-lg">Please sign in with Google to start chatting 💬</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default ChatPage;
