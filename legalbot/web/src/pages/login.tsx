// src/pages/Login.tsx
import React, { useState, ChangeEvent } from "react";
import customerApi from "../api/customerApi";
import GoogleLoginButton from "../components/GoogleLoginButton";
import {
  TextField,
  Button,
  Typography,
  Box,
  CircularProgress,
} from "@mui/material";

interface CustomerForm {
  name: string;
  email: string;
  phone?: string;
  location?: string;
}

const Login: React.FC = () => {
  const [form, setForm] = useState<CustomerForm>({
    name: "",
    email: "",
    phone: "",
    location: "",
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleRegister = async () => {
    if (!form.name || !form.email) {
      setMessage("⚠️ Please fill in your name and email.");
      return;
    }

    setLoading(true);
    setMessage("");
    try {
      const res = await customerApi.register({
        ...form,
        google_verified: false,
      });
      setMessage(`✅ Registered successfully! Customer ID: ${res.data.customer_id}`);
      setForm({ name: "", email: "", phone: "", location: "" });
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || "Registration failed.";
      setMessage("❌ " + errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 420, mx: "auto", mt: 10, textAlign: "center" }}>
      <Typography variant="h4" gutterBottom>
        ⚖️ Welcome to LegalBOT
      </Typography>

      <Typography variant="subtitle1" sx={{ mb: 3 }}>
        Smart Legal Assistance Platform
      </Typography>

      {/* ---- Google Login ---- */}
      <GoogleLoginButton />

      <Typography variant="body1" sx={{ mt: 3, mb: 1 }}>
        or register manually
      </Typography>

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
        {loading ? <CircularProgress size={22} color="inherit" /> : "Register"}
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
