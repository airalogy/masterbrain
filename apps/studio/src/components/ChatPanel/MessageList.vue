<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import MarkdownIt from 'markdown-it';
import type { ChatMessage, CodeChange } from '../../types/index.ts';
import AiAvatar from './AiAvatar.vue';

const COLLAPSE_LINES = 18;
const EXAMPLE_PROMPTS = [
  'Summarize the current AIMD protocol and point out the risky steps.',
  'Find possible syntax or structure issues in my current file.',
  'Suggest how to improve this workflow before I export the ZIP.',
];

const props = defineProps<{
  messages: ChatMessage[];
  hasWorkspace: boolean;
}>();

const emit = defineEmits<{
  exampleClick: [text: string];
  applyBlock: [block: string, msgId: string];
  dismissBlock: [msgId: string];
  previewBlock: [block: string, msgId: string];
  previewChangedFile: [change: CodeChange, msgId: string];
  applyChangedFile: [change: CodeChange, msgId: string];
  applyAllChangedFiles: [changes: CodeChange[], msgId: string];
  dismissChangedFiles: [msgId: string];
  confirmStep: [];
  regenerateStep: [];
}>();

const bottomRef = ref<HTMLDivElement | null>(null);

const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

// Collapsible state per message
const expandedMessages = ref<Set<string>>(new Set());

function toggleExpand(msgId: string) {
  const next = new Set(expandedMessages.value);
  if (next.has(msgId)) next.delete(msgId);
  else next.add(msgId);
  expandedMessages.value = next;
}

function getDisplayContent(msg: ChatMessage) {
  const content = msg.content || (msg.streaming ? '▋' : '');
  const lines = content.split('\n');
  const needsCollapse = lines.length > COLLAPSE_LINES;
  const expanded = expandedMessages.value.has(msg.id);
  const displayed = needsCollapse && !expanded
    ? lines.slice(0, COLLAPSE_LINES).join('\n')
    : content;
  return { displayed, needsCollapse, expanded, lineCount: lines.length };
}

function renderMarkdown(content: string): string {
  return md.render(content || '▋');
}

