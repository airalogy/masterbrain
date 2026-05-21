<script setup lang="ts">
import { computed, ref } from 'vue';
import type {
  EditorSelection,
  FileEntry,
  PreviewState,
  ModelConfig,
  ProtocolDebugResponse,
} from '../../types/index.ts';
import { debugProtocol } from '../../utils/apiClient.ts';
import CodeEditor from './CodeEditor.vue';
import AimdPreview from './AimdPreview.vue';

const props = defineProps<{
  activeFile: FileEntry | null;
  previewState: PreviewState | null;
  isDark: boolean;
  model: ModelConfig;
  hasWorkspace: boolean;
}>();

const emit = defineEmits<{
  change: [content: string];
  keepPreview: [];
  discardPreview: [];
  selectionChange: [selection: EditorSelection | null];
}>();

interface DebugState {
  loading: boolean;
  result: ProtocolDebugResponse | null;
  error: string | null;
  selectionRange: { startOffset: number; endOffset: number } | null;
  originalText: string;
}

const EMPTY_DEBUG: DebugState = { loading: false, result: null, error: null, selectionRange: null, originalText: '' };

const debugState = ref<DebugState>({ ...EMPTY_DEBUG });
const selection = ref<EditorSelection | null>(null);
const viewMode = ref<'split' | 'editor' | 'preview'>('split');

function handleSelectionChange(sel: EditorSelection | null) {
  selection.value = sel;
  emit('selectionChange', sel);
}

const displayFile = computed<FileEntry | null>(() => {
  if (props.previewState) {
    return {
      name: props.previewState.name,
      path: props.previewState.path ?? '__preview__',
      content: props.previewState.content,
      type: props.previewState.type,
    };
  }
  return props.activeFile;
});

const lineCount = computed(() => {
  if (!displayFile.value) return 0;
  return displayFile.value.content.split('\n').length;
});

const typeLabel = computed(() => {
  if (!displayFile.value) return 'FILE';
  if (displayFile.value.type === 'aimd') return 'AIMD';
  if (displayFile.value.type === 'py') return 'PY';
  return 'TXT';
});

async function handleDebug() {
  if (!props.activeFile || props.activeFile.type !== 'aimd' || !selection.value) return;
  const range = { startOffset: selection.value.startOffset, endOffset: selection.value.endOffset };
  debugState.value = { loading: true, result: null, error: null, selectionRange: range, originalText: selection.value.text };
  try {
    const result = await debugProtocol({
      full_protocol: props.activeFile.content,
      suspect_protocol: selection.value.text,
      model: { name: props.model.name, enable_thinking: props.model.enable_thinking, enable_search: false },
    });
    debugState.value = { loading: false, result, error: null, selectionRange: range, originalText: selection.value!.text };
  } catch (e: unknown) {
    const error = e instanceof Error ? e.message : 'Debug failed';
    debugState.value = { loading: false, result: null, error, selectionRange: null, originalText: '' };
  }
}

function handleApplyDebugFix() {
  if (!debugState.value.result || !debugState.value.selectionRange || !props.activeFile) return;
  const { startOffset, endOffset } = debugState.value.selectionRange;
  const content = props.activeFile.content;
  const newContent = content.slice(0, startOffset) + debugState.value.result.fixed_protocol + content.slice(endOffset);
  emit('change', newContent);
  debugState.value = { ...EMPTY_DEBUG };
}

function handleDiscardDebug() {
  debugState.value = { ...EMPTY_DEBUG };
}
</script>

