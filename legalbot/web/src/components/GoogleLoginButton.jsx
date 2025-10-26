// src/components/GoogleLoginButton.jsx
import React from "react";
import { Button } from "@mui/material";
import GoogleIcon from "@mui/icons-material/Google";

const GoogleLoginButton = () => {
  const handleGoogleLogin = () => {
    window.location.href = "${import.meta.env.VITE_API_BASE_URL}/auth/google/login";
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

