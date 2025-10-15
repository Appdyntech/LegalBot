// web/src/components/ChatHistory.tsx
import React, { useEffect, useState } from "react";

const ChatHistory = () => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8705/api/v1/chat/history?limit=50")
      .then((res) => res.json())
      .then((data) => setHistory(data.data || []))
      .catch((err) => console.error("Error loading chat history:", err));
  }, []);

  return (
    <div>
      <h2>🕓 Chat History</h2>
      {history.length === 0 ? (
        <p>No previous chats found.</p>
      ) : (
        <ul>
          {history.map((item: any, i: number) => (
            <li key={i}>
              <strong>Q:</strong> {item.question} <br />
              <strong>A:</strong> {item.answer}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ChatHistory;
