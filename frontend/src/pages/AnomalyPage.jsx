import { useEffect, useState } from "react";
import AnomalyChart from "../components/AnomalyChart";

export default function AnomalyPage() {
  const [data, setData] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/anomalies");  // Using Vite proxy
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Error loading anomalies:", err);
      }
    }
    load();
  }, []);

  return (
    <div className="p-6 space-y-6">  {/* <-- Optional global spacing */}
      
      {/* Chart with spacing */}
      <div className="mb-6">
        <AnomalyChart />
      </div>

      <h1 className="text-2xl font-bold mb-4">⚠️ Anomaly Logs</h1>

      {data.length === 0 ? (
        <p className="text-gray-500">No anomalies found.</p>
      ) : (
        <div className="overflow-x-auto bg-white shadow-md rounded-lg">
          <table className="min-w-full border-collapse">
            <thead className="bg-gray-100 border-b">
              <tr>
                <th className="px-4 py-2 text-left font-semibold">Timestamp</th>
                <th className="px-4 py-2 text-left font-semibold">Source</th>
                <th className="px-4 py-2 text-left font-semibold">Metric</th>
                <th className="px-4 py-2 text-left font-semibold">Value</th>
                <th className="px-4 py-2 text-left font-semibold">Severity</th>
                <th className="px-4 py-2 text-left font-semibold">Trend</th>
              </tr>
            </thead>

            <tbody>
              {data.map((row, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2">{row.timestamp}</td>
                  <td className="px-4 py-2">{row.source}</td>
                  <td className="px-4 py-2">{row.metric}</td>
                  <td className="px-4 py-2">{row.value}</td>
                  <td className="px-4 py-2">
                    <span
                      className={
                        "px-2 py-1 rounded text-white text-sm " +
                        (row.severity === "High"
                          ? "bg-red-600"
                          : row.severity === "Medium"
                          ? "bg-yellow-600"
                          : "bg-green-600")
                      }
                    >
                      {row.severity}
                    </span>
                  </td>
                  <td className="px-4 py-2">{row.trend}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
    </div>
  );
}
