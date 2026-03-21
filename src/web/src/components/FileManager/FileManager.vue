<script setup lang="ts">
import { ref } from 'vue';
import type { FileEntry } from '../../types/index.ts';
import FileTree from './FileTree.vue';
import logoIconUrl from '../../assets/airalogy-logo.svg';

const props = defineProps<{
  files: FileEntry[];
  folders: string[];
  activeFile: FileEntry | null;
  hasManualChanges: boolean;
}>();

const emit = defineEmits<{
  upload: [file: File];
  download: [];
  select: [path: string];
  delete: [path: string];
  rename: [oldPath: string, newName: string];
  createFile: [name: string, content: string];
  createFolder: [name: string];
  collapse: [];
}>();

const inputRef = ref<HTMLInputElement | null>(null);
const createMode = ref<'file' | 'folder' | null>(null);
const newName = ref('');
const showOverwriteWarning = ref(false);
let pendingFile: File | null = null;

function handleUploadClick() {
  inputRef.value?.click();
}

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  target.value = '';
  if (props.hasManualChanges && props.files.length > 0) {
    pendingFile = file;
    showOverwriteWarning.value = true;
  } else {
    emit('upload', file);
  }
}

function confirmOverwrite() {
  if (pendingFile) emit('upload', pendingFile);
  pendingFile = null;
  showOverwriteWarning.value = false;
}

function cancelOverwrite() {
  pendingFile = null;
  showOverwriteWarning.value = false;
}

function handleCreate() {
  const trimmed = newName.value.trim();
  if (!trimmed) return;
  if (createMode.value === 'file') {
    const finalName = trimmed.includes('.') ? trimmed : trimmed + '.aimd';
    emit('createFile', finalName, '');
  } else if (createMode.value === 'folder') {
    emit('createFolder', trimmed);
  }
  newName.value = '';
  createMode.value = null;
}

function handleCreateKey(e: KeyboardEvent) {
  if (e.key === 'Enter') handleCreate();
  if (e.key === 'Escape') { createMode.value = null; newName.value = ''; }
}
</script>

<template>
  <div class="files-shell">
    <div class="files-shell__header">
      <div>
        <div class="files-shell__brand">
          <span class="files-shell__brand-mark">
            <img :src="logoIconUrl" alt="Airalogy logo" class="files-shell__brand-image" />
          </span>
          <span class="files-shell__brand-copy">
            <span class="files-shell__brand-name">Airalogy</span>
            <span class="files-shell__brand-product">Masterbrain</span>
          </span>
        </div>
        <p class="files-shell__eyebrow">Project Files</p>
        <h2 class="files-shell__title">Workspace Assets</h2>
      </div>
      <div class="files-shell__actions">
        <button
          title="New File"
          class="files-shell__action-button"
          @click="createMode = 'file'; newName = ''"
        >＋ File</button>
        <button
          title="New Folder"
          class="files-shell__action-button"
          @click="createMode = 'folder'; newName = ''"
        >＋ Folder</button>
        <button
          title="Collapse panel"
          class="files-shell__icon-button"
          @click="emit('collapse')"
        >‹</button>
      </div>
    </div>

    <div class="files-shell__meta">
      <span>{{ props.files.length }} files</span>
      <span>{{ props.folders.length }} folders</span>
      <span>{{ props.hasManualChanges ? 'Local edits' : 'Synced workspace' }}</span>
    </div>

    <div v-if="createMode" class="files-shell__card">
      <p class="files-shell__card-label">
        {{ createMode === 'file' ? 'New file name' : 'New folder name' }}
      </p>
      <input
        v-model="newName"
        autofocus
        :placeholder="createMode === 'file' ? 'e.g. protocol.aimd' : 'e.g. experiments'"
        class="files-shell__input"
        @keydown="handleCreateKey"
      />
      <div class="files-shell__card-actions">
        <button class="files-shell__primary-button" @click="handleCreate">Create</button>
        <button class="files-shell__secondary-button" @click="createMode = null; newName = ''">Cancel</button>
      </div>
    </div>

    <div v-if="showOverwriteWarning" class="files-shell__warning">
      <p class="files-shell__warning-title">Overwrite warning</p>
      <p class="files-shell__warning-text">The workspace contains local edits. Uploading a ZIP will replace the current content.</p>
      <div class="files-shell__card-actions">
        <button class="files-shell__warning-button" @click="confirmOverwrite">Overwrite</button>
        <button class="files-shell__secondary-button" @click="cancelOverwrite">Cancel</button>
      </div>
    </div>

    <div class="files-shell__tree">
      <FileTree
        :files="props.files"
        :folders="props.folders"
        :active-file="props.activeFile"
        @select="(path) => emit('select', path)"
        @delete="(path) => emit('delete', path)"
        @rename="(oldPath, newNameVal) => emit('rename', oldPath, newNameVal)"
      />
    </div>

    <div class="files-shell__footer">
      <input ref="inputRef" type="file" accept=".zip" class="hidden" @change="handleFileChange" />
      <button
        class="files-shell__primary-button"
        @click="handleUploadClick"
      >Upload ZIP</button>
      <button
        :disabled="props.files.length === 0"
        class="files-shell__secondary-button"
        @click="emit('download')"
      >Download ZIP</button>
    </div>
  </div>
