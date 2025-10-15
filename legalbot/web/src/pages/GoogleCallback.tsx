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
      localStorage.setItem("token", jwt);
      localStorage.setItem(
        "user",
        JSON.stringify({ email, name, picture })
      );
      navigate("/dashboard"); // Redirect after successful login
    } else {
      navigate("/login");
    }
  }, [navigate]);

  return (
    <div style={{ textAlign: "center", marginTop: "30vh" }}>
      <h3>Verifying Google Login...</h3>
    </div>
  );
};

export default GoogleCallback;
