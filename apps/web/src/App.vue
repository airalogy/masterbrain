<script setup lang="ts">
import { ref, watch } from 'vue';
import FileManager from './components/FileManager/FileManager.vue';
import LibraryPanel from './components/FileManager/LibraryPanel.vue';
import EditorPanel from './components/EditorPanel/EditorPanel.vue';
import ChatPanel from './components/ChatPanel/ChatPanel.vue';
import { useFileManager } from './composables/useFileManager.ts';
import { useLibrary } from './composables/useLibrary.ts';
import { useChat } from './composables/useChat.ts';
import { provideTheme, type Theme } from './composables/useTheme.ts';
import type { CodeChange, EditorSelection, PreviewState } from './types/index.ts';

const leftOpen = ref(true);
const rightOpen = ref(true);
const leftView = ref<'workspace' | 'library'>('workspace');
const theme = ref<Theme>('light');

provideTheme(theme);

watch(theme, (val) => {
  const html = document.documentElement;
  html.classList.toggle('light', val === 'light');
  html.classList.toggle('dark', val === 'dark');
}, { immediate: true });

const {
  files, activeFile, hasManualChanges, folders,
  workspaceRoot, workspaceEntryCount, canSelectDirectory, isLoadingWorkspace, workspaceError, hasWorkspace,
  uploadZip, downloadZip, updateFileContent, createFile, deleteFile, renameFile, selectFile, createFolder,
  refreshWorkspace, selectWorkspace, openWorkspace,
} = useFileManager();

const {
  libraryState, isLoadingLibrary, isLoadingPreview, libraryError, lastImportResult,
  selectedProtocolPreview, selectedRecordDetail,
  refreshLibrary, importAiraPath, importAiraFile, previewProtocol, previewRecord, loadProtocolToWorkspace,
} = useLibrary();

watch(
  [() => libraryState.value.archive_count, () => hasWorkspace.value],
  ([archiveCount, workspaceReady]) => {
    if (archiveCount > 0 && !workspaceReady) {
      leftView.value = 'library';
    }
  },
  { immediate: true },
);

const previewState = ref<PreviewState | null>(null);
const editorSelection = ref<EditorSelection | null>(null);

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
  sendMessage, applyBlock, dismissBlock, removeChangedFile, dismissChangedFiles, clearMessages,
  confirmStep, regenerateStep,
} = useChat(files, activeFile, editorSelection, hasWorkspace, handleApplyContent, handleAutoApply);

function handleEditorChange(content: string) {
  if (activeFile.value) updateFileContent(activeFile.value.path, content);
}

function handleSelectionChange(selection: EditorSelection | null) {
  editorSelection.value = selection;
}

function applyCodeChange(change: CodeChange, activate = false) {
  if (change.status === 'deleted') {
    deleteFile(change.path);
    return;
  }

  const existing = files.value.find(file => file.path === change.path);
  if (existing) {
    updateFileContent(change.path, change.content);
    if (activate) selectFile(change.path);
    return;
  }

  createFile(change.path, change.content, change.type, false, activate);
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
  previewState.value = {
    source: 'block',
    content,
    type,
    msgId,
    name: type === 'aimd' ? 'preview.aimd' : 'preview.py',
  };
}

function handlePreviewChangedFile(change: CodeChange, msgId: string) {
  previewState.value = {
    source: 'change',
    content: change.content,
    type: change.type,
    msgId,
    name: change.name,
    path: change.path,
  };
}

function handleKeepPreview() {
  if (!previewState.value) return;
  if (previewState.value.source === 'change' && previewState.value.path) {
    applyCodeChange({
      path: previewState.value.path,
      name: previewState.value.name,
      type: previewState.value.type,
      status: 'modified',
      content: previewState.value.content,
      diff: '',
    }, true);
    removeChangedFile(previewState.value.msgId, previewState.value.path);
  } else {
    handleApplyContent(previewState.value.content, previewState.value.type);
    dismissBlock(previewState.value.msgId);
  }
  previewState.value = null;
}

function handleDiscardPreview() {
  previewState.value = null;
}

function handleCreateFile(name: string, content: string) {
  createFile(name, content, undefined, true);
}

async function handleImportAiraPath(path: string) {
  try {
    await importAiraPath(path);
  } catch {
    // Error state is already surfaced inside the library panel.
  }
}

