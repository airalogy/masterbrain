<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ModelConfig } from '../../types/index.ts';
import { SUPPORTED_MODELS } from '../../types/index.ts';
import { detectIntent } from '../../utils/apiClient.ts';
import type { SendIntent } from '../../composables/useChat.ts';

const props = defineProps<{
  isStreaming: boolean;
  model: ModelConfig;
}>();

const emit = defineEmits<{
  'update:model': [model: ModelConfig];
  send: [text: string, intent: SendIntent];
  applyRaw: [content: string, type: 'aimd' | 'py'];
}>();

const text = ref('');
const detectedIntent = ref<SendIntent>('chat');
const intentOverridden = ref(false);
const showRaw = ref(false);
const rawContent = ref('');
const rawType = ref<'aimd' | 'py'>('aimd');
const textareaRef = ref<HTMLTextAreaElement | null>(null);

watch(text, (val) => {
  if (intentOverridden.value) return;
  if (val.trim().length < 3) { detectedIntent.value = 'chat'; return; }
  detectedIntent.value = detectIntent(val);
});

function handleTextChange(e: Event) {
  const target = e.target as HTMLTextAreaElement;
  text.value = target.value;
  intentOverridden.value = false;
  target.style.height = 'auto';
  target.style.height = `${Math.min(target.scrollHeight, 140)}px`;
}

function handleSend() {
  const trimmed = text.value.trim();
  if (!trimmed || props.isStreaming) return;
  emit('send', trimmed, detectedIntent.value);
  text.value = '';
  intentOverridden.value = false;
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
  if (!rawContent.value.trim()) return;
  emit('applyRaw', rawContent.value.trim(), rawType.value);
  rawContent.value = '';
  showRaw.value = false;
}
</script>

<template>
  <div class="border-t border-gray-700">
    <!-- Paste Raw panel -->
    <div v-if="showRaw" class="border-b border-gray-700 p-2.5 bg-gray-800">
      <div class="flex items-center gap-2 mb-1.5">
        <span class="text-xs text-gray-400 font-medium">Paste content to editor</span>
        <div class="flex gap-1 ml-auto">
          <button
            v-for="t in (['aimd', 'py'] as const)"
            :key="t"
            :class="['text-xs px-1.5 py-0.5 rounded transition-colors', rawType === t ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600']"
            @click="rawType = t"
          >.{{ t }}</button>
        </div>
        <button class="text-gray-500 hover:text-gray-300 text-xs" @click="showRaw = false">✕</button>
      </div>
      <textarea
        v-model="rawContent"
        :placeholder="rawType === 'aimd' ? 'Paste .aimd content here...' : 'Paste Python code here...'"
        rows="5"
        class="w-full bg-gray-900 border border-gray-600 rounded text-xs text-gray-200 p-2 outline-none resize-none font-mono"
      />
      <button
        :disabled="!rawContent.trim()"
        class="mt-1.5 w-full py-1 text-xs rounded bg-green-700 hover:bg-green-600 text-white disabled:opacity-40 disabled:cursor-not-allowed"
        @click="handleApplyRaw"
      >✅ Apply to editor</button>
    </div>

    <!-- Model selector row -->
    <div class="flex items-center gap-2 px-3 pt-2 pb-1">
      <span class="text-xs text-gray-500">Model:</span>
      <select
        :value="props.model.name"
        class="text-xs bg-gray-800 border border-gray-600 rounded px-1.5 py-0.5 text-gray-300 outline-none focus:border-blue-500"
        @change="emit('update:model', { ...props.model, name: ($event.target as HTMLSelectElement).value })"
      >
        <option v-for="name in SUPPORTED_MODELS" :key="name" :value="name">{{ name }}</option>
      </select>
      <label class="flex items-center gap-1 text-xs text-gray-500 cursor-pointer">
        <input
          type="checkbox"
          :checked="props.model.enable_thinking"
          class="w-3 h-3 accent-blue-500"
          @change="emit('update:model', { ...props.model, enable_thinking: ($event.target as HTMLInputElement).checked })"
        />
        Think
      </label>
      <button
        :class="['ml-auto text-xs px-2 py-0.5 rounded transition-colors', showRaw ? 'bg-gray-600 text-gray-200' : 'bg-gray-700 text-gray-400 hover:bg-gray-600']"
        title="Paste raw .aimd or .py content directly into the editor"
        @click="showRaw = !showRaw"
      >📋 Paste</button>
    </div>

    <!-- Textarea + Send -->
    <div class="px-3 pb-3">
      <div class="flex items-end gap-2 bg-gray-800 rounded-lg px-3 py-2">
        <textarea
          ref="textareaRef"
          :value="text"
          :placeholder="props.isStreaming ? 'Generating...' : 'Message (Enter to send, Shift+Enter for newline)'"
          :disabled="props.isStreaming"
          rows="1"
          class="flex-1 bg-transparent text-sm text-gray-200 placeholder-gray-500 resize-none outline-none overflow-hidden"
          style="min-height: 24px"
          @input="handleTextChange"
          @keydown="handleKeyDown"
        />
        <button
          :disabled="!text.trim() || props.isStreaming"
          class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-md bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          @click="handleSend"
        >
          <span v-if="props.isStreaming" class="text-xs animate-pulse">⏳</span>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>
