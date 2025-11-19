import React, { useState } from "react";

export default function CreateJobForm() {
  const [jobName, setJobName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreateJob = async (e) => {
    e.preventDefault();
    if (!jobName.trim()) return;

    setLoading(true);

    try {
      const res = await  fetch("/create_job", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ job_name: jobName.trim() }),
      });

      const data = await res.json();
      alert(data.message || "Job created successfully!");

      setJobName("");
    } catch (err) {
      console.error("Error creating job:", err);
      alert("Failed to create job");
    }

    setLoading(false);
  };

  return (
    <form
      onSubmit={handleCreateJob}
      className="flex flex-wrap gap-3 items-center bg-white shadow p-4 rounded-md"
    >
      <input
        type="text"
        placeholder="Enter job name"
        value={jobName}
        onChange={(e) => setJobName(e.target.value)}
        required
        className="border border-gray-300 rounded-md px-3 py-2 text-sm flex-1 min-w-[220px]"
      />

      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-60"
      >
        {loading ? "Creating..." : "Create Job"}
      </button>
    </form>
  );
}
