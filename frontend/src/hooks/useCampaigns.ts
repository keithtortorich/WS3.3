"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { Campaign, Page } from "@/types/campaign";

interface UseCampaignsParams {
  page?: number;
  pageSize?: number;
  clientId?: string;
  token?: string;
}

/**
 * Fetches a paginated list of campaigns from
 * GET {API_BASE}/api/v1/campaigns — the reference end-to-end wiring
 * example for the rest of the frontend's data hooks.
 */
export function useCampaigns({ page = 1, pageSize = 20, clientId, token }: UseCampaignsParams = {}) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (clientId) params.set("client_id", clientId);

  return useQuery<Page<Campaign>>({
    queryKey: ["campaigns", { page, pageSize, clientId }],
    queryFn: () => apiFetch<Page<Campaign>>(`/api/v1/campaigns?${params.toString()}`, { token }),
  });
}
