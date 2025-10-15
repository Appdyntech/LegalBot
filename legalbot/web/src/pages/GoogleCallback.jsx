// src/pages/GoogleCallback.jsx
import React, { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import customerApi from "../api/customerApi";

const GoogleCallback = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const jwt = params.get("jwt");
    const email = params.get("email");
    const name = params.get("name");
    const picture = params.get("picture");

    if (!jwt || !email) {
      alert("Google login failed or missing token.");
      navigate("/login");
      return;
    }

    // ✅ Save token & user info in localStorage
    localStorage.setItem("token", jwt);
    localStorage.setItem("user", JSON.stringify({ email, name, picture }));

    // ✅ Register user if new
    const registerUser = async () => {
      try {
        await customerApi.register({
          name,
          email,
          phone: "",
          location: "",
          google_verified: true,
        });
      } catch (err) {
        console.warn("User registration skipped:", err.response?.data || err.message);
      } finally {
        // ✅ Redirect after successful verification
        navigate("/chat");
      }
    };

    registerUser();
  }, [params, navigate]);

  return (
    <div style={{ textAlign: "center", marginTop: "30vh" }}>
      <h2>Verifying your account...</h2>
      <p>Please wait a moment.</p>
    </div>
  );
};

export default GoogleCallback;
