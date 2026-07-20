import { ClientsTable } from "@/components/clients/clients-table";

export default function ClientsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Clients</h1>
        <p className="text-muted-foreground">Agencies you manage social media for.</p>
      </div>
      <ClientsTable />
    </div>
  );
}
