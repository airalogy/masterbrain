<script setup lang="ts">
import { ref } from 'vue';
import type { FileEntry } from '../../types/index.ts';
import FileTree from './FileTree.vue';

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
  <div class="flex flex-col h-full bg-gray-900 border-r border-gray-700">
    <!-- Header -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-gray-700">
      <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Files</h2>
      <div class="flex items-center gap-1">
        <button
          title="New File"
          class="text-xs text-gray-400 hover:text-white hover:bg-gray-700 px-1.5 h-5 flex items-center rounded"
          @click="createMode = 'file'; newName = ''"
        >＋ File</button>
        <button
          title="New Folder"
          class="text-xs text-gray-400 hover:text-white hover:bg-gray-700 px-1.5 h-5 flex items-center rounded"
          @click="createMode = 'folder'; newName = ''"
        >＋ Folder</button>
        <button
          title="Collapse panel"
          class="text-gray-500 hover:text-white hover:bg-gray-700 w-5 h-5 flex items-center justify-center rounded text-sm"
          @click="emit('collapse')"
        >‹</button>
      </div>
    </div>

    <!-- New file / folder input -->
    <div v-if="createMode" class="px-2 py-1.5 border-b border-gray-700 bg-gray-800">
      <p class="text-xs text-gray-500 mb-1">
        {{ createMode === 'file' ? 'New file name' : 'New folder name' }}
      </p>
      <input
        v-model="newName"
        autofocus
        :placeholder="createMode === 'file' ? 'e.g. protocol.aimd' : 'e.g. experiments'"
        class="w-full bg-gray-900 border border-blue-500 rounded px-2 py-1 text-xs text-gray-200 outline-none placeholder-gray-600"
        @keydown="handleCreateKey"
      />
      <div class="flex gap-1 mt-1">
        <button class="flex-1 text-xs py-0.5 bg-blue-600 hover:bg-blue-500 text-white rounded" @click="handleCreate">Create</button>
        <button class="flex-1 text-xs py-0.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded" @click="createMode = null; newName = ''">Cancel</button>
      </div>
    </div>

    <!-- Overwrite warning -->
    <div v-if="showOverwriteWarning" class="mx-2 my-1.5 p-2 bg-yellow-900 border border-yellow-600 rounded text-xs text-yellow-200">
      <p class="font-medium mb-1">⚠ Overwrite Warning</p>
      <p class="text-yellow-300 mb-2">The workspace has manually modified files. Uploading a ZIP will overwrite all content.</p>
      <div class="flex gap-1">
        <button class="flex-1 py-0.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded" @click="confirmOverwrite">Overwrite</button>
        <button class="flex-1 py-0.5 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded" @click="cancelOverwrite">Cancel</button>
      </div>
    </div>

    <!-- File Tree -->
    <div class="flex-1 overflow-y-auto py-1">
      <FileTree
        :files="props.files"
        :folders="props.folders"
        :active-file="props.activeFile"
        @select="(path) => emit('select', path)"
        @delete="(path) => emit('delete', path)"
        @rename="(oldPath, newNameVal) => emit('rename', oldPath, newNameVal)"
      />
    </div>

    <!-- Upload / Download -->
    <div class="border-t border-gray-700 p-2 flex flex-col gap-1.5">
      <input ref="inputRef" type="file" accept=".zip" class="hidden" @change="handleFileChange" />
      <button
        class="w-full py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
        @click="handleUploadClick"
      >⬆ Upload ZIP</button>
      <button
        :disabled="props.files.length === 0"
        class="w-full py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-white text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        @click="emit('download')"
      >⬇ Download ZIP</button>
    </div>
  </div>
</template>
