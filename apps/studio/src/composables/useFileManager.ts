import { computed, ref, shallowRef } from 'vue';
import type { FileEntry, WorkspaceState } from '../types/index.ts';

function detectType(filename: string): FileEntry['type'] {
  if (filename.endsWith('.aimd')) return 'aimd';
  if (filename.endsWith('.py')) return 'py';
  return 'other';
}

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function parseDownloadFilename(contentDisposition: string | null, fallback: string): string {
  if (!contentDisposition) return fallback;
  const match = /filename="?([^"]+)"?/i.exec(contentDisposition);
  return match?.[1]?.trim() || fallback;
}

async function readApiError(res: Response): Promise<string> {
  const fallback = `Workspace API error ${res.status}`;
  try {
    const text = await res.text();
    if (!text.trim()) return fallback;
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      return parsed.detail ? `${fallback}: ${parsed.detail}` : `${fallback}: ${text}`;
    } catch {
      return `${fallback}: ${text}`;
    }
  } catch {
    return fallback;
  }
}

async function requestWorkspace<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return res.json() as Promise<T>;
}

function normalizeEntries(entries: FileEntry[]): FileEntry[] {
  return [...entries].sort((a, b) => a.path.localeCompare(b.path));
}

export function useFileManager() {
  const files = shallowRef<FileEntry[]>([]);
  const activeFile = shallowRef<FileEntry | null>(null);
  const hasManualChanges = ref(false);
  const folders = shallowRef<string[]>([]);
  const workspaceRoot = ref<string | null>(null);
  const workspaceEntryCount = ref(0);
  const canSelectDirectory = ref(true);
  const isLoadingWorkspace = ref(true);
  const workspaceError = ref<string | null>(null);

  const hasWorkspace = computed(() => workspaceRoot.value !== null);

  function applyWorkspaceState(state: WorkspaceState) {
    const previousActivePath = activeFile.value?.path;
    files.value = normalizeEntries(state.files);
    folders.value = [...state.folders];
    workspaceRoot.value = state.root_path;
    workspaceEntryCount.value = state.entry_count;
    canSelectDirectory.value = state.can_select_directory;
    hasManualChanges.value = false;

    if (previousActivePath) {
      activeFile.value = files.value.find(file => file.path === previousActivePath) ?? files.value[0] ?? null;
    } else {
      activeFile.value = files.value[0] ?? null;
    }
  }

  async function refreshWorkspace() {
    isLoadingWorkspace.value = true;
    try {
      const state = await requestWorkspace<WorkspaceState>('/api/endpoints/workspace');
      applyWorkspaceState(state);
      workspaceError.value = null;
    } catch (error) {
      workspaceError.value = error instanceof Error ? error.message : 'Failed to load workspace.';
    } finally {
      isLoadingWorkspace.value = false;
    }
  }

  async function selectWorkspace() {
    isLoadingWorkspace.value = true;
    try {
      const state = await requestWorkspace<WorkspaceState>('/api/endpoints/workspace/select', {
        method: 'POST',
      });
      applyWorkspaceState(state);
      workspaceError.value = null;
    } catch (error) {
      workspaceError.value = error instanceof Error ? error.message : 'Failed to select workspace.';
    } finally {
      isLoadingWorkspace.value = false;
    }
  }

  async function openWorkspace(path: string) {
    isLoadingWorkspace.value = true;
    try {
      const state = await requestWorkspace<WorkspaceState>('/api/endpoints/workspace/open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });
      applyWorkspaceState(state);
      workspaceError.value = null;
    } catch (error) {
      workspaceError.value = error instanceof Error ? error.message : 'Failed to open workspace path.';
    } finally {
      isLoadingWorkspace.value = false;
    }
  }

  async function uploadZip(file: File) {
    if (!hasWorkspace.value) {
      workspaceError.value = 'Choose a workspace directory before importing a ZIP.';
      return;
    }

    try {
      const state = await requestWorkspace<WorkspaceState>('/api/endpoints/workspace/import-zip', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/zip',
        },
        body: file,
      });
      applyWorkspaceState(state);
      workspaceError.value = null;
    } catch (error) {
      workspaceError.value = error instanceof Error ? error.message : 'Failed to import ZIP.';
    }
  }

  async function downloadZip() {
    if (!hasWorkspace.value) {
      workspaceError.value = 'Choose a workspace directory before exporting a ZIP.';
      return;
    }

    try {
      const res = await fetch('/api/endpoints/workspace/export-zip');
      if (!res.ok) {
        throw new Error(await readApiError(res));
      }
      const blob = await res.blob();
      const fallbackName = workspaceRoot.value
        ? `${workspaceRoot.value.split('/').filter(Boolean).pop() ?? 'workspace'}.zip`
        : 'workspace.zip';
      const filename = parseDownloadFilename(res.headers.get('Content-Disposition'), fallbackName);
      triggerBrowserDownload(blob, filename);
      workspaceError.value = null;
    } catch (error) {
      workspaceError.value = error instanceof Error ? error.message : 'Failed to export ZIP.';
    }
  }

  function updateFileContent(path: string, content: string) {
    files.value = files.value.map(f => f.path === path ? { ...f, content } : f);
    if (activeFile.value?.path === path) {
      activeFile.value = { ...activeFile.value, content };
    }

    if (!hasWorkspace.value) {
      workspaceError.value = 'Choose a workspace directory before editing files.';
      return;
    }

    void requestWorkspace<WorkspaceState>('/api/endpoints/workspace/file', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content }),
    })
      .then((state) => {
        applyWorkspaceState(state);
        workspaceError.value = null;
      })
      .catch((error) => {
        workspaceError.value = error instanceof Error ? error.message : 'Failed to save file.';
        void refreshWorkspace();
      });
  }

  function createFile(
    name: string,
    content: string,
    type?: FileEntry['type'],
    isManual = false,
    activate = true,
  ) {
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
      if (activeFile.value?.path === name) {
        activeFile.value = { ...activeFile.value, content };
      }
    } else {
      files.value = normalizeEntries([...files.value, entry]);
    }
    if (activate) {
      activeFile.value = entry;
    }
    if (isManual) hasManualChanges.value = true;

    if (!hasWorkspace.value) {
      workspaceError.value = 'Choose a workspace directory before creating files.';
      return;
    }

    const method = existing ? 'PUT' : 'POST';
    void requestWorkspace<WorkspaceState>('/api/endpoints/workspace/file', {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: name, content }),
    })
      .then((state) => {
        applyWorkspaceState(state);
        workspaceError.value = null;
      })
      .catch((error) => {
        workspaceError.value = error instanceof Error ? error.message : 'Failed to create file.';
        void refreshWorkspace();
      });
  }

  function deleteFile(path: string) {
    files.value = files.value.filter(f => f.path !== path);
    if (activeFile.value?.path === path) activeFile.value = null;
    hasManualChanges.value = true;

    if (!hasWorkspace.value) {
      workspaceError.value = 'Choose a workspace directory before deleting files.';
      return;
    }

    const encodedPath = encodeURIComponent(path);
    void requestWorkspace<WorkspaceState>(`/api/endpoints/workspace/file?path=${encodedPath}`, {
      method: 'DELETE',
    })
      .then((state) => {
        applyWorkspaceState(state);
        workspaceError.value = null;
      })
      .catch((error) => {
        workspaceError.value = error instanceof Error ? error.message : 'Failed to delete file.';
        void refreshWorkspace();
      });
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

    if (!hasWorkspace.value) {
      workspaceError.value = 'Choose a workspace directory before renaming files.';
      return;
    }

    void requestWorkspace<{ path: string }>('/api/endpoints/workspace/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old_path: oldPath, new_name: newName }),
    })
      .then(() => refreshWorkspace())
      .catch((error) => {
        workspaceError.value = error instanceof Error ? error.message : 'Failed to rename file.';
        void refreshWorkspace();
      });
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

    if (!hasWorkspace.value) {
      workspaceError.value = 'Choose a workspace directory before creating folders.';
      return;
    }

    void requestWorkspace<WorkspaceState>('/api/endpoints/workspace/folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: folderPath }),
    })
      .then((state) => {
        applyWorkspaceState(state);
        workspaceError.value = null;
      })
      .catch((error) => {
        workspaceError.value = error instanceof Error ? error.message : 'Failed to create folder.';
        void refreshWorkspace();
      });
  }

  void refreshWorkspace();

  return {
    files,
    folders,
    activeFile,
    hasManualChanges,
    workspaceRoot,
    workspaceEntryCount,
    canSelectDirectory,
    isLoadingWorkspace,
    workspaceError,
    hasWorkspace,
    uploadZip,
    downloadZip,
    updateFileContent,
    createFile,
    deleteFile,
    renameFile,
    selectFile,
    createFolder,
    refreshWorkspace,
    selectWorkspace,
    openWorkspace,
  };
}
