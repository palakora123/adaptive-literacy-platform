/**
 * Thin fetch wrapper for the FastAPI backend.
 *
 * Requests go to /api/* and next.config.ts rewrites them to the backend, so
 * the browser never needs to know the backend origin.
 */

export class ApiError extends Error {
  status: number;
  /** Machine-readable code from voice endpoints, e.g. "not_configured". */
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

function authHeaders(token: string | null): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseError(res: Response): Promise<ApiError> {
  let message = `Request failed (${res.status})`;
  let code: string | undefined;
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === 'string') {
      message = detail;
    } else if (detail && typeof detail === 'object') {
      // Voice endpoints return {code, message} so the UI can branch on code.
      message = detail.message ?? message;
      code = detail.code;
    }
  } catch {
    // Non-JSON error body (proxy failure, HTML error page) - keep the default.
  }
  return new ApiError(message, res.status, code);
}

export async function apiGet<T>(path: string, token: string | null): Promise<T> {
  const res = await fetch(`/api${path}`, { headers: authHeaders(token) });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<T>;
}

export async function apiSend<T>(
  path: string,
  token: string | null,
  body?: unknown,
  method: 'POST' | 'PUT' | 'DELETE' = 'POST',
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(token),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<T>;
}

/** Multipart upload, used for sending recorded audio to /voice/transcribe. */
export async function apiUpload<T>(
  path: string,
  token: string | null,
  form: FormData,
): Promise<T> {
  // Do not set Content-Type - the browser must add the multipart boundary.
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: authHeaders(token),
    body: form,
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<T>;
}
