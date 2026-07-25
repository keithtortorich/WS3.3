export interface AgentTemplate {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  template_body: string;
  variables: string[] | null;
  category: string | null;
  version: number;
  is_active: boolean;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface UseAgentTemplatesParams {
  category?: string;
  token?: string;
}

export interface AgentCategoryItem {
  slug: string | null;
  label: string;
  description: string;
}
