import { MasterbrainContractError } from './errors.js';
import type {
  CodeEditChangedFile,
  CodeEditResponse,
  CodeEditRisk,
  RecommendedAction,
  RiskLevel,
} from './types.js';

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new MasterbrainContractError(`${label} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, label: string): string {
  if (typeof value !== 'string') {
    throw new MasterbrainContractError(`${label} must be a string.`);
  }
  return value;
}

function stringArray(value: unknown, label: string): string[] {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.some(item => typeof item !== 'string')) {
    throw new MasterbrainContractError(`${label} must be an array of strings.`);
  }
  return [...value] as string[];
}

function oneOf<T extends string>(value: unknown, values: readonly T[], label: string): T {
  if (typeof value !== 'string' || !values.includes(value as T)) {
    throw new MasterbrainContractError(`${label} has an unsupported value.`);
  }
  return value as T;
}

function nullableText(value: unknown, label: string): string | null {
  if (value === undefined || value === null) return null;
  return text(value, label);
}

function nullableSha256(value: unknown, label: string): string | null {
  const result = nullableText(value, label);
  if (result !== null && !/^[0-9a-f]{64}$/.test(result)) {
    throw new MasterbrainContractError(`${label} must be a lowercase SHA-256 digest.`);
  }
  return result;
}

function normalizeChangedFile(value: unknown, index: number): CodeEditChangedFile {
  const item = record(value, `changed_files[${index}]`);
  const beforeHash = item.before_hash === undefined
    ? undefined
    : nullableSha256(item.before_hash, `changed_files[${index}].before_hash`);
  const afterHash = item.after_hash === undefined
    ? undefined
    : nullableSha256(item.after_hash, `changed_files[${index}].after_hash`);
  return {
    path: text(item.path, `changed_files[${index}].path`),
    name: text(item.name, `changed_files[${index}].name`),
    type: oneOf(item.type, ['aimd', 'py', 'toml'] as const, `changed_files[${index}].type`),
    status: oneOf(item.status, ['created', 'modified', 'deleted'] as const, `changed_files[${index}].status`),
    content: text(item.content ?? '', `changed_files[${index}].content`),
    diff: text(item.diff ?? '', `changed_files[${index}].diff`),
    ...(beforeHash !== undefined ? { before_hash: beforeHash } : {}),
    ...(afterHash !== undefined ? { after_hash: afterHash } : {}),
  };
}

function inferRisk(changes: CodeEditChangedFile[], warnings: string[]): CodeEditRisk {
  const deleted = changes.filter(change => change.status === 'deleted');
  if (deleted.length > 0) {
    return {
      level: 'destructive',
      reasons: deleted.map(change => `Deletes workspace file: ${change.path}`).concat(warnings),
      recommended_action: 'review',
    };
  }
  if (warnings.length > 0) {
    return { level: 'warning', reasons: warnings, recommended_action: 'review' };
  }
  return { level: 'safe', reasons: [], recommended_action: 'auto_apply' };
}

function normalizeRisk(value: unknown, fallback: CodeEditRisk): CodeEditRisk {
  if (value === undefined) return fallback;
  const item = record(value, 'risk');
  return {
    level: oneOf<RiskLevel>(item.level, ['safe', 'warning', 'destructive'], 'risk.level'),
    reasons: stringArray(item.reasons, 'risk.reasons'),
    recommended_action: oneOf<RecommendedAction>(
      item.recommended_action,
      ['auto_apply', 'review', 'block'],
      'risk.recommended_action',
    ),
  };
}

export function normalizeCodeEditResponse(value: unknown): CodeEditResponse {
  const payload = record(value, 'Code edit response');
  const rawChanges = payload.changed_files ?? [];
  if (!Array.isArray(rawChanges)) {
    throw new MasterbrainContractError('changed_files must be an array.');
  }
  const changedFiles = rawChanges.map(normalizeChangedFile);
  const warnings = stringArray(payload.warnings, 'warnings');
  const derivedEditStatus = changedFiles.length > 0 ? 'changed' : 'no_changes';
  const editStatus = payload.edit_status === undefined
    ? derivedEditStatus
    : oneOf(payload.edit_status, ['changed', 'no_changes'] as const, 'edit_status');
  const derivedOutcome = changedFiles.length > 0 ? 'changed' : 'answer';
  const outcome = payload.outcome === undefined
    ? derivedOutcome
    : oneOf(payload.outcome, ['answer', 'changed'] as const, 'outcome');
  if (editStatus !== derivedEditStatus || outcome !== derivedOutcome) {
    throw new MasterbrainContractError('Code edit response change status does not match changed_files.');
  }
  const changeSetId = nullableText(payload.change_set_id, 'change_set_id');
  if (changeSetId !== null && !/^sha256:[0-9a-f]{64}$/.test(changeSetId)) {
    throw new MasterbrainContractError('change_set_id must be a sha256-prefixed digest.');
  }

  return {
    runtime: oneOf(payload.runtime, ['opencode'] as const, 'runtime'),
    contract_version: payload.contract_version === undefined
      ? '1'
      : oneOf(payload.contract_version, ['1'] as const, 'contract_version'),
    outcome,
    change_set_id: changeSetId,
    message: text(payload.message, 'message'),
    edit_status: editStatus,
    changed_files: changedFiles,
    warnings,
    execution_log: stringArray(payload.execution_log, 'execution_log'),
    risk: normalizeRisk(payload.risk, inferRisk(changedFiles, warnings)),
  };
}
