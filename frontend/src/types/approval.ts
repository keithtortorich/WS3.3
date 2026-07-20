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
