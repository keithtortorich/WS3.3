/**
 * Mirrors backend/app/schemas/approval.py::ApprovalRead.
 */
export interface Approval {
  id: string;
  post_id: string;
  reviewer_user_id: string | null;
  stage: string;
  status: string;
  feedback: string | null;
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
