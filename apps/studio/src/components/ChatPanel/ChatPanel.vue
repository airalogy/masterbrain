<script setup lang="ts">
import { ref } from 'vue';
import type { ChatMessage, CodeChange, ModelConfig, ProtocolRouter } from '../../types/index.ts';
import type { Theme } from '../../composables/useTheme.ts';
import type { SendIntent } from '../../composables/useChat.ts';
import MessageList from './MessageList.vue';
import ChatInput from './ChatInput.vue';
import AiAvatar from './AiAvatar.vue';

const props = defineProps<{
  messages: ChatMessage[];
  isStreaming: boolean;
  model: ModelConfig;
  router: ProtocolRouter;
  theme: Theme;
  hasWorkspace: boolean;
}>();

const emit = defineEmits<{
  'update:model': [model: ModelConfig];
  'update:router': [router: ProtocolRouter];
  themeToggle: [];
  send: [text: string, intent: SendIntent];
  applyBlock: [block: string, msgId: string];
  dismissBlock: [msgId: string];
  previewBlock: [block: string, msgId: string];
  previewChangedFile: [change: CodeChange, msgId: string];
  applyChangedFile: [change: CodeChange, msgId: string];
  applyAllChangedFiles: [changes: CodeChange[], msgId: string];
  dismissChangedFiles: [msgId: string];
  applyRaw: [content: string, type: 'aimd' | 'py'];
  clear: [];
  confirmStep: [];
  regenerateStep: [];
  collapse: [];
}>();

const showAdvanced = ref(false);

const ROUTER_INFO: Record<ProtocolRouter, { label: string; desc: string }> = {
  v3: {
    label: 'v3 Single-file (default)',
    desc: 'Generate a complete protocol.aimd in one call. Result is auto-applied to the editor.',
  },
  v1: {
    label: 'v1 Three-step',
    desc: 'Generate protocol.aimd → model.py → assigner.py in sequence. Each file is written to the editor after confirmation.',
  },
};
</script>

<template>
  <div class="chat-shell">
    <div class="chat-shell__header">
      <div class="chat-shell__heading">
        <AiAvatar size="md" />
        <div>
          <p class="chat-shell__eyebrow">Ask Aira</p>
          <h2 class="chat-shell__title">Masterbrain Copilot</h2>
        </div>
      </div>
      <div class="chat-shell__actions">
        <button
          title="Protocol settings"
          :class="['chat-shell__action-button', showAdvanced ? 'chat-shell__action-button--active' : '']"
          @click="showAdvanced = !showAdvanced"
        >Settings</button>
        <button
          :disabled="props.messages.length === 0"
          class="chat-shell__action-button"
          @click="emit('clear')"
        >Clear</button>
        <button
          title="Collapse panel"
          class="chat-shell__icon-button"
          @click="emit('collapse')"
        >›</button>
      </div>
    </div>

    <div class="chat-shell__meta">
      <span class="chat-shell__pill">Router: {{ ROUTER_INFO[props.router].label }}</span>
      <span class="chat-shell__pill">Model: {{ props.model.name }}</span>
    </div>

    <div v-if="showAdvanced" class="chat-shell__settings">
      <div>
        <p class="chat-shell__settings-label">Protocol generation router</p>
        <label
          v-for="(info, key) in ROUTER_INFO"
          :key="key"
          class="chat-shell__router-option"
        >
          <input
            type="radio"
            name="router"
            :value="key"
            :checked="props.router === key"
            class="chat-shell__radio"
            @change="emit('update:router', key as ProtocolRouter)"
          />
          <span class="chat-shell__router-content">
            <span :class="['chat-shell__router-title', props.router === key ? 'chat-shell__router-title--active' : '']">{{ info.label }}</span>
            <span class="chat-shell__router-desc">{{ info.desc }}</span>
          </span>
        </label>
      </div>
      <div class="chat-shell__settings-footer">
        <span class="chat-shell__settings-label">Theme</span>
        <button
          class="chat-shell__action-button"
          @click="emit('themeToggle')"
        >{{ props.theme === 'dark' ? 'Light mode' : 'Dark mode' }}</button>
      </div>
    </div>

    <MessageList
      :messages="props.messages"
      :has-workspace="props.hasWorkspace"
      @example-click="(text) => !props.isStreaming && emit('send', text, 'chat')"
      @apply-block="(block, msgId) => emit('applyBlock', block, msgId)"
      @dismiss-block="(msgId) => emit('dismissBlock', msgId)"
      @preview-block="(block, msgId) => emit('previewBlock', block, msgId)"
      @preview-changed-file="(change, msgId) => emit('previewChangedFile', change, msgId)"
      @apply-changed-file="(change, msgId) => emit('applyChangedFile', change, msgId)"
      @apply-all-changed-files="(changes, msgId) => emit('applyAllChangedFiles', changes, msgId)"
      @dismiss-changed-files="(msgId) => emit('dismissChangedFiles', msgId)"
      @confirm-step="emit('confirmStep')"
      @regenerate-step="emit('regenerateStep')"
    />

    <div class="chat-shell__composer">
      <ChatInput
        :is-streaming="props.isStreaming"
        :model="props.model"
        :has-workspace="props.hasWorkspace"
        @update:model="(m) => emit('update:model', m)"
        @send="(text, intent) => emit('send', text, intent)"
        @apply-raw="(content, type) => emit('applyRaw', content, type)"
      />
      <p class="chat-shell__disclaimer">Masterbrain may make mistakes. Review generated protocol content before saving it back to the workspace.</p>
    </div>
  </div>
</template>

<style scoped>
.chat-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: transparent;
}

.chat-shell__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid var(--border-color);
}

.chat-shell__heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-shell__eyebrow {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.chat-shell__title {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
  color: var(--text-primary);
}

.chat-shell__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.chat-shell__action-button,
.chat-shell__icon-button {
  border: none;
  cursor: pointer;
  transition: transform 0.2s ease, background-color 0.2s ease, color 0.2s ease, opacity 0.2s ease;
}

.chat-shell__action-button {
  padding: 8px 11px;
  border-radius: 12px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.chat-shell__action-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.chat-shell__action-button:hover:not(:disabled),
.chat-shell__icon-button:hover {
  background: var(--accent-soft);
  color: var(--accent);
  transform: translateY(-1px);
}

.chat-shell__action-button--active {
  background: var(--accent-soft);
  color: var(--accent);
}

.chat-shell__icon-button {
  width: 34px;
  height: 34px;
  padding: 0;
  border-radius: 999px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 18px;
}

.chat-shell__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 14px 18px 0;
}

.chat-shell__pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--panel-solid);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
}

.chat-shell__settings {
  margin: 14px 18px 0;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.chat-shell__settings-label {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.chat-shell__router-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--panel-muted);
  cursor: pointer;
}

.chat-shell__router-option + .chat-shell__router-option {
  margin-top: 10px;
}

.chat-shell__radio {
  margin-top: 2px;
  accent-color: var(--accent);
}

.chat-shell__router-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-shell__router-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
}

.chat-shell__router-title--active {
  color: var(--accent);
}

.chat-shell__router-desc {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-muted);
}

.chat-shell__settings-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border-color);
}

.chat-shell__settings-footer .chat-shell__settings-label {
  margin: 0;
}

.chat-shell__composer {
  padding: 14px 18px 18px;
  border-top: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, var(--panel-bg) 28%);
}

.chat-shell__disclaimer {
  margin: 10px 6px 0;
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-muted);
  text-align: center;
}
</style>
