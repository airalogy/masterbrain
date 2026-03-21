import { ref, shallowRef } from 'vue';
import type { FileEntry } from '../types/index.ts';
import { extractZip, packZip, downloadBlob } from '../utils/zipUtils.ts';

function detectType(filename: string): FileEntry['type'] {
  if (filename.endsWith('.aimd')) return 'aimd';
  if (filename.endsWith('.py')) return 'py';
  return 'other';
}

export function useFileManager() {
  const files = shallowRef<FileEntry[]>([]);
  const activeFile = shallowRef<FileEntry | null>(null);
  const hasManualChanges = ref(false);
  const folders = shallowRef<string[]>([]);

  async function uploadZip(file: File) {
    const entries = await extractZip(file);
    files.value = entries;
    folders.value = [];
    hasManualChanges.value = false;
    if (entries.length > 0) activeFile.value = entries[0];
  }

  async function downloadZip() {
    if (files.value.length === 0) return;
    const blob = await packZip(files.value);
    downloadBlob(blob, 'workspace.zip');
  }

  function updateFileContent(path: string, content: string) {
    files.value = files.value.map(f => f.path === path ? { ...f, content } : f);
    if (activeFile.value?.path === path) {
      activeFile.value = { ...activeFile.value, content };
    }
  }

  function createFile(name: string, content: string, type?: FileEntry['type'], isManual = false) {
    const resolvedType = type ?? detectType(name);
    const entry: FileEntry = {
      name: name.split('/').pop() ?? name,
      path: name,
      content,
      type: resolvedType,
      isManual,
    };
    const existing = files.value.find(f => f.path === name);
    if (existing) {
      files.value = files.value.map(f => f.path === name ? { ...f, content } : f);
    } else {
      files.value = [...files.value, entry];
    }
    activeFile.value = entry;
    if (isManual) hasManualChanges.value = true;
  }

  function deleteFile(path: string) {
    files.value = files.value.filter(f => f.path !== path);
    if (activeFile.value?.path === path) activeFile.value = null;
    hasManualChanges.value = true;
  }

  function renameFile(oldPath: string, newName: string) {
    const dir = oldPath.includes('/') ? oldPath.slice(0, oldPath.lastIndexOf('/') + 1) : '';
    const newPath = dir + newName;
    const newType = detectType(newName);
    files.value = files.value.map(f =>
      f.path === oldPath ? { ...f, name: newName, path: newPath, type: newType } : f
    );
    if (activeFile.value?.path === oldPath) {
      activeFile.value = { ...activeFile.value, name: newName, path: newPath, type: newType };
    }
    hasManualChanges.value = true;
  }

  function selectFile(path: string) {
    const f = files.value.find(f => f.path === path);
    if (f) activeFile.value = f;
  }

  function createFolder(name: string) {
    const folderPath = name.trim().replace(/\/$/, '');
    if (!folderPath) return;
    if (!folders.value.includes(folderPath)) {
      folders.value = [...folders.value, folderPath];
    }
    hasManualChanges.value = true;
  }

  return {
    files,
    folders,
    activeFile,
    hasManualChanges,
    uploadZip,
    downloadZip,
    updateFileContent,
    createFile,
    deleteFile,
    renameFile,
    selectFile,
    createFolder,
  };
}
