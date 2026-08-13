export type MaybePromise<T> = T | Promise<T>;

export type WorkspaceFileType = 'aimd' | 'py' | 'toml' | 'other';
export type ChangedFileType = Exclude<WorkspaceFileType, 'other'>;
export type ChangedFileStatus = 'created' | 'modified' | 'deleted';
export type RiskLevel = 'safe' | 'warning' | 'destructive';
export type RecommendedAction = 'auto_apply' | 'review' | 'block';

export interface ModelConfig {
  name: string;
  enable_thinking: boolean;
}

export interface WorkspaceFile {
  path: string;
  content: string;
  type: WorkspaceFileType;
}

export interface EditorSelection {
  text: string;
  start_offset: number;
  end_offset: number;
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface CodeEditRequest {
  model: ModelConfig;
  prompt: string;
  workspace_id?: string;
  files: WorkspaceFile[];
  active_file_path?: string;
  selection?: EditorSelection;
  chat_history?: ChatHistoryMessage[];
}

export interface CodeEditChangedFile {
  path: string;
  name: string;
  type: ChangedFileType;
  status: ChangedFileStatus;
  content: string;
  diff: string;
  before_hash?: string | null;
  after_hash?: string | null;
}

export interface CodeEditRisk {
  level: RiskLevel;
  reasons: string[];
  recommended_action: RecommendedAction;
}

export interface CodeEditResponse {
  runtime: 'opencode';
  contract_version: '1';
  outcome: 'answer' | 'changed';
  change_set_id: string | null;
  message: string;
  /** @deprecated Prefer outcome. Retained for older consumers. */
  edit_status: 'changed' | 'no_changes';
  changed_files: CodeEditChangedFile[];
  warnings: string[];
  execution_log: string[];
  risk: CodeEditRisk;
}

export interface TransportRequest {
  method: 'POST';
  path: string;
  body: unknown;
  signal?: AbortSignal;
}

export type MasterbrainTransport = (request: TransportRequest) => Promise<unknown>;

export interface WorkspaceMutation {
  path: string;
  type: ChangedFileType;
  status: ChangedFileStatus;
  content: string;
  expected_hash?: string | null;
}

export interface WorkspaceMutationContext {
  changeSetId: string | null;
  operation: 'apply' | 'undo';
}

export interface WorkspaceAdapter {
  readFile(path: string): MaybePromise<WorkspaceFile | null>;
  applyMutations(
    mutations: readonly WorkspaceMutation[],
    context: WorkspaceMutationContext,
  ): Promise<void>;
}

export interface AppliedFileSnapshot {
  path: string;
  type: ChangedFileType;
  before: WorkspaceFile | null;
  beforeHash: string | null;
  afterHash: string | null;
}

export interface AppliedChangeSet {
  id: string | null;
  response: CodeEditResponse;
  files: AppliedFileSnapshot[];
}

export type CodeEditApplicationResult =
  | { status: 'answer'; response: CodeEditResponse }
  | { status: 'review'; response: CodeEditResponse }
  | { status: 'blocked'; response: CodeEditResponse }
  | { status: 'applied'; response: CodeEditResponse; applied: AppliedChangeSet };
