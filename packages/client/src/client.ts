import { normalizeCodeEditResponse } from './contract.js';
import type { CodeEditRequest, CodeEditResponse, MasterbrainTransport } from './types.js';

export interface RunCodeEditOptions {
  signal?: AbortSignal;
}

export class MasterbrainClient {
  constructor(private readonly transport: MasterbrainTransport) {}

  async runCodeEdit(
    request: CodeEditRequest,
    options: RunCodeEditOptions = {},
  ): Promise<CodeEditResponse> {
    const raw = await this.transport({
      method: 'POST',
      path: '/api/endpoints/code_edit',
      body: request,
      ...(options.signal ? { signal: options.signal } : {}),
    });
    return normalizeCodeEditResponse(raw);
  }
}
