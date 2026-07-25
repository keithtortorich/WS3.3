/** Mirrors backend/app/schemas/campaign.py::CampaignRead exactly. */
export type CampaignStatus = "draft" | "active" | "paused" | "completed" | "archived";

export interface Campaign {
  id: string;
  organization_id: string;
  client_id: string;
  brand_id: string | null;
  name: string;
  goal: string | null;
  status: CampaignStatus;
  start_date: string | null;
  end_date: string | null;
  budget_cents: number | null;
  created_at: string;
  updated_at: string;
}

/** Mirrors backend/app/schemas/common.py::Page[T]. */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
