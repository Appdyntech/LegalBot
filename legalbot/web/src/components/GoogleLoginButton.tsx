import React, { useState } from "react";
import { Button, Card, CardContent, Typography, CircularProgress } from "@mui/material";
import GoogleIcon from "@mui/icons-material/Google";
import { signInWithGoogle } from "../firebase";

const GoogleLoginButton: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      console.log("🚀 Triggering Google popup login...");
      await signInWithGoogle();
      window.location.reload(); // reload to load Dashboard
    } catch (error) {
      console.error("❌ Login failed:", error);
      alert("Google sign-in failed. Please check Firebase setup or authorized domains.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #f3f4f6, #e0e7ff)",
      }}
    >
      <Card
        style={{
          maxWidth: 400,
          padding: 24,
          textAlign: "center",
          borderRadius: 16,
          boxShadow: "0 6px 16px rgba(0,0,0,0.1)",
        }}
      >
        <CardContent>
          <Typography variant="h4" fontWeight="bold" color="primary" gutterBottom>
            ⚖️ LegalBOT
          </Typography>
          <Typography variant="body1" color="textSecondary" gutterBottom>
            Sign in securely with Google to start using LegalBOT.
          </Typography>

          <Button
            variant="contained"
            startIcon={!loading && <GoogleIcon />}
            onClick={handleGoogleLogin}
            disabled={loading}
            sx={{
              mt: 3,
              textTransform: "none",
              fontSize: "1rem",
              fontWeight: 500,
              borderRadius: 2,
              padding: "10px 20px",
              backgroundColor: "#4285F4",
              "&:hover": { backgroundColor: "#3367D6" },
              width: "100%",
            }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : "Sign in with Google"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default GoogleLoginButton;
