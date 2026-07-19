import { CampaignsTable } from "@/components/campaigns/campaigns-table";

export default function CampaignsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Campaigns</h1>
        <p className="text-muted-foreground">Manage marketing campaigns across all clients.</p>
      </div>
      <CampaignsTable />
    </div>
  );
}
