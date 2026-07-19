import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Performance metrics across campaigns and platforms.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Campaign performance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Wire this page to GET /api/v1/analytics/campaigns/{"{campaign_id}"}/summary.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
