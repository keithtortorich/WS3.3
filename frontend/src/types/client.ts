/** Mirrors backend/app/schemas/client.py::ClientRead exactly. */
export interface Client {
  id: string;
  organization_id: string;
  name: string;
  industry: string | null;
  website_url: string | null;
  contact_name: string | null;
  contact_email: string | null;
  notes: string | null;
  is_active: boolean;
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
