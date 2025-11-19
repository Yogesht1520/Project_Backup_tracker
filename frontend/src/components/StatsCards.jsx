import React, { useEffect, useState } from "react";

export default function StatsCards() {
  const [stats, setStats] = useState({
    total: 0,
    success: 0,
    failed: 0,
    pending: 0,
  });

  const loadStats = async () => {
    try {
      const res = await fetch("/api/stats")

      const data = await res.json();
      setStats({
        total: data.total ?? 0,
        success: data.success ?? 0,
        failed: data.failed ?? 0,
        pending: data.pending ?? 0,
      });
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
      <StatCard
        label="Total"
        value={stats.total}
        className="bg-blue-600 text-white"
      />
      <StatCard
        label="Success"
        value={stats.success}
        className="bg-green-600 text-white"
      />
      <StatCard
        label="Failed"
        value={stats.failed}
        className="bg-red-600 text-white"
      />
      <StatCard
        label="Pending"
        value={stats.pending}
        className="bg-yellow-400 text-black"
      />
    </div>
  );
}

function StatCard({ label, value, className }) {
  return (
    <div className={`rounded-lg px-4 py-4 shadow text-center ${className}`}>
      <div className="text-xs uppercase tracking-wide opacity-80 font-medium">
        {label}
      </div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}
