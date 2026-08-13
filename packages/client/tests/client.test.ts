import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import {
  MasterbrainClient,
  WorkspaceConflictError,
  applyCodeEditResponse,
  handleCodeEditResponse,
  normalizeCodeEditResponse,
  sha256Hex,
  undoAppliedChangeSet,
  type CodeEditResponse,
  type WorkspaceAdapter,
  type WorkspaceFile,
  type WorkspaceMutation,
} from '../src/index.js';

function response(overrides: Partial<CodeEditResponse> = {}): CodeEditResponse {
  return {
    runtime: 'opencode',
    contract_version: '1',
    outcome: 'answer',
    change_set_id: null,
    message: 'No edits needed.',
    edit_status: 'no_changes',
    changed_files: [],
    warnings: [],
    execution_log: [],
    risk: { level: 'safe', reasons: [], recommended_action: 'auto_apply' },
    ...overrides,
  };
}

class MemoryWorkspace implements WorkspaceAdapter {
  readonly files = new Map<string, WorkspaceFile>();
  readonly contexts: string[] = [];

  constructor(files: WorkspaceFile[]) {
    for (const file of files) this.files.set(file.path, file);
  }

  readFile(path: string): WorkspaceFile | null {
    return this.files.get(path) ?? null;
  }

  async applyMutations(mutations: readonly WorkspaceMutation[], context: { operation: 'apply' | 'undo' }): Promise<void> {
    this.contexts.push(context.operation);
    for (const mutation of mutations) {
      if (mutation.status === 'deleted') this.files.delete(mutation.path);
      else this.files.set(mutation.path, {
        path: mutation.path,
        type: mutation.type,
        content: mutation.content,
      });
    }
  }
}

describe('code edit contract', () => {
  it('keeps the TypeScript surface aligned with the generated Python schema', () => {
    const schema = JSON.parse(readFileSync(
      new URL('../schema/code-edit.v1.schema.json', import.meta.url),
      'utf8',
    )) as {
      request: { properties: Record<string, unknown> };
      response: {
        properties: Record<string, unknown>;
        $defs: { CodeEditChangedFile: { properties: Record<string, unknown> } };
      };
    };
    expect(Object.keys(schema.request.properties).sort()).toEqual([
      'active_file_path', 'chat_history', 'files', 'model', 'prompt', 'selection', 'workspace_id',
    ]);
    expect(Object.keys(schema.response.properties).sort()).toEqual([
      'change_set_id', 'changed_files', 'contract_version', 'edit_status', 'execution_log',
      'message', 'outcome', 'risk', 'runtime', 'warnings',
    ]);
    expect(Object.keys(schema.response.$defs.CodeEditChangedFile.properties).sort()).toEqual([
      'after_hash', 'before_hash', 'content', 'diff', 'name', 'path', 'status', 'type',
    ]);
  });

  it('normalizes legacy responses and infers review for deletes', () => {
    const result = normalizeCodeEditResponse({
      runtime: 'opencode',
      message: 'Removed the assigner.',
      edit_status: 'changed',
      changed_files: [{
        path: 'assigner.py',
        name: 'assigner.py',
        type: 'py',
        status: 'deleted',
        content: '',
        diff: '-old',
      }],
      warnings: [],
      execution_log: [],
    });

    expect(result.contract_version).toBe('1');
    expect(result.outcome).toBe('changed');
    expect(result.risk.level).toBe('destructive');
    expect(result.risk.recommended_action).toBe('review');
  });

  it('rejects response metadata that contradicts changed_files', () => {
    expect(() => normalizeCodeEditResponse({
      runtime: 'opencode',
      message: 'Contradictory response.',
      outcome: 'answer',
      edit_status: 'no_changes',
      changed_files: [{
        path: 'protocol.aimd', name: 'protocol.aimd', type: 'aimd', status: 'modified',
        content: '# After', diff: '',
      }],
      warnings: [],
      execution_log: [],
    })).toThrow(/does not match changed_files/);
  });

  it('rejects malformed conflict hashes at the contract boundary', () => {
    expect(() => normalizeCodeEditResponse({
      runtime: 'opencode',
      message: 'Changed the title.',
      edit_status: 'changed',
      changed_files: [{
        path: 'protocol.aimd', name: 'protocol.aimd', type: 'aimd', status: 'modified',
        content: '# After', diff: '', before_hash: 'not-a-hash',
      }],
      warnings: [],
      execution_log: [],
    })).toThrow(/lowercase SHA-256/);
  });

  it('uses an injected transport', async () => {
    const client = new MasterbrainClient(async request => {
      expect(request.path).toBe('/api/endpoints/code_edit');
      return response();
    });
    const result = await client.runCodeEdit({
      model: { name: 'qwen3.5-flash', enable_thinking: false },
      prompt: 'Explain this protocol.',
      files: [],
    });
    expect(result.outcome).toBe('answer');
  });
});

