<script setup lang="ts">
import { ref } from 'vue';
import type { ChatMessage, ModelConfig, ProtocolRouter } from '../../types/index.ts';
import type { Theme } from '../../composables/useTheme.ts';
import type { SendIntent } from '../../composables/useChat.ts';
import MessageList from './MessageList.vue';
import ChatInput from './ChatInput.vue';

const props = defineProps<{
  messages: ChatMessage[];
  isStreaming: boolean;
  model: ModelConfig;
  router: ProtocolRouter;
  theme: Theme;
}>();

const emit = defineEmits<{
  'update:model': [model: ModelConfig];
  'update:router': [router: ProtocolRouter];
  themeToggle: [];
  send: [text: string, intent: SendIntent];
  applyBlock: [block: string, msgId: string];
  dismissBlock: [msgId: string];
  previewBlock: [block: string, msgId: string];
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
  <div class="flex flex-col h-full bg-gray-900 border-l border-gray-700">
    <!-- Header -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-gray-700">
      <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">AI Chat</h2>
      <div class="flex items-center gap-1.5">
        <button
          title="Protocol settings"
          :class="[
            'text-xs px-2 py-1 rounded border font-medium transition-colors',
            showAdvanced
              ? 'border-blue-500 bg-blue-600/20 text-blue-400'
              : 'border-gray-600 text-gray-400 hover:border-gray-400 hover:text-gray-200',
          ]"
          @click="showAdvanced = !showAdvanced"
        >⚙ Settings</button>
        <button
          :disabled="props.messages.length === 0"
          class="text-xs text-gray-500 hover:text-gray-300 disabled:opacity-40 transition-colors px-1"
          @click="emit('clear')"
        >Clear</button>
        <button
          title="Collapse panel"
          class="text-gray-500 hover:text-white hover:bg-gray-700 w-5 h-5 flex items-center justify-center rounded text-sm"
          @click="emit('collapse')"
        >›</button>
      </div>
    </div>

    <!-- Advanced settings panel -->
    <div v-if="showAdvanced" class="border-b border-gray-700 px-3 py-2.5 bg-gray-800 space-y-3">
      <div>
        <p class="text-xs font-medium text-gray-400 mb-2">Protocol Generation Router</p>
        <label
          v-for="(info, key) in ROUTER_INFO"
          :key="key"
          class="flex items-start gap-2 cursor-pointer mb-1.5"
        >
          <input
            type="radio"
            name="router"
            :value="key"
            :checked="props.router === key"
            class="mt-0.5 accent-blue-500"
            @change="emit('update:router', key as ProtocolRouter)"
          />
          <span>
            <span :class="['text-xs font-medium', props.router === key ? 'text-blue-400' : 'text-gray-300']">{{ info.label }}</span>
            <span class="block text-xs text-gray-500 mt-0.5">{{ info.desc }}</span>
          </span>
        </label>
      </div>
      <div class="flex items-center justify-between pt-1 border-t border-gray-700">
        <span class="text-xs text-gray-400">Theme</span>
        <button
          class="text-xs px-2 py-1 rounded border border-gray-600 text-gray-300 hover:border-gray-400 hover:text-gray-100 transition-colors"
          @click="emit('themeToggle')"
        >{{ props.theme === 'dark' ? '☀ Light mode' : '🌙 Dark mode' }}</button>
      </div>
    </div>

    <!-- Messages -->
    <MessageList
      :messages="props.messages"
      @apply-block="(block, msgId) => emit('applyBlock', block, msgId)"
      @dismiss-block="(msgId) => emit('dismissBlock', msgId)"
      @preview-block="(block, msgId) => emit('previewBlock', block, msgId)"
      @confirm-step="emit('confirmStep')"
      @regenerate-step="emit('regenerateStep')"
    />

    <!-- Input -->
    <ChatInput
      :is-streaming="props.isStreaming"
      :model="props.model"
      @update:model="(m) => emit('update:model', m)"
      @send="(text, intent) => emit('send', text, intent)"
      @apply-raw="(content, type) => emit('applyRaw', content, type)"
    />
  </div>
</template>
