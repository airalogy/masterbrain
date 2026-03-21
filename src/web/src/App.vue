<script setup lang="ts">
import { ref, watch } from 'vue';
import FileManager from './components/FileManager/FileManager.vue';
import EditorPanel from './components/EditorPanel/EditorPanel.vue';
import ChatPanel from './components/ChatPanel/ChatPanel.vue';
import { useFileManager } from './composables/useFileManager.ts';
import { useChat } from './composables/useChat.ts';
import { provideTheme, type Theme } from './composables/useTheme.ts';
import type { PreviewState } from './types/index.ts';

const leftOpen = ref(true);
const rightOpen = ref(true);
const theme = ref<Theme>('dark');

provideTheme(theme);

watch(theme, (val) => {
  const html = document.documentElement;
  html.classList.toggle('light', val === 'light');
  html.classList.toggle('dark', val === 'dark');
}, { immediate: true });

const {
  files, activeFile, hasManualChanges, folders,
  uploadZip, downloadZip, updateFileContent, createFile, deleteFile, renameFile, selectFile, createFolder,
} = useFileManager();

const previewState = ref<PreviewState | null>(null);

function handleApplyContent(content: string, type: 'aimd' | 'py') {
  if (activeFile.value) {
    updateFileContent(activeFile.value.path, content);
  } else {
    const name = type === 'aimd' ? 'protocol.aimd' : 'script.py';
    createFile(name, content, type, true);
  }
}

function handleAutoApply(name: string, content: string, type: 'aimd' | 'py') {
  createFile(name, content, type, false);
}

const {
  messages, isStreaming, model, router,
  sendMessage, applyBlock, dismissBlock, clearMessages,
  confirmStep, regenerateStep,
} = useChat(activeFile, handleApplyContent, handleAutoApply);

function handleEditorChange(content: string) {
  if (activeFile.value) updateFileContent(activeFile.value.path, content);
}

function handleApplyBlock(block: string, msgId: string) {
  applyBlock(block);
  dismissBlock(msgId);
  previewState.value = null;
}

function handlePreviewBlock(block: string, msgId: string) {
  const isPy = block.startsWith('__py__');
  const content = isPy ? block.slice(6) : block;
  const type = isPy ? 'py' as const : 'aimd' as const;
  previewState.value = { content, type, msgId };
}

function handleKeepPreview() {
  if (!previewState.value) return;
  handleApplyContent(previewState.value.content, previewState.value.type);
  dismissBlock(previewState.value.msgId);
  previewState.value = null;
}

function handleDiscardPreview() {
  previewState.value = null;
}

function handleCreateFile(name: string, content: string) {
  createFile(name, content, undefined, true);
}
</script>

<template>
  <div class="flex h-screen w-screen overflow-hidden bg-gray-950">
    <!-- Left: File Manager -->
    <div v-if="leftOpen" class="w-56 flex-shrink-0">
      <FileManager
        :files="files"
        :folders="folders"
        :active-file="activeFile"
        :has-manual-changes="hasManualChanges"
        @upload="uploadZip"
        @download="downloadZip"
        @select="selectFile"
        @delete="deleteFile"
        @rename="renameFile"
        @create-file="handleCreateFile"
        @create-folder="createFolder"
        @collapse="leftOpen = false"
      />
    </div>
    <div
      v-else
      class="w-8 flex-shrink-0 flex flex-col items-center py-3 gap-3 bg-gray-900 border-r border-gray-700"
    >
      <button
        class="text-gray-400 hover:text-gray-200 text-base leading-none transition-colors"
        title="Expand Files"
        @click="leftOpen = true"
      >›</button>
      <span
        class="text-gray-500 text-xs font-medium"
        style="writing-mode: vertical-rl; transform: rotate(180deg)"
      >Files</span>
    </div>

    <!-- Middle: Editor + Preview -->
    <div class="flex-1 min-w-0">
      <EditorPanel
        :active-file="activeFile"
        :preview-state="previewState"
        :is-dark="theme === 'dark'"
        :model="model"
        @change="handleEditorChange"
        @keep-preview="handleKeepPreview"
        @discard-preview="handleDiscardPreview"
      />
    </div>

    <!-- Right: Chat Panel -->
    <div v-if="rightOpen" class="w-80 flex-shrink-0">
      <ChatPanel
        :messages="messages"
        :is-streaming="isStreaming"
        :model="model"
        :router="router"
        :theme="theme"
        @update:model="model = $event"
        @update:router="router = $event"
        @theme-toggle="theme = theme === 'dark' ? 'light' : 'dark'"
        @send="sendMessage"
        @apply-block="handleApplyBlock"
        @dismiss-block="dismissBlock"
        @preview-block="handlePreviewBlock"
        @apply-raw="handleApplyContent"
        @clear="clearMessages"
        @confirm-step="confirmStep"
        @regenerate-step="regenerateStep"
        @collapse="rightOpen = false"
      />
    </div>
    <div
      v-else
      class="w-8 flex-shrink-0 flex flex-col items-center py-3 gap-3 bg-gray-900 border-l border-gray-700"
    >
      <button
        class="text-gray-400 hover:text-gray-200 text-base leading-none transition-colors"
        title="Expand Chat"
        @click="rightOpen = true"
      >‹</button>
      <span
        class="text-gray-500 text-xs font-medium"
        style="writing-mode: vertical-rl; transform: rotate(180deg)"
      >Chat</span>
    </div>
  </div>
</template>
