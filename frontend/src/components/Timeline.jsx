import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";

// Helper: Infer severity if backend doesn't provide it
function inferSeverity(metric, value) {
  const v = Number(value) || 0;

  if (metric === "CPU" || metric === "RAM") {
    if (v >= 90) return "High";
    if (v >= 75) return "Medium";
    return "Low";
  }
  if (metric === "Disk") {
    if (v >= 95) return "High";
    if (v >= 85) return "Medium";
    return "Low";
  }
  return "Low";
}

export default function Timeline() {
  const socket = io();

  const [events, setEvents] = useState([]);
  const [metricFilter, setMetricFilter] = useState("All");
  const [severityFilter, setSeverityFilter] = useState("All");
  const [sourceFilter, setSourceFilter] = useState("All");

  const [collectorStatus, setCollectorStatus] = useState({
    color: "bg-gray-400",
    text: "Collector: Unknown",
  });

  // Fetch the timeline from backend
  const fetchTimeline = async () => {
    try {
      const res = await fetch("/api/anomaly_timeline");
      const data = await res.json();
      setEvents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Timeline error:", err);
    }
  };

  useEffect(() => {
    fetchTimeline();
    const id = setInterval(fetchTimeline, 5000);
    return () => clearInterval(id);
  }, []);

  // Setup socket listeners
  useEffect(() => {
    if (!socket) return;

    const onConnect = () => {
      setCollectorStatus({
        color: "bg-green-500",
        text: "Collector: Connected",
      });
    };

    const onDisconnect = () => {
      setCollectorStatus({
        color: "bg-orange-500",
        text: "Collector: Disconnected",
      });
    };

    const onAnomaly = () => {
      fetchTimeline(); // refresh immediately when anomaly event arrives
    };

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("anomaly_alert", onAnomaly);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("anomaly_alert", onAnomaly);
    };
  }, [socket]);

  // Apply filters
  const filtered = events
    .map((e) => ({
      ...e,
      severity:
        e.severity ||
        inferSeverity(
          e.metric || "Unknown",
          e.value != null ? e.value : 0
        ),
    }))
    .filter((ev) => {
      if (metricFilter !== "All" && ev.metric !== metricFilter) return false;
      if (severityFilter !== "All" && ev.severity !== severityFilter) return false;
      if (sourceFilter !== "All" && ev.source !== sourceFilter) return false;
      return true;
    })
    .sort((a, b) =>
      String(b.timestamp || "").localeCompare(String(a.timestamp || ""))
    );

  // Export visible rows as CSV
  const exportCsv = () => {
    if (filtered.length === 0) {
      alert("No rows to export");
      return;
    }

    const headers = ["timestamp", "source", "metric", "value", "severity"];
    const rows = [
      headers.join(","),
      ...filtered.map((r) =>
        headers
          .map((h) =>
            `"${r[h] !== undefined && r[h] !== null
              ? String(r[h]).replace(/"/g, '""')
              : ""
            }"`
          )
          .join(",")
      ),
    ];

    const blob = new Blob([rows.join("\n")], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.href = url;
    a.download = `anomaly_timeline_${new Date()
      .toISOString()
      .replace(/[:T]/g, "-")
      .slice(0, 19)}.csv`;

    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white shadow rounded-lg p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-xl font-semibold">🧠 Unified Anomaly Timeline</h2>

        <div className="flex items-center gap-2 text-sm">
          <span className={`inline-block w-3 h-3 rounded-full ${collectorStatus.color}`}></span>
          <span>{collectorStatus.text}</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 text-sm items-center">
        <Filter label="Metric">
          <select
            className="border rounded px-2 py-1"
            value={metricFilter}
            onChange={(e) => setMetricFilter(e.target.value)}
          >
            <option value="All">All</option>
            <option value="CPU">CPU</option>
            <option value="RAM">RAM</option>
            <option value="Disk">Disk</option>
          </select>
        </Filter>

        <Filter label="Severity">
          <select
            className="border rounded px-2 py-1"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="All">All</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </Filter>

        <Filter label="Source">
          <select
            className="border rounded px-2 py-1"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
          >
            <option value="All">All</option>
            <option value="Rule-Based">Rule-Based</option>
            <option value="ML">ML</option>
          </select>
        </Filter>

        <button
          onClick={exportCsv}
          className="ml-auto px-4 py-2 rounded bg-gray-900 text-white text-xs hover:bg-black"
        >
          Export Visible CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-3 py-2 text-left font-semibold">Timestamp</th>
              <th className="px-3 py-2 text-left font-semibold">Source</th>
              <th className="px-3 py-2 text-left font-semibold">Metric</th>
              <th className="px-3 py-2 text-left font-semibold">Value</th>
              <th className="px-3 py-2 text-left font-semibold">Severity</th>
              <th className="px-3 py-2 text-left font-semibold">Trend</th>
            </tr>
          </thead>

          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center text-gray-500 py-4">
                  No events found
                </td>
              </tr>
            ) : (
              filtered.map((ev, index) => {
                const sevColor =
                  ev.severity === "High"
                    ? "text-red-600"
                    : ev.severity === "Medium"
                    ? "text-yellow-500"
                    : "text-green-600";

                return (
                  <tr
                    key={index}
                    className="border-t border-gray-200 hover:bg-gray-50"
                  >
                    <td className="px-3 py-2">{ev.timestamp}</td>
                    <td className="px-3 py-2">{ev.source || "Unknown"}</td>
                    <td className="px-3 py-2">{ev.metric}</td>
                    <td className="px-3 py-2">{ev.value}</td>
                    <td className={`px-3 py-2 font-semibold ${sevColor}`}>
                      {ev.severity}
                    </td>
                    <td className="px-3 py-2 text-gray-500 text-xs">
                      {/* Sparkline chart removed to keep component lightweight */}
                      Trend
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Filter({ label, children }) {
  return (
    <div className="flex items-center gap-2">
      <span className="bg-gray-100 px-2 py-1 rounded text-xs font-medium">
        {label}
      </span>
      {children}
    </div>
  );
}
