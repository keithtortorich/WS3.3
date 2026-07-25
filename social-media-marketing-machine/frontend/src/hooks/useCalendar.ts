"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { CalendarEntry } from "@/types/calendar";

interface UseCalendarParams {
  startDate?: string;
  endDate?: string;
  campaignId?: string;
  token?: string;
}

/**
 * Fetches calendar entries from GET {API_BASE}/api/v1/calendar.
 *
 * Defaults to the current month when dates are not provided, which keeps
 * the page usable on first render without requiring route params.
 */
export function useCalendar({
  startDate,
  endDate,
  campaignId,
  token,
}: UseCalendarParams = {}) {
  const now = new Date();
  const defaultStart = startDate ?? new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
  const defaultEnd = endDate ?? new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10);

  const params = new URLSearchParams({
    start_date: defaultStart,
    end_date: defaultEnd,
  });
  if (campaignId) params.set("campaign_id", campaignId);

  return useQuery<CalendarEntry[]>({
    queryKey: ["calendar", { startDate: defaultStart, endDate: defaultEnd, campaignId }],
    queryFn: () => apiFetch<CalendarEntry[]>(`/api/v1/calendar?${params.toString()}`, { token }),
  });
}
