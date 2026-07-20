import { ApprovalsTable } from "@/components/approvals/approvals-table";

export default function ApprovalsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Approvals</h1>
        <p className="text-muted-foreground">Posts awaiting internal or client review.</p>
      </div>
      <ApprovalsTable />
    </div>
  );
}