watch(() => props.messages, () => {
  nextTick(() => {
    bottomRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
});
</script>

<template>
  <div v-if="props.messages.length === 0" class="chat-empty">
    <div class="chat-empty__hero">
      <AiAvatar size="lg" />
      <div>
        <h3 class="chat-empty__title">Hi, I'm Aira</h3>
        <p class="chat-empty__subtitle">
          {{ props.hasWorkspace
            ? 'Choose Chat for discussion, Edit for workspace changes, or Generate for protocol creation. The active editor context is included automatically when relevant.'
            : 'Choose a workspace folder first, then use Chat for discussion, Edit for workspace changes, or Generate for protocol creation.' }}
        </p>
      </div>
    </div>
    <div class="chat-empty__examples">
      <button
        v-for="prompt in EXAMPLE_PROMPTS"
        :key="prompt"
        class="chat-empty__example"
        @click="emit('exampleClick', prompt)"
      >
        {{ prompt }}
      </button>
    </div>
  </div>

  <div v-else class="chat-thread">
    <div
      v-for="msg in props.messages"
      :key="msg.id"
      :class="['chat-message', msg.role === 'user' ? 'chat-message--user' : 'chat-message--assistant']"
    >
      <AiAvatar v-if="msg.role === 'assistant'" size="sm" />
      <div v-else class="chat-message__avatar">You</div>
      <div class="chat-message__body">
        <div class="chat-message__meta">
          <span>{{ msg.role === 'assistant' ? 'Masterbrain' : 'You' }}</span>
          <span v-if="msg.streaming">Thinking…</span>
        </div>
        <div :class="['chat-message__bubble', msg.role === 'user' ? 'chat-message__bubble--user' : 'chat-message__bubble--assistant']">
          <template v-if="msg.role === 'assistant'">
            <div>
              <div class="chat-rich-text" v-html="renderMarkdown(getDisplayContent(msg).displayed)" />
              <button
                v-if="getDisplayContent(msg).needsCollapse"
                class="chat-message__toggle"
                @click="toggleExpand(msg.id)"
              >
                {{ getDisplayContent(msg).expanded ? 'Collapse' : `Expand (${getDisplayContent(msg).lineCount} lines)` }}
              </button>
            </div>
          </template>
          <template v-else>
            <span class="chat-message__user-text">{{ msg.content }}</span>
          </template>
        </div>

        <div v-if="msg.role === 'assistant' && !msg.streaming && msg.stepPending" class="chat-action-card">
          <p class="chat-action-card__text">Written to the editor. Confirm to save and continue to the next step.</p>
          <div class="chat-action-card__actions">
            <button
              class="chat-action-card__button chat-action-card__button--primary"
              @click="emit('confirmStep')"
            >Confirm &amp; Continue</button>
            <button
              class="chat-action-card__button chat-action-card__button--secondary"
              @click="emit('regenerateStep')"
            >Regenerate</button>
          </div>
        </div>

        <div v-if="msg.role === 'assistant' && !msg.streaming && msg.aimdBlocks && msg.aimdBlocks.length > 0" class="chat-action-card">
          <p class="chat-action-card__text">AI generated code or AIMD content. Preview it in the editor or apply it directly.</p>
          <div class="chat-action-card__actions chat-action-card__actions--wrap">
            <span v-for="(block, i) in msg.aimdBlocks" :key="i" class="chat-action-card__inline-actions">
              <button
                class="chat-action-card__button chat-action-card__button--preview"
                title="Preview in editor before deciding"
                @click="emit('previewBlock', block, msg.id)"
              >Preview {{ block.startsWith('__py__') ? '.py' : '.aimd' }}</button>
              <button
                class="chat-action-card__button chat-action-card__button--primary"
                title="Apply directly to editor"
                @click="emit('applyBlock', block, msg.id)"
              >Apply</button>
            </span>
            <button
              class="chat-action-card__button chat-action-card__button--ghost"
              @click="emit('dismissBlock', msg.id)"
            >Dismiss</button>
          </div>
        </div>

        <div v-if="msg.role === 'assistant' && !msg.streaming && msg.changedFiles && msg.changedFiles.length > 0" class="chat-action-card">
          <p class="chat-action-card__text">OpenCode prepared workspace edits. Review them file by file or apply everything at once.</p>
          <div class="chat-action-card__actions chat-action-card__actions--wrap">
            <span v-for="change in msg.changedFiles" :key="change.path" class="chat-action-card__inline-actions">
              <span class="chat-action-card__file-label">{{ change.name }} · {{ change.status }}</span>
              <button
                v-if="change.status !== 'deleted'"
                class="chat-action-card__button chat-action-card__button--preview"
                @click="emit('previewChangedFile', change, msg.id)"
              >Preview</button>
              <button
                class="chat-action-card__button chat-action-card__button--primary"
                @click="emit('applyChangedFile', change, msg.id)"
              >{{ change.status === 'deleted' ? 'Delete' : 'Apply' }}</button>
            </span>
            <button
              class="chat-action-card__button chat-action-card__button--primary"
              @click="emit('applyAllChangedFiles', msg.changedFiles, msg.id)"
            >Apply all</button>
            <button
              class="chat-action-card__button chat-action-card__button--ghost"
              @click="emit('dismissChangedFiles', msg.id)"
            >Dismiss</button>
          </div>
          <details v-if="msg.executionLog && msg.executionLog.length > 0" class="chat-action-card__details">
            <summary>Execution details</summary>
            <ul class="chat-action-card__log">
              <li v-for="(line, index) in msg.executionLog" :key="`${msg.id}-change-log-${index}`">{{ line }}</li>
            </ul>
          </details>
        </div>

        <div
          v-if="msg.role === 'assistant' && !msg.streaming && msg.editStatus === 'no_changes'"
          class="chat-action-card"
        >
          <p class="chat-action-card__text">OpenCode completed, but it did not modify any supported workspace files this time.</p>
          <details v-if="msg.executionLog && msg.executionLog.length > 0" class="chat-action-card__details" open>
            <summary>Execution details</summary>
            <ul class="chat-action-card__log">
              <li v-for="(line, index) in msg.executionLog" :key="`${msg.id}-noop-log-${index}`">{{ line }}</li>
            </ul>
          </details>
        </div>
      </div>
    </div>
    <div ref="bottomRef" />
  </div>
</template>

<style scoped>
.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 22px;
  padding: 28px 18px 24px;
}

.chat-empty__hero {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.chat-empty__title {
  margin: 2px 0 8px;
  font-size: 20px;
  line-height: 1.2;
  color: var(--text-primary);
}

.chat-empty__subtitle {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-muted);
}

.chat-empty__examples {
  display: grid;
  gap: 10px;
}

.chat-empty__example {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--panel-solid);
  color: var(--text-secondary);
  text-align: left;
  font-size: 13px;
  line-height: 1.5;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.chat-empty__example:hover {
  transform: translateY(-1px);
  border-color: var(--accent-border);
  box-shadow: var(--shadow-md);
}

.chat-thread {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 18px;
}

.chat-message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.chat-message--user {
  flex-direction: row-reverse;
}

.chat-message__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 14px;
  background: var(--panel-solid);
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  flex-shrink: 0;
}

