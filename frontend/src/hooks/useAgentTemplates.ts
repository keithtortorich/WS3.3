"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api-client";
import type { AgentTemplate } from "@/types/agents";

interface UseAgentTemplatesParams {
  category?: string;
  token?: string;
}

export function useAgentTemplates({ category, token }: UseAgentTemplatesParams = {}) {
  const params = new URLSearchParams({ page: "1", page_size: "200", active_only: "true" });
  if (category) params.set("category", category);

  return useQuery<AgentTemplate[]>({
    queryKey: ["agent-templates", { category }],
    queryFn: () =>
      apiFetch<AgentTemplate[]>(`/api/v1/agents?${params.toString()}`, { token }),
  });
}
