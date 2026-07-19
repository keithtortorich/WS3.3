import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Organization, team, and integration settings.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Organization settings</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Manage organization profile, team members, and platform connections here.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
