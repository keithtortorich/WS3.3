"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AnalyticsSnapshot, CampaignAnalyticsSummary } from "@/types/analytics";

interface UseCampaignAnalyticsParams {
  campaignId?: string;
  token?: string;
}

/**
 * Fetches campaign analytics rollup from
 * GET {API_BASE}/api/v1/analytics/campaigns/{campaign_id}/summary.
 *
 * This is intentionally summary-only for now; paginated snapshot listing
 * may be added later without changing the page shell.
 */
export function useCampaignAnalytics({
  campaignId,
  token,
}: UseCampaignAnalyticsParams = {}) {
  const enabled = Boolean(campaignId && campaignId.trim().length > 0);

  return useQuery<CampaignAnalyticsSummary>({
    queryKey: ["analytics", "campaign-summary", campaignId],
    enabled,
    queryFn: () =>
      apiFetch<CampaignAnalyticsSummary>(`/api/v1/analytics/campaigns/${campaignId}/summary`, { token }),
  });
}
