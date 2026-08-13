import { WorkspaceConflictError } from './errors.js';
import type {
  AppliedChangeSet,
  AppliedFileSnapshot,
  CodeEditApplicationResult,
  CodeEditResponse,
  WorkspaceAdapter,
  WorkspaceFile,
  WorkspaceMutation,
} from './types.js';

export async function sha256Hex(content: string): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new Error('Web Crypto SHA-256 support is required for workspace conflict checks.');
  }
  const bytes = new TextEncoder().encode(content);
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

async function fileHash(file: WorkspaceFile | null): Promise<string | null> {
  return file ? sha256Hex(file.content) : null;
}

async function captureAndVerify(
  response: CodeEditResponse,
  workspace: WorkspaceAdapter,
  expected: 'before_hash' | 'after_hash',
): Promise<{ snapshots: AppliedFileSnapshot[]; conflicts: string[] }> {
  const snapshots: AppliedFileSnapshot[] = [];
  const conflicts: string[] = [];
  for (const change of response.changed_files) {
    const current = await workspace.readFile(change.path);
    const currentHash = await fileHash(current);
    const expectedHash = change[expected];
    const declaredAfterHash = change.after_hash === undefined
      ? (change.status === 'deleted' ? null : await sha256Hex(change.content))
      : change.after_hash;
    if (expectedHash !== undefined) {
      if (expectedHash !== null && currentHash !== expectedHash) conflicts.push(change.path);
      if (expectedHash === null && current !== null) conflicts.push(change.path);
    }
    snapshots.push({
      path: change.path,
      type: change.type,
      before: current,
      beforeHash: expected === 'before_hash' ? currentHash : (change.before_hash ?? null),
      afterHash: expected === 'after_hash' ? currentHash : declaredAfterHash,
    });
  }
  return { snapshots, conflicts: [...new Set(conflicts)] };
}

function applyMutations(response: CodeEditResponse): WorkspaceMutation[] {
  return response.changed_files.map(change => ({
    path: change.path,
    type: change.type,
    status: change.status,
    content: change.content,
    ...(change.before_hash !== undefined ? { expected_hash: change.before_hash } : {}),
  }));
}

export async function applyCodeEditResponse(
  response: CodeEditResponse,
  workspace: WorkspaceAdapter,
): Promise<AppliedChangeSet> {
  const { snapshots, conflicts } = await captureAndVerify(response, workspace, 'before_hash');
  if (conflicts.length > 0) {
    throw new WorkspaceConflictError(
      `Workspace files changed after the AI request: ${conflicts.join(', ')}`,
      conflicts,
    );
  }
  await workspace.applyMutations(applyMutations(response), {
    changeSetId: response.change_set_id,
    operation: 'apply',
  });
  return { id: response.change_set_id, response, files: snapshots };
}

export async function undoAppliedChangeSet(
  applied: AppliedChangeSet,
  workspace: WorkspaceAdapter,
): Promise<void> {
  const { conflicts } = await captureAndVerify(applied.response, workspace, 'after_hash');
  if (conflicts.length > 0) {
    throw new WorkspaceConflictError(
      `Workspace files changed after the AI edit: ${conflicts.join(', ')}`,
      conflicts,
    );
  }
  const mutations: WorkspaceMutation[] = applied.files.map(snapshot => ({
    path: snapshot.path,
    type: snapshot.type,
    status: snapshot.before === null
      ? 'deleted'
      : snapshot.afterHash === null
        ? 'created'
        : 'modified',
    content: snapshot.before?.content ?? '',
    expected_hash: snapshot.afterHash,
  }));
  await workspace.applyMutations(mutations, {
    changeSetId: applied.id,
    operation: 'undo',
  });
}

export async function handleCodeEditResponse(
  response: CodeEditResponse,
  workspace: WorkspaceAdapter,
): Promise<CodeEditApplicationResult> {
  if (response.outcome === 'answer' || response.changed_files.length === 0) {
    return { status: 'answer', response };
  }
  if (response.risk.recommended_action === 'block') {
    return { status: 'blocked', response };
  }
  const requiresReview = response.risk.recommended_action === 'review'
    || response.risk.level !== 'safe'
    || response.warnings.length > 0
    || response.changed_files.some(change => change.status === 'deleted');
  if (requiresReview) {
    return { status: 'review', response };
  }
  const applied = await applyCodeEditResponse(response, workspace);
  return { status: 'applied', response, applied };
}