describe('workspace changes', () => {
  it('auto-applies safe changes and supports conflict-safe undo', async () => {
    const before = '# Before';
    const after = '# After';
    const workspace = new MemoryWorkspace([{ path: 'protocol.aimd', type: 'aimd', content: before }]);
    const result = response({
      outcome: 'changed',
      edit_status: 'changed',
      change_set_id: `sha256:${'c'.repeat(64)}`,
      changed_files: [{
        path: 'protocol.aimd',
        name: 'protocol.aimd',
        type: 'aimd',
        status: 'modified',
        content: after,
        diff: '-# Before\n+# After',
        before_hash: await sha256Hex(before),
        after_hash: await sha256Hex(after),
      }],
    });

    const handled = await handleCodeEditResponse(result, workspace);
    expect(handled.status).toBe('applied');
    expect(workspace.readFile('protocol.aimd')?.content).toBe(after);
    if (handled.status !== 'applied') throw new Error('Expected applied result.');
    await undoAppliedChangeSet(handled.applied, workspace);
    expect(workspace.readFile('protocol.aimd')?.content).toBe(before);
    expect(workspace.contexts).toEqual(['apply', 'undo']);
  });

  it('restores a deleted file as a create mutation during undo', async () => {
    const before = 'value = 1\n';
    const workspace = new MemoryWorkspace([{ path: 'model.py', type: 'py', content: before }]);
    const result = response({
      outcome: 'changed',
      edit_status: 'changed',
      risk: { level: 'destructive', reasons: ['Deletes workspace file: model.py'], recommended_action: 'review' },
      changed_files: [{
        path: 'model.py', name: 'model.py', type: 'py', status: 'deleted', content: '', diff: `-${before}`,
        before_hash: await sha256Hex(before), after_hash: null,
      }],
    });

    const applied = await applyCodeEditResponse(result, workspace);
    expect(workspace.readFile('model.py')).toBeNull();
    await undoAppliedChangeSet(applied, workspace);
    expect(workspace.readFile('model.py')?.content).toBe(before);
  });

  it('derives the after hash so legacy changes can still be undone safely', async () => {
    const workspace = new MemoryWorkspace([{ path: 'protocol.aimd', type: 'aimd', content: '# Before' }]);
    const legacy = normalizeCodeEditResponse({
      runtime: 'opencode',
      message: 'Changed the title.',
      edit_status: 'changed',
      changed_files: [{
        path: 'protocol.aimd', name: 'protocol.aimd', type: 'aimd', status: 'modified',
        content: '# After', diff: '-# Before\n+# After',
      }],
      warnings: [],
      execution_log: [],
    });

    const applied = await applyCodeEditResponse(legacy, workspace);
    await undoAppliedChangeSet(applied, workspace);
    expect(workspace.readFile('protocol.aimd')?.content).toBe('# Before');
  });

  it('rejects applying over a file changed after the request', async () => {
    const workspace = new MemoryWorkspace([{ path: 'model.py', type: 'py', content: 'new local' }]);
    const result = response({
      outcome: 'changed',
      edit_status: 'changed',
      changed_files: [{
        path: 'model.py',
        name: 'model.py',
        type: 'py',
        status: 'modified',
        content: 'ai content',
        diff: '',
        before_hash: await sha256Hex('request snapshot'),
        after_hash: await sha256Hex('ai content'),
      }],
    });

    await expect(applyCodeEditResponse(result, workspace)).rejects.toBeInstanceOf(WorkspaceConflictError);
  });

  it('returns review without writing warning changes', async () => {
    const workspace = new MemoryWorkspace([]);
    const result = response({
      outcome: 'changed',
      edit_status: 'changed',
      risk: { level: 'warning', reasons: ['Invalid AIMD'], recommended_action: 'review' },
      changed_files: [{
        path: 'protocol.aimd',
        name: 'protocol.aimd',
        type: 'aimd',
        status: 'created',
        content: '# Draft',
        diff: '+# Draft',
        before_hash: null,
        after_hash: await sha256Hex('# Draft'),
      }],
    });
    expect((await handleCodeEditResponse(result, workspace)).status).toBe('review');
    expect(workspace.files.size).toBe(0);
  });

  it('never auto-applies a deletion even when a host supplies unsafe risk metadata', async () => {
    const workspace = new MemoryWorkspace([{ path: 'model.py', type: 'py', content: 'value = 1\n' }]);
    const result = response({
      outcome: 'changed',
      edit_status: 'changed',
      changed_files: [{
        path: 'model.py', name: 'model.py', type: 'py', status: 'deleted',
        content: '', diff: '-value = 1',
      }],
    });

    expect((await handleCodeEditResponse(result, workspace)).status).toBe('review');
    expect(workspace.readFile('model.py')).not.toBeNull();
  });
});
