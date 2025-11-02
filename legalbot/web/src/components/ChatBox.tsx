// web/src/components/ChatBox.tsx
import React, { useState, useRef, useEffect } from "react";
import { secureFetch } from "../api/secureApi";
import api from "../api/apiClient";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8705/api/v1";

interface HistoryItem {
  id?: number;
  session_id: string;
  question: string;
  answer: string;
  confidence?: number;
  timestamp?: string;
}

export default function ChatBox() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<
    { role: "user" | "bot"; text: string; confidence?: number; chatId?: string }[]
  >([]);
  const [recognition, setRecognition] = useState<any>(null);
  const [showFeedback, setShowFeedback] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ✅ Persistent session using localStorage
  const [sessionId] = useState(() => {
    const existing = localStorage.getItem("session_id");
    if (existing) return existing;
    const newId = `sess-${Date.now()}`;
    localStorage.setItem("session_id", newId);
    return newId;
  });

  // 🧠 Load chat history for this session only
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/chat/history?session_id=${sessionId}&limit=20`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data.success && Array.isArray(data.data)) {
          const formatted = data.data.flatMap((item: HistoryItem) => [
            { role: "user" as const, text: item.question },
            { role: "bot" as const, text: item.answer, confidence: item.confidence },
          ]);
          setMessages(formatted.reverse()); // oldest first
        }
      } catch (err) {
        console.error("Error loading chat history:", err);
        setError("⚠️ Unable to load previous chat history.");
      }
    };
    loadHistory();
  }, [sessionId]);

  // 🧭 Auto scroll on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 🎤 Voice input setup
  useEffect(() => {
    if ("webkitSpeechRecognition" in window) {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recog = new SpeechRecognition();
      recog.continuous = false;
      recog.interimResults = false;
      recog.lang = "en-IN";

      recog.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
        handleSend(transcript);
      };
      setRecognition(recog);
    }
  }, []);

  // 🚀 Send chat message
  const handleSend = async (voiceQuery?: string) => {
    const question = voiceQuery || query.trim();
    if (!question) return;

    setLoading(true);
    setError(null);
    setShowFeedback(null);
    setMessages((prev) => [...prev, { role: "user", text: question }]);

    try {
      const res = await secureFetch("chat/ask", {
        query: question,
        session_id: sessionId,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: res.answer || res.response || "No answer received.",
          confidence: res.confidence,
          chatId: (res as any).chat_id,
        },
      ]);

      if (res.feedback_prompt) {
        setShowFeedback((res as any).chat_id || "latest");
      }

      setQuery("");
    } catch (err) {
      console.error("Chat API error:", err);
      setError("❌ Failed to fetch response from LegalBOT API.");
    } finally {
      setLoading(false);
    }
  }; // ✅ Added missing closing brace

  // 🎙️ Voice input handler
  const handleVoiceInput = () => {
    if (recognition) recognition.start();
    else alert("🎙️ Voice input not supported in this browser.");
  };

  // 📝 Feedback handling
  const handleFeedback = async (option: "satisfied" | "need_assistance") => {
    if (!showFeedback) return;
    setShowFeedback(null);

    try {
      await api.post("/chat/feedback", {
        chat_id: showFeedback,
        feedback_option: option,
        feedback_text:
          option === "satisfied"
            ? "User confirmed query answered."
            : "User requested further assistance.",
        user_id: "frontend-user",
        session_id: sessionId,
      });

      if (option === "need_assistance") {
        const resp = await api.post("/tickets/create", {
          chat_id: showFeedback,
          user_id: "frontend-user",
          user_name: "Guest",
          user_phone: "+919999999999",
          category: "general",
          location: "Delhi",
        });

        alert(
          `✅ Ticket created successfully!\nTicket ID: ${resp.data.ticket_id}\nStatus: ${resp.data.status}`
        );
      } else {
        alert("✅ Thanks for your feedback!");
      }
    } catch (err) {
      console.error("❌ Feedback/Ticket Error:", err);
      alert("⚠️ Failed to record feedback or create ticket.");
    }
  };

  return (
    <div className="flex flex-col h-[90vh] max-w-4xl mx-auto border rounded-lg shadow-md p-4 bg-white">
      <h2 className="text-xl font-semibold text-center mb-4">
        ⚖️ LegalBOT AI Assistant
      </h2>

      {/* Chat Window */}
      <div className="flex-1 overflow-y-auto border p-3 rounded-md bg-gray-50">
        {messages.length === 0 && (
          <p className="text-center text-gray-500 italic mt-4">
            💬 Start a conversation by typing your legal question below.
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`my-2 p-3 rounded-lg max-w-[80%] ${
              msg.role === "user"
                ? "ml-auto bg-blue-100 text-right"
                : "mr-auto bg-gray-200 text-left"
            }`}
          >
            <p>{msg.text}</p>
            {msg.role === "bot" && msg.confidence !== undefined && (
              <p className="text-xs text-gray-500 mt-1">
                🔍 Confidence: {msg.confidence?.toFixed(2)}
              </p>
            )}
          </div>
        ))}

        {/* Feedback Prompt */}
        {showFeedback && (
          <div className="mt-4 p-3 bg-yellow-50 border rounded-md text-center">
            <p className="font-medium mb-2">
              🤔 Was your query answered satisfactorily?
            </p>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => handleFeedback("satisfied")}
                className="bg-green-500 text-white px-3 py-2 rounded-md hover:bg-green-600"
              >
                ✅ Yes
              </button>
              <button
                onClick={() => handleFeedback("need_assistance")}
                className="bg-red-500 text-white px-3 py-2 rounded-md hover:bg-red-600"
              >
                ⚖️ Need Lawyer
              </button>
            </div>
          </div>
        )}

        <div ref={chatEndRef}></div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="text-red-600 bg-red-100 border border-red-300 rounded-md p-2 mt-2">
          {error}
        </div>
      )}

      {/* Input Controls */}
      <div className="flex items-center gap-2 mt-4">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a legal question..."
          className="flex-grow border rounded-md p-2 h-16 resize-none"
          disabled={loading}
        />
        <button
          onClick={handleVoiceInput}
          className="bg-green-500 text-white px-3 py-2 rounded-md hover:bg-green-600"
          title="Voice Input"
        >
          🎤
        </button>
        <button
          onClick={() => handleSend()}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}
