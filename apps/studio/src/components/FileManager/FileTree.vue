<script setup lang="ts">
import { ref } from 'vue';
import type { FileEntry } from '../../types/index.ts';

const props = defineProps<{
  files: FileEntry[];
  folders: string[];
  activeFile: FileEntry | null;
  hasWorkspace: boolean;
}>();

const emit = defineEmits<{
  select: [path: string];
  delete: [path: string];
  rename: [oldPath: string, newName: string];
}>();

const fileIcon: Record<FileEntry['type'], string> = {
  aimd: '📄',
  py: '🐍',
  other: '📁',
};

interface TreeGroup {
  folder: string | null;
  files: FileEntry[];
}

function groupByFolder(files: FileEntry[], explicitFolders: string[]): TreeGroup[] {
  const map = new Map<string | null, FileEntry[]>();
  for (const folder of explicitFolders) {
    if (!map.has(folder)) map.set(folder, []);
  }
  for (const f of files) {
    const slash = f.path.lastIndexOf('/');
    const folder = slash >= 0 ? f.path.slice(0, slash) : null;
    if (!map.has(folder)) map.set(folder, []);
    map.get(folder)!.push(f);
  }
  const groups: TreeGroup[] = [];
  if (map.has(null)) groups.push({ folder: null, files: map.get(null)! });
  for (const [folder, groupFiles] of map) {
    if (folder !== null) groups.push({ folder, files: groupFiles });
  }
  return groups;
}

const hoveredPath = ref<string | null>(null);
const renamingPath = ref<string | null>(null);
const renameValue = ref('');
const collapsedFolders = ref<Set<string>>(new Set());

function startRename(f: FileEntry, e: MouseEvent) {
  e.stopPropagation();
  renamingPath.value = f.path;
  renameValue.value = f.name;
}

function confirmRename() {
  if (renamingPath.value && renameValue.value.trim()) {
    emit('rename', renamingPath.value, renameValue.value.trim());
  }
  renamingPath.value = null;
}

function handleRenameKey(e: KeyboardEvent) {
  if (e.key === 'Enter') confirmRename();
  if (e.key === 'Escape') renamingPath.value = null;
}

function handleDelete(f: FileEntry, e: MouseEvent) {
  e.stopPropagation();
  if (window.confirm(`Delete file "${f.name}"?`)) emit('delete', f.path);
}

function toggleFolder(folder: string) {
  const next = new Set(collapsedFolders.value);
  if (next.has(folder)) next.delete(folder);
  else next.add(folder);
  collapsedFolders.value = next;
}
</script>

<template>
  <div v-if="!props.hasWorkspace" class="tree-empty">
    Choose a workspace folder to start browsing and editing files.
  </div>
  <div v-else-if="props.files.length === 0 && props.folders.length === 0" class="tree-empty">
    This workspace is empty. Create a file, add a folder, or import a ZIP archive.
  </div>
  <div v-else class="tree-list">
    <div v-for="group in groupByFolder(props.files, props.folders)" :key="group.folder ?? '__root__'">
      <div
        v-if="group.folder !== null"
        class="tree-folder"
        @click="toggleFolder(group.folder!)"
      >
        <span class="tree-folder__arrow">{{ collapsedFolders.has(group.folder!) ? '▶' : '▼' }}</span>
        <span class="tree-folder__label">📁 {{ group.folder }}</span>
        <span v-if="group.files.length === 0" class="tree-folder__empty">empty</span>
      </div>
      <template v-if="!collapsedFolders.has(group.folder ?? '')">
        <div
          v-for="f in group.files"
          :key="f.path"
          :class="[
            'tree-file',
            group.folder !== null ? 'tree-file--nested' : '',
            props.activeFile?.path === f.path ? 'tree-file--active' : '',
          ]"
          @mouseenter="hoveredPath = f.path"
          @mouseleave="hoveredPath = null"
          @click="renamingPath !== f.path && emit('select', f.path)"
        >
          <span class="tree-file__icon">{{ fileIcon[f.type] }}</span>
          <input
            v-if="renamingPath === f.path"
            v-model="renameValue"
            autofocus
            class="tree-file__input"
            @blur="confirmRename"
            @keydown="handleRenameKey"
            @click.stop
          />
          <span v-else class="tree-file__name" :title="f.path">{{ f.name }}</span>
          <span v-if="hoveredPath === f.path && renamingPath !== f.path" class="tree-file__actions">
            <button
              title="Rename"
              class="tree-file__action"
              @click="startRename(f, $event)"
            >✏</button>
            <button
              title="Delete"
              class="tree-file__action tree-file__action--danger"
              @click="handleDelete(f, $event)"
            >🗑</button>
          </span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.tree-empty {
  padding: 16px 12px;
  text-align: center;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-muted);
}

.tree-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  user-select: none;
}

.tree-folder {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 14px;
  color: var(--text-muted);
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.tree-folder:hover {
  background: var(--panel-subtle);
  color: var(--text-secondary);
}

.tree-folder__arrow,
.tree-folder__empty {
  font-size: 12px;
}

.tree-folder__label {
  font-size: 12px;
  font-weight: 600;
}

.tree-folder__empty {
  margin-left: auto;
  font-style: italic;
}

.tree-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 16px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.tree-file:hover {
  background: var(--panel-solid);
  transform: translateX(1px);
}

.tree-file--nested {
  margin-left: 18px;
}

.tree-file--active {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: #ffffff;
  box-shadow: 0 16px 28px -18px rgba(37, 99, 235, 0.65);
}

.tree-file__icon {
  flex-shrink: 0;
  font-size: 13px;
}

.tree-file__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 500;
}

.tree-file__input {
  flex: 1;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid var(--accent-border);
  border-radius: 12px;
  background: var(--panel-muted);
  color: var(--text-primary);
  outline: none;
}

.tree-file__actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.tree-file__action {
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: inherit;
  cursor: pointer;
}

.tree-file:not(.tree-file--active) .tree-file__action {
  background: var(--panel-subtle);
  color: var(--text-muted);
}

.tree-file__action--danger:hover {
  color: #ffffff;
  background: rgba(239, 68, 68, 0.85);
}

.tree-file__action:hover {
  color: #ffffff;
  background: rgba(37, 99, 235, 0.85);
}
</style>
