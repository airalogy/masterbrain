<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import MarkdownIt from 'markdown-it';
import type { ChatMessage } from '../../types/index.ts';
import { useTheme } from '../../composables/useTheme.ts';

const COLLAPSE_LINES = 18;

const props = defineProps<{
  messages: ChatMessage[];
}>();

const emit = defineEmits<{
  applyBlock: [block: string, msgId: string];
  dismissBlock: [msgId: string];
  previewBlock: [block: string, msgId: string];
  confirmStep: [];
  regenerateStep: [];
}>();

const theme = useTheme();
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

// Auto-scroll on new messages
watch(() => props.messages, () => {
  nextTick(() => {
    bottomRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
});
</script>

<template>
  <div v-if="props.messages.length === 0" class="flex-1 flex items-center justify-center text-gray-500 text-sm text-center p-4">
    <div>
      <div class="text-3xl mb-2">🤖</div>
      <p class="font-medium text-gray-400">Airalogy Masterbrain</p>
      <p class="text-xs mt-2 text-gray-600 leading-relaxed">
        Enter your request — AI will decide whether to chat or generate a protocol.<br/>
        Click <span class="font-mono">⚙ Settings</span> to choose the protocol router.
      </p>
    </div>
  </div>

  <div v-else class="flex-1 overflow-y-auto px-3 py-2 space-y-3">
    <div v-for="msg in props.messages" :key="msg.id" :class="['flex flex-col', msg.role === 'user' ? 'items-end' : 'items-start']">
      <div
        :class="[
          'max-w-[92%] rounded-lg px-3 py-2 text-sm',
          msg.role === 'user'
            ? 'bg-blue-700 text-white rounded-br-none'
            : 'bg-gray-800 text-gray-200 rounded-bl-none',
        ]"
      >
        <template v-if="msg.role === 'assistant'">
          <div>
            <div :class="['prose prose-sm max-w-none break-words', theme === 'dark' ? 'prose-invert' : '']" v-html="renderMarkdown(getDisplayContent(msg).displayed)" />
            <button
              v-if="getDisplayContent(msg).needsCollapse"
              class="mt-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              @click="toggleExpand(msg.id)"
            >
              {{ getDisplayContent(msg).expanded ? '▲ Collapse' : `▼ Expand (${getDisplayContent(msg).lineCount} lines)` }}
            </button>
          </div>
        </template>
        <template v-else>
          <span class="whitespace-pre-wrap break-words">{{ msg.content }}</span>
        </template>
      </div>

      <!-- V1 step: confirm / regenerate -->
      <div v-if="msg.role === 'assistant' && !msg.streaming && msg.stepPending" class="mt-1.5 w-full max-w-[92%]">
        <div class="bg-gray-800 border border-blue-700 rounded-lg p-2">
          <p class="text-xs text-gray-400 mb-2">Written to editor. Confirm to save and continue to the next step.</p>
          <div class="flex gap-1.5">
            <button
              class="flex-1 text-xs px-2 py-1.5 bg-green-700 hover:bg-green-600 text-white rounded-md transition-colors font-medium"
              @click="emit('confirmStep')"
            >✅ Confirm &amp; Continue</button>
            <button
              class="flex-1 text-xs px-2 py-1.5 bg-orange-700 hover:bg-orange-600 text-white rounded-md transition-colors"
              @click="emit('regenerateStep')"
            >🔄 Regenerate</button>
          </div>
        </div>
      </div>

      <!-- Chat mode: action buttons for detected code blocks -->
      <div v-if="msg.role === 'assistant' && !msg.streaming && msg.aimdBlocks && msg.aimdBlocks.length > 0" class="mt-1.5 w-full max-w-[92%]">
        <div class="bg-gray-800 border border-gray-600 rounded-lg p-2">
          <p class="text-xs text-gray-400 mb-2">✨ AI generated content. What would you like to do?</p>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="(block, i) in msg.aimdBlocks" :key="i" class="flex gap-1">
              <button
                class="text-xs px-2 py-1 bg-yellow-700 hover:bg-yellow-600 text-white rounded-md transition-colors"
                title="Preview in editor before deciding"
                @click="emit('previewBlock', block, msg.id)"
              >👁 Preview {{ block.startsWith('__py__') ? '.py' : '.aimd' }}</button>
              <button
                class="text-xs px-2 py-1 bg-green-700 hover:bg-green-600 text-white rounded-md transition-colors"
                title="Apply directly to editor"
                @click="emit('applyBlock', block, msg.id)"
              >✅ Apply</button>
            </span>
            <button
              class="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-md transition-colors"
              @click="emit('dismissBlock', msg.id)"
            >✕ Dismiss</button>
          </div>
        </div>
      </div>
    </div>
    <div ref="bottomRef" />
  </div>
</template>
