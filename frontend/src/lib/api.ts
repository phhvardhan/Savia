/**
 * Thin fetch wrapper around the SAVIA FastAPI backend.
 *
 * Two backend quirks this file exists to absorb:
 *
 * 1. Routes that go through `app/utils/response.py` return HTTP 200 with the
 *    *real* status nested in the body: `{status_code, content: {success, message,
 *    data, errors}}`. So `res.ok` tells us nothing — a failed login is a 200.
 *    `request()` unwraps that envelope and throws on `success: false`.
 * 2. Routes guarded by `require_authenticated_user` (only /auth/me today) raise
 *    a real FastAPI 401 with a plain `{detail}` body instead of the envelope.
 *
 * Both shapes end up as an ApiError with a usable `.message` and `.status`.
 */

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

const TOKEN_KEY = 'savia.token';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    // Safari in private mode throws on localStorage access.
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token === null) localStorage.removeItem(TOKEN_KEY);
    else localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* non-fatal — the session just won't survive a reload */
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Skip attaching the bearer token (used by login itself). */
  anonymous?: boolean;
  /** Abort after this many ms. Agent runs are slow, so they set it high. */
  timeoutMs?: number;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, anonymous = false, timeoutMs } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const token = anonymous ? null : getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const controller = timeoutMs ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller?.signal,
    });
  } catch (caught) {
    if (caught instanceof DOMException && caught.name === 'AbortError') {
      throw new ApiError(
        `The agent did not answer within ${Math.round((timeoutMs ?? 0) / 1000)} seconds.`,
        0,
      );
    }
    throw new ApiError('Could not reach the SAVIA server. Is the backend running?', 0);
  } finally {
    if (timer) clearTimeout(timer);
  }

  const text = await res.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      throw new ApiError(`Unexpected response from the server (${res.status}).`, res.status);
    }
  }

  // Shape 2: a real FastAPI error, e.g. {"detail": "Authentication required."}
  if (!res.ok) {
    const detail = (payload as { detail?: unknown } | null)?.detail;
    throw new ApiError(typeof detail === 'string' ? detail : `Request failed (${res.status}).`, res.status);
  }

  // Shape 1: the {status_code, content} envelope.
  const envelope = payload as
    | { status_code?: number; content?: { success?: boolean; message?: string; data?: unknown } }
    | null;

  // Match on the WHOLE envelope signature, not just a `content` key. An agent
  // run replies with its own top-level `content` (the artifact body), and
  // treating that as the envelope returned `content.data` — undefined.
  const isEnvelope =
    envelope !== null &&
    typeof envelope === 'object' &&
    'status_code' in envelope &&
    typeof envelope.content === 'object' &&
    envelope.content !== null &&
    'success' in envelope.content;

  if (isEnvelope) {
    const { success, message, data } = envelope.content as {
      success?: boolean;
      message?: string;
      data?: unknown;
    };
    const status = envelope.status_code ?? res.status;
    if (success === false) {
      throw new ApiError(message || 'Request failed.', status);
    }
    return data as T;
  }

  // Routes that return their model directly (agents, ingestion, meetings…).
  return payload as T;
}

/**
 * Multipart POST for file ingestion. Kept separate from `request` because the
 * browser must set its own Content-Type so the multipart boundary is correct.
 */
export async function uploadFile<T>(path: string, file: File): Promise<T> {
  const body = new FormData();
  body.append('file', file);

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { method: 'POST', headers, body });
  } catch {
    throw new ApiError('Could not reach the SAVIA server. Is the backend running?', 0);
  }

  const text = await res.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      throw new ApiError(`Unexpected response from the server (${res.status}).`, res.status);
    }
  }

  if (!res.ok) {
    const detail = (payload as { detail?: unknown } | null)?.detail;
    throw new ApiError(typeof detail === 'string' ? detail : `Upload failed (${res.status}).`, res.status);
  }

  return payload as T;
}