async function handleImportAiraFile(file: File) {
  try {
    await importAiraFile(file);
  } catch {
    // Error state is already surfaced inside the library panel.
  }
}

async function handleLoadProtocol(protocolId: number) {
  const loaded = await loadProtocolToWorkspace(protocolId);
  if (!loaded) return;
  await refreshWorkspace();
  leftView.value = 'workspace';
}

function handleApplyChangedFile(change: CodeChange, msgId: string) {
  applyCodeChange(change, change.status !== 'deleted');
  removeChangedFile(msgId, change.path);
  if (previewState.value?.source === 'change' && previewState.value.path === change.path) {
    previewState.value = null;
  }
}

function handleApplyAllChangedFiles(changes: CodeChange[], msgId: string) {
  for (const change of changes) {
    applyCodeChange(change, false);
  }
  dismissChangedFiles(msgId);
  if (previewState.value?.source === 'change') {
    previewState.value = null;
  }
}
</script>

<template>
  <div class="workspace-shell">
    <div v-if="leftOpen" class="workspace-shell__sidebar">
      <div class="workspace-shell__sidebar-tabs">
        <button
          :class="['workspace-shell__sidebar-tab', leftView === 'workspace' ? 'workspace-shell__sidebar-tab--active' : '']"
          @click="leftView = 'workspace'"
        >Workspace</button>
        <button
          :class="['workspace-shell__sidebar-tab', leftView === 'library' ? 'workspace-shell__sidebar-tab--active' : '']"
          @click="leftView = 'library'"
        >Library</button>
      </div>
      <FileManager
        v-if="leftView === 'workspace'"
        :files="files"
        :folders="folders"
        :active-file="activeFile"
        :has-manual-changes="hasManualChanges"
        :workspace-root="workspaceRoot"
        :workspace-entry-count="workspaceEntryCount"
        :has-workspace="hasWorkspace"
        :can-select-directory="canSelectDirectory"
        :is-loading-workspace="isLoadingWorkspace"
        :workspace-error="workspaceError"
        @upload="uploadZip"
        @download="downloadZip"
        @select="selectFile"
        @delete="deleteFile"
        @rename="renameFile"
        @create-file="handleCreateFile"
        @create-folder="createFolder"
        @select-workspace="selectWorkspace"
        @open-workspace="openWorkspace"
        @refresh-workspace="refreshWorkspace"
        @collapse="leftOpen = false"
      />
      <LibraryPanel
        v-else
        :library-state="libraryState"
        :has-workspace="hasWorkspace"
        :is-loading-library="isLoadingLibrary"
        :is-loading-preview="isLoadingPreview"
        :library-error="libraryError"
        :last-import-result="lastImportResult"
        :selected-protocol-preview="selectedProtocolPreview"
        :selected-record-detail="selectedRecordDetail"
        @import-file="handleImportAiraFile"
        @import-path="handleImportAiraPath"
        @refresh-library="refreshLibrary"
        @preview-protocol="previewProtocol"
        @preview-record="previewRecord"
        @load-protocol="handleLoadProtocol"
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
        :has-workspace="hasWorkspace"
        @change="handleEditorChange"
        @keep-preview="handleKeepPreview"
        @discard-preview="handleDiscardPreview"
        @selection-change="handleSelectionChange"
      />
    </div>

    <div v-if="rightOpen" class="workspace-shell__chat">
      <ChatPanel
        :messages="messages"
        :is-streaming="isStreaming"
        :model="model"
        :router="router"
        :theme="theme"
        :has-workspace="hasWorkspace"
        @update:model="model = $event"
        @update:router="router = $event"
        @theme-toggle="theme = theme === 'dark' ? 'light' : 'dark'"
        @send="sendMessage"
        @apply-block="handleApplyBlock"
        @dismiss-block="dismissBlock"
        @preview-block="handlePreviewBlock"
        @preview-changed-file="handlePreviewChangedFile"
        @apply-changed-file="handleApplyChangedFile"
        @apply-all-changed-files="handleApplyAllChangedFiles"
        @dismiss-changed-files="dismissChangedFiles"
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
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  overflow: hidden;
  background: var(--panel-bg);
  backdrop-filter: blur(22px);
  box-shadow: var(--shadow-md);
}

.workspace-shell__sidebar-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 12px 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent);
}

.workspace-shell__sidebar-tab {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--panel-subtle);
  color: var(--text-muted);
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.workspace-shell__sidebar-tab--active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent);
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
