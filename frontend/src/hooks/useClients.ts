"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { Client, Page } from "@/types/client";

interface UseClientsParams {
  page?: number;
  pageSize?: number;
  token?: string;
}

/**
 * Fetches a paginated list of clients from
 * GET {API_BASE}/api/v1/clients.
 */
export function useClients({
  page = 1,
  pageSize = 20,
  token,
}: UseClientsParams = {}) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  return useQuery<Page<Client>>({
    queryKey: ["clients", { page, pageSize }],
    queryFn: () => apiFetch<Page<Client>>(`/api/v1/clients?${params.toString()}`, { token }),
  });
}