.chat-message--user .chat-message__avatar {
  background: var(--user-surface);
  border-color: transparent;
  color: var(--user-text);
}

.chat-message__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: calc(100% - 46px);
}

.chat-message--user .chat-message__body {
  align-items: flex-end;
}

.chat-message__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.chat-message__bubble {
  max-width: 100%;
  padding: 14px 16px;
  border-radius: 22px;
  box-shadow: var(--shadow-md);
}

.chat-message__bubble--assistant {
  border: 1px solid var(--assistant-border);
  background: var(--assistant-surface);
  color: var(--text-secondary);
  border-top-left-radius: 8px;
}

.chat-message__bubble--user {
  background: var(--user-surface);
  color: var(--user-text);
  border-top-right-radius: 8px;
}

.chat-message__user-text {
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.chat-message__toggle {
  margin-top: 12px;
  border: none;
  background: transparent;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

.chat-action-card {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.chat-action-card__text {
  margin: 0 0 12px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-muted);
}

.chat-action-card__actions {
  display: flex;
  gap: 10px;
}

.chat-action-card__actions--wrap {
  flex-wrap: wrap;
}

.chat-action-card__file-label {
  padding: 0 2px 0 0;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
}

.chat-action-card__inline-actions {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chat-action-card__details {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

.chat-action-card__details summary {
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}

.chat-action-card__log {
  margin: 8px 0 0;
  padding-left: 18px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.5;
}

.chat-action-card__button {
  padding: 9px 12px;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease, background-color 0.2s ease;
}

.chat-action-card__button:hover {
  transform: translateY(-1px);
}

.chat-action-card__button--primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: #ffffff;
}

.chat-action-card__button--secondary {
  background: rgba(245, 158, 11, 0.9);
  color: #ffffff;
}

.chat-action-card__button--preview {
  background: rgba(14, 165, 233, 0.88);
  color: #ffffff;
}

.chat-action-card__button--ghost {
  background: var(--panel-subtle);
  color: var(--text-secondary);
}

@media (max-width: 640px) {
  .chat-thread {
    padding: 14px;
  }

  .chat-message__body {
    max-width: calc(100% - 42px);
  }

  .chat-action-card__actions {
    flex-direction: column;
  }
}
</style>
