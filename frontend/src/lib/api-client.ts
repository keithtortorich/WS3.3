import { API_BASE_URL } from "@/lib/config";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Thin fetch wrapper. Auth token attachment is intentionally NOT baked in
 * here — call sites that need an authenticated request should pass a
 * `token` (obtained from Clerk's `useAuth().getToken()`) and this function
 * attaches it as a Bearer header, matching the backend's
 * `app.core.auth.get_current_user` expectations.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers, ...rest } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }

  return (await response.json()) as T;
}
