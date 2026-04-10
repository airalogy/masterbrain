// File types
export interface FileEntry {
  name: string;
  path: string;
  content: string;
  type: 'aimd' | 'py' | 'other';
  isManual?: boolean; // created/added by user (not from ZIP)
}

export interface WorkspaceState {
  mode: 'directory';
  has_workspace: boolean;
  root_path: string | null;
  files: FileEntry[];
  folders: string[];
  entry_count: number;
  can_select_directory: boolean;
}

export interface LibraryArchiveSummary {
  id: number;
  source_name: string;
  source_path: string | null;
  kind: 'protocol' | 'records';
  sha256: string;
  imported_at: string;
  protocol_count: number;
  record_count: number;
}

export interface LibraryProtocolSummary {
  id: number;
  archive_id: number;
  protocol_id: string | null;
  protocol_version: string | null;
  protocol_name: string;
  entrypoint: string;
  archive_root: string | null;
  file_count: number;
  imported_at: string;
}

export interface LibraryRecordSummary {
  id: number;
  archive_id: number;
  record_id: string | null;
  record_version: string | null;
  protocol_id: string | null;
  protocol_version: string | null;
  sha1: string | null;
  source_path: string | null;
  source_index: number;
  embedded_protocol_root: string | null;
  imported_at: string;
}

export interface LibraryState {
  db_path: string;
  archive_count: number;
  protocol_count: number;
  record_count: number;
  archives: LibraryArchiveSummary[];
  protocols: LibraryProtocolSummary[];
  records: LibraryRecordSummary[];
}

export interface LibraryImportResult {
  archive_id: number;
  duplicate: boolean;
  source_name: string;
  source_path: string | null;
  kind: 'protocol' | 'records';
  sha256: string;
  imported_at: string;
  protocol_count: number;
  record_count: number;
}

export interface LibraryImportResponse {
  result: LibraryImportResult;
  state: LibraryState;
}

export interface LibraryProtocolPreview {
  protocol: LibraryProtocolSummary;
  files: FileEntry[];
  binary_file_count: number;
  total_file_count: number;
}

export interface LibraryRecordDetailPayload {
  id: number;
  archive_id: number;
  record_id: string | null;
  record_version: string | null;
  protocol_id: string | null;
  protocol_version: string | null;
  sha1: string | null;
  source_path: string | null;
  source_index: number;
  embedded_protocol_root: string | null;
  imported_at: string;
}

export interface LibraryRecordDetail {
  record: LibraryRecordDetailPayload;
  payload: Record<string, unknown>;
}

export interface EditorSelection {
  text: string;
  startOffset: number;
  endOffset: number;
}

export interface CodeChange {
  path: string;
  name: string;
  type: 'aimd' | 'py';
  status: 'created' | 'modified' | 'deleted';
  content: string;
  diff: string;
}

// Chat types
export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  streaming?: boolean;
  intent?: 'generate' | 'chat' | 'edit';
  aimdBlocks?: string[];
  changedFiles?: CodeChange[];
  editStatus?: 'changed' | 'no_changes';
  executionLog?: string[];
  stepPending?: boolean; // v1: waiting for user confirm/regenerate
}

// Preview state (AI-generated content shown in editor before user confirms)
export interface PreviewState {
  source: 'block' | 'change';
  content: string;
  type: 'aimd' | 'py';
  msgId: string;
  name: string;
  path?: string;
}

// Protocol generation router choice
export type ProtocolRouter = 'v3' | 'v1';

// API types
export interface ModelConfig {
  name: string;
  enable_thinking: boolean;
}

export interface ChatApiRequest {
  model: ModelConfig;
  messages: Array<{ role: string; content: string }>;
}

export interface CodeEditRequest {
  model: ModelConfig;
  prompt: string;
  files: Array<{ path: string; content: string; type: FileEntry['type'] }>;
  active_file_path?: string;
  selection?: {
    text: string;
    start_offset: number;
    end_offset: number;
  };
  chat_history: Array<{ role: MessageRole; content: string }>;
}

export interface CodeEditResponse {
  runtime: 'opencode';
  message: string;
  edit_status: 'changed' | 'no_changes';
  changed_files: CodeChange[];
  warnings: string[];
  execution_log: string[];
}

export interface ProtocolGenRequest {
  use_model: ModelConfig;
  instruction: string;
}

// Protocol debug types
export interface ProtocolDebugRequest {
  full_protocol: string;
  suspect_protocol: string;
  model: { name: string; enable_thinking: boolean; enable_search: boolean };
}

export interface ProtocolDebugResponse {
  has_errors: boolean;
  fixed_protocol: string;
  response: string;
}

export const SUPPORTED_MODELS = [
  'qwen3.5-flash',
  'qwen3.5-plus',
  'qwen3-max',
] as const;

export const DEFAULT_MODEL: ModelConfig = {
  name: 'qwen3.5-flash',
  enable_thinking: false,
};
