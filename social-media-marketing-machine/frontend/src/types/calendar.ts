/**
 * Calendar entry returned by GET /api/v1/calendar.
 *
 * Mirrors the dict shape constructed in backend/app/routers/calendar.py.
 */
export interface CalendarEntry {
  schedule_id: string;
  post_id: string;
  platform_account_id: string;
  scheduled_at: string;
  platform: string;
  post_status: string;
  caption_preview: string;
}
