import { useEffect, useRef, useState } from "react";
import Chart from "chart.js/auto";

export default function AnomalyChart() {
  const chartRef = useRef(null);
  const [chart, setChart] = useState(null);
  const [data, setData] = useState([]);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await fetch("/api/anomalies"); // via Vite proxy
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Error loading anomalies:", err);
      }
    }
    loadData();
  }, []);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    const labels = data.map((item) => item.timestamp);
    const values = data.map((item) => item.value);

    if (chart) {
      chart.destroy();
    }

    const newChart = new Chart(chartRef.current, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Anomaly Value",
            data: values,
            borderColor: "rgba(255, 99, 132, 0.8)",
            backgroundColor: "rgba(255, 99, 132, 0.3)",
            borderWidth: 2,
            pointRadius: 3,
            fill: false,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
          legend: { display: false },
        },

        scales: {
          x: {
            ticks: {
              autoSkip: true,
              maxTicksLimit: 8,  // <-- prevents overlapping
              maxRotation: 0,
              minRotation: 0,
            },
          },
          y: {
            beginAtZero: true,
          },
        },
      },
    });

    setChart(newChart);
  }, [data]);

  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-3">📈 Anomaly Trend Chart</h2>

      {/* Add spacing so it doesn't overlap UI elements */}
      <div className="h-72 mb-8">  
        <canvas ref={chartRef}></canvas>
      </div>
    </div>
  );
}
