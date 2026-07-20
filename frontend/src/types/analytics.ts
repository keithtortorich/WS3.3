/**
 * Mirrors backend/app/schemas/analytics.py::AnalyticsRead.
 */
export interface AnalyticsSnapshot {
  id: string;
  post_id: string;
  captured_at: string;
  impressions: number;
  likes: number;
  comments_count: number;
  shares: number;
  clicks: number;
  engagement_rate: number | null;
}

/**
 * Mirrors backend/app/schemas/analytics.py::CampaignAnalyticsSummary.
 */
export interface CampaignAnalyticsSummary {
  campaign_id: string;
  total_posts: number;
  total_impressions: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_clicks: number;
  average_engagement_rate: number | null;
}
