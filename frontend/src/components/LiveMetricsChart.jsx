import React, { useEffect, useRef } from "react";
import { io } from "socket.io-client";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
);

export default function LiveMetricsChart() {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  // Connect socket
  const socket = io({
    path: "/socket.io"
  })

  useEffect(() => {
    if (!canvasRef.current) return;

    const ctx = canvasRef.current.getContext("2d");

    // Create initial empty chart
    chartRef.current = new ChartJS(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "CPU %",
            data: [],
            borderColor: "red",
            borderWidth: 2,
            tension: 0.3,
          },
          {
            label: "RAM %",
            data: [],
            borderColor: "blue",
            borderWidth: 2,
            tension: 0.3,
          },
          {
            label: "Disk %",
            data: [],
            borderColor: "green",
            borderWidth: 2,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true, max: 100 },
        },
      },
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, []);

  // Handle live updates from socket.io
  useEffect(() => {
    if (!socket || !chartRef.current) return;

    const updateHandler = ({ timestamp, cpu, ram, disk }) => {
      const chart = chartRef.current;

      // Keep last 15 points
      if (chart.data.labels.length > 15) {
        chart.data.labels.shift();
        chart.data.datasets.forEach((ds) => ds.data.shift());
      }

      chart.data.labels.push(timestamp);
      chart.data.datasets[0].data.push(cpu);
      chart.data.datasets[1].data.push(ram);
      chart.data.datasets[2].data.push(disk);

      chart.update();
    };

    socket.on("metrics_update", updateHandler);

    return () => {
      socket.off("metrics_update", updateHandler);
    };
  }, [socket]);

  return (
    <div className="bg-white shadow rounded-lg p-5">
      <h2 className="text-lg font-semibold mb-3">
        📡 Live System Metrics (CPU / RAM / Disk)
      </h2>

      <canvas ref={canvasRef} height={260}></canvas>
    </div>
  );
}
