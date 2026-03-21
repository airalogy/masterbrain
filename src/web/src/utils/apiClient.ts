import type { ChatApiRequest, ProtocolGenRequest, ModelConfig, ProtocolDebugRequest, ProtocolDebugResponse } from '../types';

export async function* streamChatLanguage(req: ChatApiRequest): AsyncGenerator<string> {
  const res = await fetch('/api/endpoints/chat/qa/language', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok || !res.body) throw new Error(`API error: ${res.status}`);
  yield* readStream(res.body);
}

/** Protocol generation v3 - single unified .aimd file */
export async function* streamProtocolGenV3(req: ProtocolGenRequest): AsyncGenerator<string> {
  const res = await fetch('/api/endpoints/single_protocol_file_generation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok || !res.body) throw new Error(`API error: ${res.status}`);
  yield* readStream(res.body);
}

/** Protocol generation v1 - step 1: generate protocol.aimd */
export async function* streamProtocolGenAimd(req: ProtocolGenRequest): AsyncGenerator<string> {
  const res = await fetch('/api/endpoints/protocol_generation/aimd', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok || !res.body) throw new Error(`API error: ${res.status}`);
  yield* readStream(res.body);
}

/** Protocol generation v1 - step 2: generate model.py */
export async function* streamProtocolGenModel(req: {
  use_model: ModelConfig;
  protocol_aimd?: string;
}): AsyncGenerator<string> {
  const res = await fetch('/api/endpoints/protocol_generation/model', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok || !res.body) throw new Error(`API error: ${res.status}`);
  yield* readStream(res.body);
}

/** Protocol generation v1 - step 3: generate assigner.py */
export async function* streamProtocolGenAssigner(req: {
  use_model: ModelConfig;
  protocol_aimd?: string;
  protocol_model?: string;
}): AsyncGenerator<string> {
  const res = await fetch('/api/endpoints/protocol_generation/assigner', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok || !res.body) throw new Error(`API error: ${res.status}`);
  yield* readStream(res.body);
}

/** Protocol debug - syntax check and fix */
export async function debugProtocol(req: ProtocolDebugRequest): Promise<ProtocolDebugResponse> {
  const res = await fetch('/api/endpoints/protocol_debug', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
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

/** Detect user intent from message text */
export function detectIntent(text: string): 'generate' | 'chat' {
  const lower = text.toLowerCase();
  const generatePatterns = [
    '生成', '创建', '新建', '制作', '写一个协议', '写个协议', '帮我写',
    'generate protocol', 'create protocol', 'new protocol', 'write a protocol', 'build protocol',
  ];
  if (generatePatterns.some(p => lower.includes(p))) return 'generate';
  return 'chat';
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
