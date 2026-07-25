"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCampaigns } from "@/hooks/useCampaigns";
import type { CampaignStatus } from "@/types/campaign";

const STATUS_VARIANT: Record<CampaignStatus, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "outline",
  active: "default",
  paused: "secondary",
  completed: "secondary",
  archived: "destructive",
};

export function CampaignsTable({ token }: { token?: string }) {
  const { data, isLoading, isError, error } = useCampaigns({ token });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Campaigns</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Campaigns</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">
            Failed to load campaigns: {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </CardContent>
      </Card>
    );
  }

  const campaigns = data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Campaigns ({data?.total ?? 0})</CardTitle>
      </CardHeader>
      <CardContent>
        {campaigns.length === 0 ? (
          <p className="text-sm text-muted-foreground">No campaigns yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Goal</TableHead>
                <TableHead>Start</TableHead>
                <TableHead>End</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {campaigns.map((campaign) => (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium">{campaign.name}</TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[campaign.status]}>{campaign.status}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{campaign.goal ?? "—"}</TableCell>
                  <TableCell>{campaign.start_date ?? "—"}</TableCell>
                  <TableCell>{campaign.end_date ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
