<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ModelConfig } from '../../types/index.ts';
import { SUPPORTED_MODELS } from '../../types/index.ts';
import type { SendIntent } from '../../composables/useChat.ts';

const props = defineProps<{
  isStreaming: boolean;
  model: ModelConfig;
  hasWorkspace: boolean;
}>();

const emit = defineEmits<{
  'update:model': [model: ModelConfig];
  send: [text: string, intent: SendIntent];
  applyRaw: [content: string, type: 'aimd' | 'py'];
}>();

const text = ref('');
const selectedIntent = ref<SendIntent>('chat');
const showRaw = ref(false);
const rawContent = ref('');
const rawType = ref<'aimd' | 'py'>('aimd');
const textareaRef = ref<HTMLTextAreaElement | null>(null);

watch(
  () => props.hasWorkspace,
  (hasWorkspace) => {
    if (!hasWorkspace && selectedIntent.value !== 'chat') {
      selectedIntent.value = 'chat';
    }
    if (!hasWorkspace) {
      showRaw.value = false;
      rawContent.value = '';
    }
  },
);

function handleTextChange(e: Event) {
  const target = e.target as HTMLTextAreaElement;
  text.value = target.value;
  target.style.height = 'auto';
  target.style.height = `${Math.min(target.scrollHeight, 140)}px`;
}

function handleSend() {
  const trimmed = text.value.trim();
  if (!trimmed || props.isStreaming) return;
  emit('send', trimmed, selectedIntent.value);
  text.value = '';
  setTimeout(() => {
    if (textareaRef.value) textareaRef.value.style.height = 'auto';
  }, 0);
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

function handleApplyRaw() {
  if (!props.hasWorkspace) return;
  if (!rawContent.value.trim()) return;
  emit('applyRaw', rawContent.value.trim(), rawType.value);
  rawContent.value = '';
  showRaw.value = false;
}

function setIntent(intent: SendIntent) {
  if ((intent === 'edit' || intent === 'generate') && !props.hasWorkspace) return;
  selectedIntent.value = intent;
}
</script>

<template>
  <div class="composer-shell">
    <div v-if="showRaw" class="composer-shell__raw-card">
      <div class="composer-shell__raw-header">
        <span class="composer-shell__label">Paste content to editor</span>
        <div class="composer-shell__raw-types">
          <button
            v-for="t in (['aimd', 'py'] as const)"
            :key="t"
            :class="['composer-shell__type-chip', rawType === t ? 'composer-shell__type-chip--active' : '']"
            @click="rawType = t"
          >.{{ t }}</button>
        </div>
        <button class="composer-shell__ghost-button" @click="showRaw = false">Close</button>
      </div>
      <textarea
        v-model="rawContent"
        :placeholder="rawType === 'aimd' ? 'Paste .aimd content here...' : 'Paste Python code here...'"
        rows="5"
        class="composer-shell__raw-textarea"
      />
      <button
        :disabled="!rawContent.trim()"
        class="composer-shell__primary-button"
        @click="handleApplyRaw"
      >Apply to editor</button>
    </div>

    <div class="composer-shell__toolbar">
      <label class="composer-shell__field">
        <span class="composer-shell__label">Model</span>
        <select
          :value="props.model.name"
          class="composer-shell__select"
          @change="emit('update:model', { ...props.model, name: ($event.target as HTMLSelectElement).value })"
        >
          <option v-for="name in SUPPORTED_MODELS" :key="name" :value="name">{{ name }}</option>
        </select>
      </label>
      <label class="composer-shell__check">
        <input
          type="checkbox"
          :checked="props.model.enable_thinking"
          @change="emit('update:model', { ...props.model, enable_thinking: ($event.target as HTMLInputElement).checked })"
        />
        <span>Thinking</span>
      </label>
      <button
        :class="['composer-shell__ghost-button', showRaw ? 'composer-shell__ghost-button--active' : '']"
        :disabled="!props.hasWorkspace"
        :title="props.hasWorkspace
          ? 'Paste raw .aimd or .py content directly into the editor'
          : 'Choose a workspace folder before writing files'"
        @click="showRaw = !showRaw"
      >Paste code</button>
    </div>

    <div class="composer-shell__editor">
      <textarea
        ref="textareaRef"
        :value="text"
        :placeholder="props.isStreaming ? 'Generating...' : selectedIntent === 'chat'
          ? 'Chat about the current file or workspace (Enter to send, Shift+Enter for newline)'
          : selectedIntent === 'edit'
            ? 'Describe the code change you want to apply to the workspace'
            : 'Describe the protocol you want to generate in the selected workspace'"
        :disabled="props.isStreaming"
        rows="1"
        class="composer-shell__textarea"
        style="min-height: 24px"
        @input="handleTextChange"
        @keydown="handleKeyDown"
      />
      <div class="composer-shell__footer">
        <div class="composer-shell__mode-group">
          <button
            :class="['composer-shell__mode-button', selectedIntent === 'chat' ? 'composer-shell__mode-button--active' : '']"
            @click="setIntent('chat')"
          >Chat</button>
          <button
            :class="['composer-shell__mode-button', selectedIntent === 'edit' ? 'composer-shell__mode-button--active' : '']"
            :disabled="!props.hasWorkspace"
            :title="props.hasWorkspace ? 'Apply workspace edits through OpenCode' : 'Choose a workspace folder to enable Edit mode'"
            @click="setIntent('edit')"
          >Edit</button>
          <button
            :class="['composer-shell__mode-button', selectedIntent === 'generate' ? 'composer-shell__mode-button--active' : '']"
            :disabled="!props.hasWorkspace"
            :title="props.hasWorkspace ? 'Generate protocol files into the selected workspace' : 'Choose a workspace folder to enable Generate mode'"
            @click="setIntent('generate')"
          >Generate</button>
          <span class="composer-shell__mode-hint">
            {{ selectedIntent === 'chat'
              ? 'Conversation only'
              : selectedIntent === 'edit'
                ? (props.hasWorkspace ? 'Workspace editing via OpenCode' : 'Workspace required')
                : (props.hasWorkspace ? 'Protocol generation into workspace' : 'Workspace required') }}
          </span>
        </div>
        <button
          :disabled="!text.trim() || props.isStreaming || ((selectedIntent === 'edit' || selectedIntent === 'generate') && !props.hasWorkspace)"
          class="composer-shell__send-button"
          @click="handleSend"
        >
          <span v-if="props.isStreaming">…</span>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.composer-shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.composer-shell__toolbar,
.composer-shell__editor,
.composer-shell__raw-card {
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.composer-shell__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
}

.composer-shell__field {
  display: flex;
  align-items: center;
  gap: 10px;
}

.composer-shell__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.composer-shell__select {
  min-width: 146px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--panel-muted);
  color: var(--text-primary);
  outline: none;
}

