import { useEffect, useRef, useState } from "react";
import Chart from "chart.js/auto";

export default function StatusChart() {
  const chartRef = useRef(null);
  const [chart, setChart] = useState(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await fetch("/api/stats"); // Vite proxy used
        const data = await res.json();

        const labels = ["Success", "Failed", "Pending"];
        const values = [data.success, data.failed, data.pending];

        if (chart) {
          chart.destroy();
        }

        const newChart = new Chart(chartRef.current, {
          type: "bar",
          data: {
            labels,
            datasets: [
              {
                label: "Jobs Summary",
                data: values,
                backgroundColor: ["#22c55e", "#ef4444", "#fbbf24"],
                borderColor: ["#16a34a", "#dc2626", "#d97706"],
                borderWidth: 1,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,   // 🔥 Important (allows height to work)
            scales: {
              y: {
                beginAtZero: true,
              },
            },
          },
        });

        setChart(newChart);
      } catch (error) {
        console.error("Error loading stats:", error);
      }
    }

    loadStats();
  }, []);

  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h2 className="text-xl mb-2 font-semibold">📊 Job Status Overview</h2>

      {/* 🔥 Height added so chart becomes visible */}
      <div className="h-72">
        <canvas ref={chartRef}></canvas>
      </div>
    </div>
  );
}
