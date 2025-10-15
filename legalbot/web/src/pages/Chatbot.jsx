// src/pages/Chatbot.jsx
import React from "react";

const Chatbot = () => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h1>Welcome, {user.name || "User"} 👋</h1>
      <img
        src={user.picture}
        alt="User Avatar"
        style={{ borderRadius: "50%", width: 100, height: 100 }}
      />
      <p>Email: {user.email}</p>
      <p>JWT Token saved in localStorage ✅</p>
    </div>
  );
};

export default Chatbot;
