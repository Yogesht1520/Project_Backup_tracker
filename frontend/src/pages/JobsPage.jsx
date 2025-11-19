import JobsTable from "../components/JobsTable";
import CreateJobForm from "../components/CreateJobForm";

export default function JobsPage() {
  return (
    <div className="space-y-6">
      <CreateJobForm />
      <JobsTable />
    </div>
  );
}
