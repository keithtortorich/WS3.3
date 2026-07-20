import { AnalyticsSummary } from "@/components/analytics/analytics-summary";

export default function AnalyticsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Performance metrics across campaigns and platforms.</p>
      </div>
      <AnalyticsSummary />
    </div>
  );
}
