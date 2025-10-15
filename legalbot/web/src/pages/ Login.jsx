// src/pages/Login.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import customerApi from "../api/customerApi";
import GoogleLoginButton from "../components/GoogleLoginButton";
import {
  TextField,
  Button,
  Typography,
  Box,
  CircularProgress,
  Divider,
} from "@mui/material";

const Login = () => {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    location: "",
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // ----------------------------
  // Handle form input change
  // ----------------------------
  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // ----------------------------
  // Handle manual registration
  // ----------------------------
  const handleRegister = async () => {
    if (!form.name || !form.email) {
      setMessage("⚠️ Please enter your name and email to register.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const res = await customerApi.register({
        ...form,
        google_verified: false,
      });

      // ✅ Persist user session
      localStorage.setItem("user", JSON.stringify(res.data));
      localStorage.setItem("token", res.data?.token || "manual_user");

      // ✅ Notify and redirect
      setMessage("✅ Registered successfully! Redirecting to dashboard...");
      setTimeout(() => navigate("/dashboard"), 1200);
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || err.message || "Registration failed.";

      if (
        errorMsg.includes("unique constraint") ||
        errorMsg.includes("already exists")
      ) {
        setMessage("ℹ️ User already registered. Redirecting to dashboard...");
        setTimeout(() => navigate("/dashboard"), 1200);
      } else {
        setMessage("❌ " + errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  // ----------------------------
  // Render Login Page
  // ----------------------------
  return (
    <Box
      sx={{
        maxWidth: 420,
        mx: "auto",
        mt: 10,
        p: 4,
        textAlign: "center",
        borderRadius: 3,
        boxShadow: 3,
        backgroundColor: "#fafafa",
      }}
    >
      <Typography variant="h4" gutterBottom sx={{ fontWeight: "bold" }}>
        ⚖️ Welcome to LegalBOT
      </Typography>

      <Typography variant="subtitle1" sx={{ mb: 3, color: "text.secondary" }}>
        Smart Legal Assistance Platform
      </Typography>

      {/* ---- Google Login ---- */}
      <GoogleLoginButton />

      <Divider sx={{ my: 3 }}>or register manually</Divider>

      {/* ---- Manual Registration ---- */}
      <TextField
        label="Full Name"
        name="name"
        fullWidth
        margin="dense"
        onChange={handleChange}
        value={form.name}
      />
      <TextField
        label="Email"
        name="email"
        type="email"
        fullWidth
        margin="dense"
        onChange={handleChange}
        value={form.email}
      />
      <TextField
        label="Phone"
        name="phone"
        fullWidth
        margin="dense"
        onChange={handleChange}
        value={form.phone}
      />
      <TextField
        label="Location"
        name="location"
        fullWidth
        margin="dense"
        onChange={handleChange}
        value={form.location}
      />

      <Button
        variant="contained"
        color="secondary"
        fullWidth
        sx={{ mt: 2, py: 1.2 }}
        onClick={handleRegister}
        disabled={loading}
      >
        {loading ? (
          <CircularProgress size={22} color="inherit" />
        ) : (
          "Register"
        )}
      </Button>

      {message && (
        <Typography
          variant="body2"
          sx={{
            mt: 2,
            color: message.startsWith("✅")
              ? "green"
              : message.startsWith("⚠️")
              ? "#ff9800"
              : message.startsWith("ℹ️")
              ? "blue"
              : "red",
          }}
        >
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default Login;
