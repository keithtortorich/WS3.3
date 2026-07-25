import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Overview of activity across all clients.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Active Campaigns</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">—</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Pending Approvals</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">—</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Posts Published (30d)</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">—</CardContent>
        </Card>
      </div>
    </div>
  );
}
