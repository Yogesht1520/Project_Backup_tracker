import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-gray-900 text-white px-6 py-4 shadow-md">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        
        <h1 className="text-xl font-bold">Backup Tracker</h1>

        <div className="flex space-x-6">
          <Link to="/" className="hover:text-yellow-400">Dashboard</Link>
          {/* <Link to="/jobs" className="hover:text-yellow-400">Jobs</Link> */}
          <Link to="/vault" className="hover:text-yellow-400">Vault</Link>
          <Link to="/anomalies" className="hover:text-yellow-400">Anomalies</Link>
          <Link to="/timeline" className="hover:text-yellow-400">Timeline</Link>
          <Link to="/live" className="hover:text-yellow-400">Live Metrics</Link>
        </div>
      </div>
    </nav>
  );
}
