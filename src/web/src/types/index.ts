// File types
export interface FileEntry {
  name: string;
  path: string;
  content: string;
  type: 'aimd' | 'py' | 'other';
  isManual?: boolean; // created/added by user (not from ZIP)
}

// Chat types
export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  streaming?: boolean;
  intent?: 'generate' | 'chat';
  aimdBlocks?: string[];
  stepPending?: boolean; // v1: waiting for user confirm/regenerate
}

// Preview state (AI-generated content shown in editor before user confirms)
export interface PreviewState {
  content: string;
  type: 'aimd' | 'py';
  msgId: string;
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
