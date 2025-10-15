// web/src/pages/DashboardLayout.tsx
import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemText,
  CssBaseline,
} from "@mui/material";
import ChatBox from "../components/ChatBox";
import ChatHistory from "../components/ChatHistory";
import ClassificationPanel from "../components/ClassificationPanel";
import RiskPanel from "../components/RiskPanel";
import SummarizationPanel from "../components/SummarizationPanel";

const drawerWidth = 220;

const DashboardLayout: React.FC = () => {
  const [activeTab, setActiveTab] = useState("chat");
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };

  const renderContent = () => {
    switch (activeTab) {
      case "chat":
        return <ChatBox />;
      case "history":
        return <ChatHistory />;
      case "classify":
        return <ClassificationPanel />;
      case "risk":
        return <RiskPanel />;
      case "summarize":
        return <SummarizationPanel />;
      default:
        return <ChatBox />;
    }
  };

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      {/* Top Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: "#1e88e5",
        }}
      >
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            ⚖️ LegalBOT Dashboard
          </Typography>
          {user?.name && (
            <Typography variant="body1" sx={{ mr: 2 }}>
              Welcome, {user.name}
            </Typography>
          )}
          <Button color="inherit" onClick={handleLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: drawerWidth,
            boxSizing: "border-box",
            background: "#f4f4f4",
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: "auto" }}>
          <List>
            {[
              { key: "chat", label: "💬 Chat" },
              { key: "classify", label: "📂 Classify" },
              { key: "summarize", label: "🧾 Summarize" },
              { key: "risk", label: "⚠️ Risk Analysis" },
              { key: "history", label: "🕓 Chat History" },
            ].map((item) => (
              <ListItem
                button
                key={item.key}
                selected={activeTab === item.key}
                onClick={() => setActiveTab(item.key)}
              >
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: "#fafafa",
          p: 3,
          mt: 8,
          minHeight: "100vh",
        }}
      >
        {renderContent()}
      </Box>
    </Box>
  );
};

export default DashboardLayout;
