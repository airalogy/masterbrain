import { MasterbrainApiError } from './errors.js';
import type { MasterbrainTransport } from './types.js';

export interface FetchTransportOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
  headers?: HeadersInit | (() => HeadersInit | Promise<HeadersInit>);
}

function extractErrorDetail(payload: unknown): string | null {
  if (typeof payload === 'string') return payload;
  if (!payload || typeof payload !== 'object') return null;
  const item = payload as Record<string, unknown>;
  for (const key of ['detail', 'message', 'error']) {
    const candidate = item[key];
    if (typeof candidate === 'string') return candidate;
    const nested = extractErrorDetail(candidate);
    if (nested) return nested;
  }
  return null;
}

export function createFetchTransport(options: FetchTransportOptions = {}): MasterbrainTransport {
  const fetchImpl = options.fetch ?? globalThis.fetch;
  if (!fetchImpl) throw new Error('A fetch implementation is required.');
  const baseUrl = (options.baseUrl ?? '').replace(/\/$/, '');

  return async request => {
    const configuredHeaders = typeof options.headers === 'function'
      ? await options.headers()
      : options.headers;
    const headers = new Headers(configuredHeaders);
    headers.set('Content-Type', 'application/json');
    const response = await fetchImpl(`${baseUrl}${request.path}`, {
      method: request.method,
      headers,
      body: JSON.stringify(request.body),
      ...(request.signal ? { signal: request.signal } : {}),
    });
    const contentType = response.headers.get('content-type') ?? '';
    const payload = contentType.includes('application/json')
      ? await response.json()
      : await response.text();
    if (!response.ok) {
      const detail = extractErrorDetail(payload);
      throw new MasterbrainApiError(
        detail ? `Masterbrain API ${response.status}: ${detail}` : `Masterbrain API ${response.status}`,
        response.status,
        payload,
      );
    }
    return payload;
  };
}
