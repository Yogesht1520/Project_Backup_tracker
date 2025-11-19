import React, { useEffect, useState } from "react";

export default function JobsTable() {
  const [jobs, setJobs] = useState([]);

  // Load jobs from backend
  const loadJobs = async () => {
    try {
      const res = await fetch("/api/jobs")
      const data = await res.json();
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error loading jobs:", err);
    }
  };

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusClass = (status) => {
    if (status === "SUCCESS") return "text-green-600 font-semibold";
    if (status === "FAILED") return "text-red-600 font-semibold";
    if (status === "PENDING") return "text-yellow-600 font-semibold";
    return "text-gray-700";
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-3 py-2 text-left font-semibold">ID</th>
            <th className="px-3 py-2 text-left font-semibold">Name</th>
            <th className="px-3 py-2 text-left font-semibold">Status</th>
            <th className="px-3 py-2 text-left font-semibold">Timestamp</th>
          </tr>
        </thead>

        <tbody>
          {jobs.length === 0 ? (
            <tr>
              <td
                colSpan={4}
                className="px-3 py-4 text-center text-gray-500"
              >
                No jobs found
              </td>
            </tr>
          ) : (
            jobs.map((job) => (
              <tr
                key={job.id}
                className="border-t border-gray-100 hover:bg-gray-50"
              >
                <td className="px-3 py-2">{job.id}</td>
                <td className="px-3 py-2">{job.name}</td>
                <td className={`px-3 py-2 ${getStatusClass(job.status)}`}>
                  {job.status}
                </td>
                <td className="px-3 py-2">{job.timestamp}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
