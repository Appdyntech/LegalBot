// src/pages/Dashboard.tsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Box,
  Typography,
  Button,
  Avatar,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

interface Lawyer {
  name: string;
  category: string;
  firm_name: string;
  win_percentage: number;
  location: string;
  contact_email: string;
  consultation_fee: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [lawyers, setLawyers] = useState<Lawyer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");

    if (!token || !storedUser) {
      navigate("/login");
      return;
    }

    setUser(JSON.parse(storedUser));

    // Fetch lawyers
    const fetchLawyers = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8705/api/v1/lawyers", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setLawyers(res.data.lawyers || []);
      } catch (err) {
        console.error("Error fetching lawyers:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchLawyers();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", mt: 8, px: 3 }}>
      {user && (
        <>
          <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
            <Avatar
              src={user.picture || ""}
              alt={user.name}
              sx={{ width: 70, height: 70, mr: 2 }}
            />
            <Box>
              <Typography variant="h5">Welcome, {user.name}</Typography>
              <Typography variant="body2" color="textSecondary">
                {user.email}
              </Typography>
            </Box>
          </Box>

          <Button
            variant="outlined"
            color="secondary"
            onClick={handleLogout}
            sx={{ mb: 3 }}
          >
            Logout
          </Button>
        </>
      )}

      <Divider sx={{ mb: 3 }} />

      <Typography variant="h6" gutterBottom>
        ⚖️ Top Legal Experts
      </Typography>

      {loading ? (
        <CircularProgress sx={{ mt: 3 }} />
      ) : lawyers.length === 0 ? (
        <Typography>No lawyers found.</Typography>
      ) : (
        <List>
          {lawyers.map((lawyer, i) => (
            <ListItem
              key={i}
              sx={{
                border: "1px solid #e0e0e0",
                borderRadius: 2,
                mb: 2,
                boxShadow: "0px 2px 6px rgba(0,0,0,0.05)",
              }}
            >
              <ListItemText
                primary={`${lawyer.name} (${lawyer.category})`}
                secondary={
                  <>
                    <Typography variant="body2">
                      Firm: {lawyer.firm_name || "Independent"}
                    </Typography>
                    <Typography variant="body2">
                      Location: {lawyer.location || "N/A"}
                    </Typography>
                    <Typography variant="body2">
                      Win Rate: {lawyer.win_percentage}%
                    </Typography>
                    <Typography variant="body2">
                      Fee: ₹{lawyer.consultation_fee}
                    </Typography>
                    <Typography variant="body2">
                      Email: {lawyer.contact_email || "N/A"}
                    </Typography>
                  </>
                }
              />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
};

export default Dashboard;
