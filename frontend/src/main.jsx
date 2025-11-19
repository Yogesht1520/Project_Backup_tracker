import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";

import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import JobsPage from "./pages/JobsPage";
import VaultPage from "./pages/VaultPage";
import AnomalyPage from "./pages/AnomalyPage";
import TimelinePage from "./pages/TimelinePage";
import LiveMetricsPage from "./pages/LiveMetricsPage";

ReactDOM.createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <Navbar />

    <div className="p-6 max-w-7xl mx-auto">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/vault" element={<VaultPage />} />
        <Route path="/anomalies" element={<AnomalyPage />} />
        <Route path="/timeline" element={<TimelinePage />} />
        <Route path="/live" element={<LiveMetricsPage />} />
      </Routes>
    </div>
  </BrowserRouter>
);
