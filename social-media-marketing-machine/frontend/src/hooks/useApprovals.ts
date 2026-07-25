"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { Approval, Page } from "@/types/approval";

interface UseApprovalsParams {
  postId?: string;
  page?: number;
  pageSize?: number;
  token?: string;
}

/**
 * Fetches approvals from GET {API_BASE}/api/v1/approvals/posts/{post_id}.
 *
 * Defaults to no postId, which may not return useful data from the current
 * backend shape; the page shell is designed around a context-aware
 * postId once approvals are navigated from a post detail context.
 */
export function useApprovals({
  postId,
  page = 1,
  pageSize = 20,
  token,
}: UseApprovalsParams = {}) {
  const path =
    postId && postId.trim().length > 0
      ? `/api/v1/approvals/posts/${postId}?page=${page}&page_size=${pageSize}`
      : `/api/v1/approvals/posts?page=${page}&page_size=${pageSize}`;

  return useQuery<Page<Approval>>({
    queryKey: ["approvals", { postId, page, pageSize }],
    queryFn: () => apiFetch<Page<Approval>>(path, { token }),
  });
}