<template>
  <div v-if="!displayFile" class="editor-empty">
    <div class="editor-empty__icon">⌘</div>
    <div class="editor-empty__content">
      <h2 class="editor-empty__title">{{ props.hasWorkspace ? 'Workspace is ready' : 'Choose a workspace folder' }}</h2>
      <p class="editor-empty__text">
        {{ props.hasWorkspace
          ? 'Select a file from the left panel, create a new file, or import a ZIP archive to start editing and previewing protocol content.'
          : 'Pick a local workspace folder from the left panel. Masterbrain will work directly against that directory on disk.' }}
      </p>
    </div>
  </div>

  <div v-else class="editor-shell">
    <div class="editor-shell__header">
      <div class="editor-shell__file">
        <span class="editor-shell__file-icon">{{ typeLabel }}</span>
        <div>
          <p class="editor-shell__eyebrow">{{ props.previewState ? 'Preview session' : 'Editor workspace' }}</p>
          <h2 class="editor-shell__title">{{ displayFile.name }}</h2>
        </div>
      </div>
      <div class="editor-shell__controls">
        <div class="editor-shell__view-toggle">
          <button
            v-for="mode in ['editor', 'split', 'preview'] as const"
            :key="mode"
            :class="['editor-shell__view-button', viewMode === mode ? 'editor-shell__view-button--active' : '']"
            @click="viewMode = mode"
          >
            {{ mode }}
          </button>
        </div>
        <button
          v-if="props.activeFile?.type === 'aimd' && !props.previewState"
          :disabled="debugState.loading || !selection"
          :class="['editor-shell__action-button', !debugState.loading && selection ? 'editor-shell__action-button--active' : '']"
          :title="!debugState.loading && selection ? 'Debug selected text for AIMD syntax errors' : 'Select text in the editor to debug'"
          @click="handleDebug"
        >
          {{ debugState.loading ? 'Checking…' : 'Debug selection' }}
        </button>
      </div>
    </div>

    <div class="editor-shell__statusbar">
      <span>{{ typeLabel }}</span>
      <span>{{ lineCount }} lines</span>
      <span>{{ props.isDark ? 'Dark theme' : 'Light theme' }}</span>
      <span v-if="selection">Selection ready</span>
    </div>

    <div v-if="props.previewState" class="editor-shell__notice">
      <div>
        <p class="editor-shell__notice-title">Preview mode</p>
        <p class="editor-shell__notice-text">AI-generated {{ typeLabel }} content is loaded into the editor in read-only mode.</p>
      </div>
      <div class="editor-shell__notice-actions">
        <button
          class="editor-shell__primary-button"
          @click="emit('keepPreview')"
        >Keep preview</button>
        <button
          class="editor-shell__secondary-button"
          @click="emit('discardPreview')"
        >Discard</button>
      </div>
    </div>

    <template v-if="debugState.result">
      <div v-if="debugState.result.has_errors" class="editor-shell__debug editor-shell__debug--warning">
        <div class="editor-shell__debug-header">
          <div>
            <p class="editor-shell__debug-title">Potential syntax issues found</p>
            <p v-if="debugState.result.response" class="editor-shell__debug-text">{{ debugState.result.response }}</p>
          </div>
          <div class="editor-shell__notice-actions">
            <button
              class="editor-shell__primary-button"
              @click="handleApplyDebugFix"
            >Apply fix</button>
            <button
              class="editor-shell__secondary-button"
              @click="handleDiscardDebug"
            >Dismiss</button>
          </div>
        </div>
        <div class="editor-shell__debug-body">
          <div class="editor-shell__debug-code">
            <pre>{{ debugState.result.fixed_protocol }}</pre>
          </div>
        </div>
      </div>
      <div v-else class="editor-shell__debug editor-shell__debug--success">
        <div>
          <p class="editor-shell__debug-title">No syntax errors found</p>
          <p v-if="debugState.result.response" class="editor-shell__debug-text">{{ debugState.result.response }}</p>
        </div>
        <button
          class="editor-shell__secondary-button"
          @click="handleDiscardDebug"
        >Dismiss</button>
      </div>
    </template>

    <div v-if="debugState.error" class="editor-shell__debug editor-shell__debug--danger">
      <div>
        <p class="editor-shell__debug-title">Debug request failed</p>
        <p class="editor-shell__debug-text">{{ debugState.error }}</p>
      </div>
      <button class="editor-shell__secondary-button" @click="handleDiscardDebug">Dismiss</button>
    </div>

    <div :class="['editor-shell__workspace', `editor-shell__workspace--${viewMode}`]">
      <section v-if="viewMode !== 'preview'" class="editor-shell__pane">
        <div class="editor-shell__pane-header">
          <span>Editor</span>
          <span>{{ props.previewState ? 'Read only' : 'Editable' }}</span>
        </div>
        <div class="editor-shell__pane-body editor-shell__pane-body--editor">
          <CodeEditor
            :file="displayFile"
            :is-dark="props.isDark"
            :read-only="!!props.previewState"
            @change="props.previewState ? undefined : emit('change', $event)"
            @selection-change="handleSelectionChange"
          />
        </div>
      </section>
      <section v-if="viewMode !== 'editor'" class="editor-shell__pane">
        <div class="editor-shell__pane-header">
          <span>{{ displayFile.type === 'aimd' ? 'Rendered Preview' : 'Code Preview' }}</span>
          <span>{{ displayFile.type === 'aimd' ? 'Live rendering' : 'Escaped source' }}</span>
        </div>
        <div class="editor-shell__pane-body">
          <AimdPreview :file="displayFile" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.editor-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  height: 100%;
  padding: 32px;
  background: transparent;
}

