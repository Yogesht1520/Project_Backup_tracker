import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";

export default function VaultManager() {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  // Establish socket connection (same-origin backend)
  const socket = io();

  const loadVaultFiles = async () => {
    try {
      const res = await fetch("/vault/list");
      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Vault list error:", err);
    }
  };

  useEffect(() => {
    loadVaultFiles();
  }, []);

  // Listen for socket vault updates
  useEffect(() => {
    if (!socket) return;

    const updateHandler = (data) => {
      setMessage(data.message || "Vault updated");
      loadVaultFiles();
    };

    socket.on("vault_update", updateHandler);
    return () => socket.off("vault_update", updateHandler);
  }, [socket]);

  // File upload handler
  const handleUpload = async (e) => {
    e.preventDefault();

    const fileInput = e.target.file;
    if (!fileInput.files[0]) return;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    setUploading(true);

    try {
      const res = await fetch("/vault/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setMessage(data.message || "File uploaded");

      fileInput.value = "";
      loadVaultFiles();
    } catch (err) {
      console.error("Upload error:", err);
      setMessage("Upload failed");
    }

    setUploading(false);
  };

  // Restore a file
  const restoreFile = async (filename) => {
    try {
      window.open(`/vault/restore/${encodeURIComponent(filename)}`, "_blank");


      if (!res.ok) {
        const error = await res.json();
        alert(error.error || "Failed to restore");
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = filename.replace(".enc", "");
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Restore error:", err);
      alert("Restore failed");
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-5 space-y-4">
      <h2 className="text-xl font-semibold flex items-center gap-2">
        🔐 Vault Management
      </h2>

      {/* Upload Form */}
      <form
        onSubmit={handleUpload}
        className="flex flex-wrap gap-3 items-center"
      >
        <input type="file" name="file" required className="text-sm" />

        <button
          type="submit"
          disabled={uploading}
          className="px-4 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {uploading ? "Uploading..." : "Upload & Encrypt"}
        </button>
      </form>

      {/* Message popup */}
      {message && (
        <div className="px-3 py-2 bg-green-50 border border-green-300 text-green-700 text-sm rounded">
          {message}
        </div>
      )}

      {/* Files Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-3 py-2 text-left font-semibold">Filename</th>
              <th className="px-3 py-2 text-left font-semibold">Size (KB)</th>
              <th className="px-3 py-2 text-left font-semibold">Modified</th>
              <th className="px-3 py-2 text-left font-semibold">Action</th>
            </tr>
          </thead>

          <tbody>
            {files.length === 0 ? (
              <tr>
                <td
                  colSpan={4}
                  className="px-3 py-4 text-center text-gray-500"
                >
                  No encrypted files found
                </td>
              </tr>
            ) : (
              files.map((file) => (
                <tr
                  key={file.name}
                  className="border-t border-gray-200 hover:bg-gray-50"
                >
                  <td className="px-3 py-2">{file.name}</td>
                  <td className="px-3 py-2">{file.size_kb}</td>
                  <td className="px-3 py-2">{file.modified}</td>

                  <td className="px-3 py-2 space-x-2">
                    <button
                      onClick={() => restoreFile(file.name)}
                      className="px-3 py-1 text-xs rounded-md bg-blue-600 text-white hover:bg-blue-700"
                    >
                      Restore
                    </button>

                    {/* You can add "Verify" later when backend route is built */}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
