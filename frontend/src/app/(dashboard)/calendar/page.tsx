import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CalendarPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Content Calendar</h1>
        <p className="text-muted-foreground">Scheduled posts across all platforms.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Calendar view</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Wire this page to GET /api/v1/calendar?start_date=...&amp;end_date=....
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
