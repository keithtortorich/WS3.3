"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCampaignAnalytics } from "@/hooks/useCampaignAnalytics";
import type { CampaignAnalyticsSummary } from "@/types/analytics";

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat().format(value);
}

function MetricCard({ title, value }: { title: string; value: number | null | undefined }) {
  return (
    <Card>
      <CardHeader className="py-4">
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent className="py-2 text-2xl font-semibold">{formatNumber(value)}</CardContent>
    </Card>
  );
}

export function AnalyticsSummary({ token }: { token?: string }) {
  const [campaignId, setCampaignId] = useState("");

  const { data, isLoading, isError, error } = useCampaignAnalytics({ campaignId: campaignId || undefined, token });

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Analytics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium">Campaign ID</label>
            <input
              value={campaignId}
              onChange={(event) => setCampaignId(event.target.value)}
              placeholder="Paste a campaign UUID to load its summary"
              className="w-full rounded-md border bg-background p-2 text-sm"
            />
            <p className="text-xs text-muted-foreground">Use a Campaign ID from your data to load aggregated platform metrics.</p>
          </div>
        </CardContent>
      </Card>

      {campaignId.trim().length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Campaign performance</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full" />
                ))}
              </div>
            ) : isError ? (
              <p className="text-sm text-destructive">Failed to load analytics: {error instanceof Error ? error.message : "Unknown error"}</p>
            ) : data ? (
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <MetricCard title="Posts" value={data.total_posts} />
                <MetricCard title="Impressions" value={data.total_impressions} />
                <MetricCard title="Likes" value={data.total_likes} />
                <MetricCard title="Comments" value={data.total_comments} />
                <MetricCard title="Shares" value={data.total_shares} />
                <MetricCard title="Clicks" value={data.total_clicks} />
                <MetricCard title="Engagement rate" value={data.average_engagement_rate} />
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
