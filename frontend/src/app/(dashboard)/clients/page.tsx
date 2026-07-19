import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ClientsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Clients</h1>
        <p className="text-muted-foreground">Agencies you manage social media for.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Client list</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Wire this page to GET /api/v1/clients following the same pattern as
            useCampaigns / CampaignsTable.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
