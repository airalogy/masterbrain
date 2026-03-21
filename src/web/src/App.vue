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
const theme = ref<Theme>('light');

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
  <div class="workspace-shell">
    <div v-if="leftOpen" class="workspace-shell__sidebar">
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
      class="workspace-shell__rail workspace-shell__rail--left"
    >
      <button
        class="workspace-shell__rail-button"
        title="Expand Files"
        @click="leftOpen = true"
      >›</button>
      <span class="workspace-shell__rail-label">Files</span>
    </div>

    <div class="workspace-shell__main">
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

    <div v-if="rightOpen" class="workspace-shell__chat">
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
      class="workspace-shell__rail workspace-shell__rail--right"
    >
      <button
        class="workspace-shell__rail-button"
        title="Expand Chat"
        @click="rightOpen = true"
      >‹</button>
      <span class="workspace-shell__rail-label">Chat</span>
    </div>
  </div>
</template>

<style scoped>
.workspace-shell {
  display: flex;
  gap: 16px;
  width: 100vw;
  height: 100vh;
  padding: 16px;
  overflow: hidden;
}

.workspace-shell__sidebar {
  width: 288px;
  flex-shrink: 0;
  min-height: 0;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  overflow: hidden;
  background: var(--panel-bg);
  backdrop-filter: blur(22px);
  box-shadow: var(--shadow-md);
}

.workspace-shell__main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  border: 1px solid var(--border-color);
  border-radius: 28px;
  overflow: hidden;
  background: var(--panel-bg);
  backdrop-filter: blur(22px);
  box-shadow: var(--shadow-lg);
}

.workspace-shell__chat {
  width: 420px;
  flex-shrink: 0;
  min-height: 0;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  overflow: hidden;
  background: var(--panel-bg);
  backdrop-filter: blur(22px);
  box-shadow: var(--shadow-md);
}

.workspace-shell__rail {
  width: 52px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--panel-bg);
  backdrop-filter: blur(18px);
  color: var(--text-muted);
}

.workspace-shell__rail-button {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 999px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.workspace-shell__rail-button:hover {
  background: var(--accent-soft);
  color: var(--accent);
  transform: translateY(-1px);
}

.workspace-shell__rail-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
}

@media (max-width: 1280px) {
  .workspace-shell__sidebar {
    width: 248px;
  }

  .workspace-shell__chat {
    width: 360px;
  }
}

@media (max-width: 980px) {
  .workspace-shell {
    flex-direction: column;
    padding: 12px;
  }

  .workspace-shell__sidebar,
  .workspace-shell__chat,
  .workspace-shell__main {
    width: 100%;
  }

  .workspace-shell__sidebar,
  .workspace-shell__chat {
    min-height: 280px;
  }

  .workspace-shell__main {
    min-height: 420px;
  }

  .workspace-shell__rail {
    width: 100%;
    height: 52px;
    flex-direction: row;
  }

  .workspace-shell__rail-label {
    writing-mode: horizontal-tb;
    transform: none;
  }
}
</style>
