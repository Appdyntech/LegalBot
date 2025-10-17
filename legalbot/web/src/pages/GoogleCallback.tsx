// src/pages/GoogleCallback.tsx
import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const GoogleCallback: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const jwt = params.get("jwt");
    const email = params.get("email");
    const name = params.get("name");
    const picture = params.get("picture");

    if (jwt) {
      // ✅ Save auth info
      localStorage.setItem("token", jwt);
      localStorage.setItem(
        "user",
        JSON.stringify({ email, name, picture })
      );

      console.log("✅ Google login successful:", { email, name, picture });

      // ✅ Redirect user to chat (main page)
      navigate("/chat");
    } else {
      console.error("❌ Missing JWT in Google callback URL");
      navigate("/");
    }
  }, [navigate]);

  return (
    <div className="flex flex-col items-center justify-center h-screen text-center">
      <h2 className="text-xl font-semibold mb-3">🔄 Signing you in...</h2>
      <p className="text-gray-600">Please wait while we verify your Google login.</p>
    </div>
  );
};

export default GoogleCallback;
