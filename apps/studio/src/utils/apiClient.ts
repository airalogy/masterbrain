import type {
  ChatApiRequest,
  CodeEditRequest,
  CodeEditResponse,
  ProtocolGenRequest,
  ModelConfig,
  ProtocolDebugRequest,
  ProtocolDebugResponse,
} from '../types';

async function readApiError(res: Response): Promise<string> {
  const fallback = `API error ${res.status}`;
  const contentType = res.headers.get('content-type') ?? '';

  try {
    if (contentType.includes('application/json')) {
      const payload = await res.json();
      const detail = extractErrorDetail(payload);
      return detail ? `API error ${res.status}: ${detail}` : fallback;
    }

    const text = (await res.text()).trim();
    if (!text) return fallback;

    try {
      const parsed = JSON.parse(text);
      const detail = extractErrorDetail(parsed);
      return detail ? `API error ${res.status}: ${detail}` : `API error ${res.status}: ${text}`;
    } catch {
      return `API error ${res.status}: ${text}`;
    }
  } catch {
    return fallback;
  }
}

function extractErrorDetail(payload: unknown): string | null {
  if (typeof payload === 'string') return payload;
  if (!payload || typeof payload !== 'object') return null;

  const record = payload as Record<string, unknown>;
  const detail = record.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') {
    const nestedDetail = extractErrorDetail(detail);
    if (nestedDetail) return nestedDetail;
  }

  const error = record.error;
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object') {
    const errorRecord = error as Record<string, unknown>;
    if (typeof errorRecord.message === 'string') return errorRecord.message;
  }

  const message = record.message;
  if (typeof message === 'string') return message;

  return null;
}

async function requestTextStream(url: string, body: unknown): Promise<ReadableStream<Uint8Array>> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  if (!res.body) {
    throw new Error('API returned an empty response body.');
  }

  return res.body;
}

async function requestJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(await readApiError(res));
  }

  return res.json() as Promise<T>;
}

export async function* streamChatLanguage(req: ChatApiRequest): AsyncGenerator<string> {
  const body = await requestTextStream('/api/endpoints/chat/qa/language', req);
  yield* readStream(body);
}

export async function runCodeEdit(req: CodeEditRequest): Promise<CodeEditResponse> {
  return requestJson<CodeEditResponse>('/api/endpoints/code_edit', req);
}

/** Protocol generation v3 - single unified .aimd file */
export async function* streamProtocolGenV3(req: ProtocolGenRequest): AsyncGenerator<string> {
  const body = await requestTextStream('/api/endpoints/single_protocol_file_generation', req);
  yield* readStream(body);
}

/** Protocol generation v1 - step 1: generate protocol.aimd */
export async function* streamProtocolGenAimd(req: ProtocolGenRequest): AsyncGenerator<string> {
  const body = await requestTextStream('/api/endpoints/protocol_generation/aimd', req);
  yield* readStream(body);
}

/** Protocol generation v1 - step 2: generate model.py */
export async function* streamProtocolGenModel(req: {
  use_model: ModelConfig;
  protocol_aimd?: string;
}): AsyncGenerator<string> {
  const body = await requestTextStream('/api/endpoints/protocol_generation/model', req);
  yield* readStream(body);
}

/** Protocol generation v1 - step 3: generate assigner.py */
export async function* streamProtocolGenAssigner(req: {
  use_model: ModelConfig;
  protocol_aimd?: string;
  protocol_model?: string;
}): AsyncGenerator<string> {
  const body = await requestTextStream('/api/endpoints/protocol_generation/assigner', req);
  yield* readStream(body);
}

/** Protocol debug - syntax check and fix */
export async function debugProtocol(req: ProtocolDebugRequest): Promise<ProtocolDebugResponse> {
  return requestJson<ProtocolDebugResponse>('/api/endpoints/protocol_debug', req);
}

async function* readStream(body: ReadableStream<Uint8Array>): AsyncGenerator<string> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      yield decoder.decode(value, { stream: true });
    }
  } finally {
    reader.releaseLock();
  }
}

/** Extract all ```aimd ... ``` code blocks */
export function extractAimdBlocks(text: string): string[] {
  const regex = /```aimd\n([\s\S]*?)```/g;
  const blocks: string[] = [];
  let match;
  while ((match = regex.exec(text)) !== null) {
    blocks.push(match[1].trimEnd());
  }
  return blocks;
}

/** Extract all ```python/py ... ``` code blocks */
export function extractPyBlocks(text: string): string[] {
  const regex = /```(?:python|py)\n([\s\S]*?)```/g;
  const blocks: string[] = [];
  let match;
  while ((match = regex.exec(text)) !== null) {
    blocks.push(match[1].trimEnd());
  }
  return blocks;
}
