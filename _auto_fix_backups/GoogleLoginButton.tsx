// src/components/GoogleLoginButton.tsx
import React from "react";
import { Button } from "@mui/material";
import GoogleIcon from "@mui/icons-material/Google";

// Pull the API base from your Vite environment
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8705/api/v1";

const GoogleLoginButton: React.FC = () => {
  const handleGoogleLogin = () => {
    // Always redirect using the environment-defined backend URL
    window.location.href = `${import.meta.env.VITE_API_BASE_URL}/auth/google/login`;

  };

  return (
    <Button
      variant="contained"
      color="primary"
      fullWidth
      startIcon={<GoogleIcon />}
      sx={{
        textTransform: "none",
        backgroundColor: "#4285F4",
        "&:hover": { backgroundColor: "#3367D6" },
      }}
      onClick={handleGoogleLogin}
    >
      Sign in with Google
    </Button>
  );
};

export default GoogleLoginButton;
