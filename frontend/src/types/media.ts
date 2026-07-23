/** Mirrors backend/app/schemas/media.py::MediaRead. */
export type MediaType = "image" | "video" | "gif" | "document";

export interface Media {
  id: string;
  organization_id: string;
  post_id: string | null;
  media_type: MediaType;
  url: string;
  mime_type: string | null;
  size_bytes: number | null;
  width: number | null;
  height: number | null;
  alt_text: string | null;
  ai_generated: boolean;
  created_at: string;
}

/** Mirrors backend/app/schemas/common.py::Page[T]. */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
