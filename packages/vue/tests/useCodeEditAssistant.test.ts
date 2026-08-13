import { sha256Hex, type CodeEditResponse, type WorkspaceAdapter, type WorkspaceFile, type WorkspaceMutation } from '@airalogy/masterbrain-client';
import { describe, expect, it } from 'vitest';
import { useCodeEditAssistant } from '../src/useCodeEditAssistant.js';

class MemoryWorkspace implements WorkspaceAdapter {
  file: WorkspaceFile = { path: 'protocol.aimd', type: 'aimd', content: '# Before' };
  readFile(): WorkspaceFile { return this.file; }
  async applyMutations(mutations: readonly WorkspaceMutation[]): Promise<void> {
    const mutation = mutations[0];
    if (!mutation) return;
    this.file = { path: mutation.path, type: mutation.type, content: mutation.content };
  }
}

async function safeResponse(): Promise<CodeEditResponse> {
  return {
    runtime: 'opencode',
    contract_version: '1',
    outcome: 'changed',
    change_set_id: `sha256:${'c'.repeat(64)}`,
    message: 'Changed the title.',
    edit_status: 'changed',
    changed_files: [{
      path: 'protocol.aimd', name: 'protocol.aimd', type: 'aimd', status: 'modified',
      content: '# After', diff: '-# Before\n+# After',
      before_hash: await sha256Hex('# Before'), after_hash: await sha256Hex('# After'),
    }],
    warnings: [],
    execution_log: [],
    risk: { level: 'safe', reasons: [], recommended_action: 'auto_apply' },
  };
}

describe('useCodeEditAssistant', () => {
  it('auto-applies safe edits and exposes undo state', async () => {
    const workspace = new MemoryWorkspace();
    const assistant = useCodeEditAssistant({
      client: { runCodeEdit: safeResponse },
      workspace,
    });
    const result = await assistant.submit({
      model: { name: 'qwen3.5-flash', enable_thinking: false },
      prompt: 'Change the title.',
      files: [workspace.file],
    });
    expect(result.status).toBe('applied');
    expect(assistant.status.value).toBe('applied');
    expect(workspace.file.content).toBe('# After');
    await assistant.undoLatest();
    expect(workspace.file.content).toBe('# Before');
  });

  it('can force every edit into host review mode', async () => {
    const workspace = new MemoryWorkspace();
    const assistant = useCodeEditAssistant({
      client: { runCodeEdit: safeResponse },
      workspace,
      autoApply: false,
    });
    expect((await assistant.submit({
      model: { name: 'qwen3.5-flash', enable_thinking: false },
      prompt: 'Change the title.',
      files: [workspace.file],
    })).status).toBe('review');
    expect(workspace.file.content).toBe('# Before');
  });

  it('holds warning changes for review and applies them only on request', async () => {
    const workspace = new MemoryWorkspace();
    const response = await safeResponse();
    response.risk = {
      level: 'warning',
      reasons: ['A deterministic validation warning was reported.'],
      recommended_action: 'review',
    };
    const assistant = useCodeEditAssistant({
      client: { runCodeEdit: async () => response },
      workspace,
    });

    expect((await assistant.submit({
      model: { name: 'qwen3.5-flash', enable_thinking: false },
      prompt: 'Change the title.',
      files: [workspace.file],
    })).status).toBe('review');
    expect(workspace.file.content).toBe('# Before');
    await assistant.applyPending();
    expect(workspace.file.content).toBe('# After');
  });

  it('returns conversational answers without touching the workspace', async () => {
    const workspace = new MemoryWorkspace();
    const answer: CodeEditResponse = {
      runtime: 'opencode',
      contract_version: '1',
      outcome: 'answer',
      change_set_id: null,
      message: 'This protocol records a sample name.',
      edit_status: 'no_changes',
      changed_files: [],
      warnings: [],
      execution_log: [],
      risk: { level: 'safe', reasons: [], recommended_action: 'auto_apply' },
    };
    const assistant = useCodeEditAssistant({
      client: { runCodeEdit: async () => answer },
      workspace,
    });

    expect((await assistant.submit({
      model: { name: 'qwen3.5-flash', enable_thinking: false },
      prompt: 'What does this protocol do?',
      files: [workspace.file],
    })).status).toBe('answer');
    expect(workspace.file.content).toBe('# Before');
  });
});