.editor-empty__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 24px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: #ffffff;
  font-size: 28px;
  box-shadow: 0 28px 42px -22px rgba(37, 99, 235, 0.55);
}

.editor-empty__content {
  max-width: 520px;
  text-align: center;
}

.editor-empty__title {
  margin: 0 0 10px;
  font-size: 24px;
  line-height: 1.2;
  color: var(--text-primary);
}

.editor-empty__text {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-muted);
}

.editor-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: transparent;
}

.editor-shell__header,
.editor-shell__statusbar,
.editor-shell__notice,
.editor-shell__debug {
  flex-shrink: 0;
}

.editor-shell__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px 14px;
  border-bottom: 1px solid var(--border-color);
}

.editor-shell__file {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.editor-shell__file-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 52px;
  padding: 0 12px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(14, 165, 233, 0.16) 100%);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.editor-shell__eyebrow {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.editor-shell__title {
  margin: 0;
  font-size: 20px;
  line-height: 1.2;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.editor-shell__controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.editor-shell__view-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  border-radius: 16px;
  background: var(--panel-solid);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.editor-shell__view-button,
.editor-shell__action-button,
.editor-shell__primary-button,
.editor-shell__secondary-button {
  border: none;
  cursor: pointer;
  transition: transform 0.2s ease, background-color 0.2s ease, color 0.2s ease, opacity 0.2s ease;
}

.editor-shell__view-button,
.editor-shell__action-button,
.editor-shell__secondary-button {
  padding: 9px 12px;
  border-radius: 12px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.editor-shell__view-button:hover,
.editor-shell__action-button:hover,
.editor-shell__primary-button:hover,
.editor-shell__secondary-button:hover {
  transform: translateY(-1px);
}

.editor-shell__view-button--active,
.editor-shell__action-button--active {
  background: var(--accent-soft);
  color: var(--accent);
}

.editor-shell__action-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

.editor-shell__statusbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 22px 0;
}

.editor-shell__statusbar span {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--border-color);
  background: var(--panel-solid);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
}

.editor-shell__notice,
.editor-shell__debug {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin: 14px 22px 0;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.editor-shell__notice-title,
.editor-shell__debug-title {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 800;
  color: var(--text-primary);
}

.editor-shell__notice-text,
.editor-shell__debug-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-muted);
}

.editor-shell__notice-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.editor-shell__debug-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}

.editor-shell__primary-button,
.editor-shell__secondary-button {
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 700;
}

.editor-shell__primary-button {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: #ffffff;
}

.editor-shell__secondary-button {
  background: var(--panel-subtle);
  color: var(--text-secondary);
}

.editor-shell__debug--warning {
  flex-direction: column;
  border-color: rgba(245, 158, 11, 0.26);
}

.editor-shell__debug--success {
  border-color: rgba(34, 197, 94, 0.24);
}

.editor-shell__debug--danger {
  border-color: rgba(239, 68, 68, 0.28);
}

.editor-shell__debug-body {
  width: 100%;
  margin-top: 12px;
}

.editor-shell__debug-code {
  max-height: 220px;
  overflow: auto;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  background: var(--code-bg);
}

.editor-shell__debug-code pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.65;
  color: var(--text-secondary);
  font-family: "IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace;
}

.editor-shell__workspace {
  flex: 1;
  min-height: 0;
  display: grid;
  gap: 14px;
  padding: 18px 22px 22px;
}

.editor-shell__workspace--split {
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
}

.editor-shell__workspace--editor,
.editor-shell__workspace--preview {
  grid-template-columns: minmax(0, 1fr);
}

.editor-shell__pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.editor-shell__pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.editor-shell__pane-body {
  flex: 1;
  min-height: 0;
  background: var(--preview-bg);
}

.editor-shell__pane-body--editor {
  background: transparent;
}

@media (max-width: 980px) {
  .editor-shell__header,
  .editor-shell__notice,
  .editor-shell__debug {
    flex-direction: column;
    align-items: stretch;
  }

  .editor-shell__workspace,
  .editor-shell__workspace--split {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
