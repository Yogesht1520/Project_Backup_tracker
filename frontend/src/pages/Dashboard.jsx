import StatsCards from "../components/StatsCards";
import StatusChart from "../components/StatusChart";
import JobsTable from "../components/JobsTable";
import CreateJobForm from "../components/CreateJobForm";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <StatsCards />
      <StatusChart />
      <CreateJobForm />
      <JobsTable />
    </div>
  );
}