.composer-shell__check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--panel-muted);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.composer-shell__check input {
  accent-color: var(--accent);
}

.composer-shell__ghost-button,
.composer-shell__primary-button,
.composer-shell__mode-button,
.composer-shell__send-button,
.composer-shell__type-chip {
  border: none;
  cursor: pointer;
  transition: transform 0.2s ease, background-color 0.2s ease, color 0.2s ease, opacity 0.2s ease;
}

.composer-shell__ghost-button {
  margin-left: auto;
  padding: 9px 12px;
  border-radius: 12px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.composer-shell__ghost-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

.composer-shell__ghost-button:hover,
.composer-shell__primary-button:hover,
.composer-shell__mode-button:hover,
.composer-shell__send-button:hover,
.composer-shell__type-chip:hover {
  transform: translateY(-1px);
}

.composer-shell__mode-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
  transform: none;
}

.composer-shell__ghost-button--active {
  background: var(--accent-soft);
  color: var(--accent);
}

.composer-shell__editor {
  padding: 14px 14px 12px;
}

.composer-shell__textarea {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--text-primary);
  outline: none;
  font-size: 14px;
  line-height: 1.65;
  overflow: hidden;
}

.composer-shell__textarea::placeholder {
  color: var(--text-muted);
}

.composer-shell__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

.composer-shell__mode-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.composer-shell__mode-button {
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.composer-shell__mode-button--active {
  background: var(--accent-soft);
  color: var(--accent);
}

.composer-shell__mode-hint {
  font-size: 11px;
  color: var(--text-muted);
}

.composer-shell__send-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: #ffffff;
  box-shadow: 0 18px 30px -18px rgba(37, 99, 235, 0.6);
}

.composer-shell__send-button:disabled,
.composer-shell__primary-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

.composer-shell__raw-card {
  padding: 14px;
}

.composer-shell__raw-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.composer-shell__raw-types {
  display: inline-flex;
  gap: 8px;
}

.composer-shell__type-chip {
  padding: 7px 10px;
  border-radius: 999px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.composer-shell__type-chip--active {
  background: var(--accent-soft);
  color: var(--accent);
}

.composer-shell__raw-textarea {
  width: 100%;
  min-height: 140px;
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--panel-muted);
  color: var(--text-primary);
  outline: none;
  font-family: "IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace;
  line-height: 1.6;
}

.composer-shell__primary-button {
  width: 100%;
  margin-top: 12px;
  padding: 11px 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
}

@media (max-width: 640px) {
  .composer-shell__toolbar,
  .composer-shell__footer,
  .composer-shell__raw-header {
    flex-direction: column;
    align-items: stretch;
  }

  .composer-shell__ghost-button {
    margin-left: 0;
  }
}
</style>