</template>

<style scoped>
.files-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
  color: var(--text-primary);
}

.files-shell__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid var(--border-color);
}

.files-shell__brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.files-shell__brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 6px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(63, 102, 255, 0.14) 0%, rgba(20, 174, 255, 0.12) 100%);
  box-shadow: 0 16px 28px -22px rgba(37, 99, 235, 0.45);
}

.files-shell__brand-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.files-shell__brand-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.files-shell__brand-name {
  font-size: 14px;
  font-weight: 800;
  color: var(--text-primary);
}

.files-shell__brand-product {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--text-muted);
}

.files-shell__eyebrow {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--text-muted);
}

.files-shell__title {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
  color: var(--text-primary);
}

.files-shell__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.files-shell__action-button,
.files-shell__icon-button,
.files-shell__primary-button,
.files-shell__secondary-button,
.files-shell__warning-button {
  border: none;
  cursor: pointer;
  transition: transform 0.2s ease, background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.files-shell__action-button,
.files-shell__icon-button {
  padding: 8px 10px;
  border-radius: 12px;
  background: var(--panel-subtle);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.files-shell__icon-button {
  width: 34px;
  height: 34px;
  padding: 0;
  border-radius: 999px;
  font-size: 18px;
}

.files-shell__action-button:hover,
.files-shell__icon-button:hover {
  background: var(--accent-soft);
  color: var(--accent);
  transform: translateY(-1px);
}

.files-shell__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 18px 0;
}

.files-shell__meta span {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--panel-solid);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
}

.files-shell__card,
.files-shell__warning {
  margin: 14px 18px 0;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.files-shell__card-label,
.files-shell__warning-title {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
}

.files-shell__warning-title {
  color: var(--warning);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.files-shell__warning-text {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-secondary);
}

.files-shell__input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--accent-border);
  border-radius: 14px;
  background: var(--panel-muted);
  color: var(--text-primary);
  outline: none;
}

.files-shell__input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.files-shell__card-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.files-shell__primary-button,
.files-shell__secondary-button,
.files-shell__warning-button {
  width: 100%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 700;
}

.files-shell__primary-button {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: #ffffff;
  box-shadow: 0 16px 28px -18px rgba(37, 99, 235, 0.6);
}

.files-shell__primary-button:hover,
.files-shell__warning-button:hover,
.files-shell__secondary-button:hover {
  transform: translateY(-1px);
}

.files-shell__secondary-button {
  background: var(--panel-subtle);
  color: var(--text-secondary);
}

.files-shell__secondary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.files-shell__warning-button {
  background: #f59e0b;
  color: #ffffff;
}

.files-shell__tree {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 14px 12px 18px;
}

.files-shell__footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 18px 18px;
  border-top: 1px solid var(--border-color);
}
</style>
