<script setup lang="ts">
import { ref } from 'vue';
import type { FileEntry } from '../../types/index.ts';

const props = defineProps<{
  files: FileEntry[];
  folders: string[];
  activeFile: FileEntry | null;
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
  <div v-if="props.files.length === 0 && props.folders.length === 0" class="text-xs text-gray-500 px-3 py-4 text-center leading-relaxed">
    Upload a ZIP or click ＋ to add files
  </div>
  <div v-else class="text-sm select-none">
    <div v-for="group in groupByFolder(props.files, props.folders)" :key="group.folder ?? '__root__'">
      <div
        v-if="group.folder !== null"
        class="flex items-center gap-1 px-2 py-1 text-xs text-gray-500 cursor-pointer hover:text-gray-300"
        @click="toggleFolder(group.folder!)"
      >
        <span class="text-gray-600">{{ collapsedFolders.has(group.folder!) ? '▶' : '▼' }}</span>
        <span>📁 {{ group.folder }}</span>
        <span v-if="group.files.length === 0" class="ml-auto text-gray-600 italic">empty</span>
      </div>
      <template v-if="!collapsedFolders.has(group.folder ?? '')">
        <div
          v-for="f in group.files"
          :key="f.path"
          :class="[
            'flex items-center gap-1.5 py-1.5 cursor-pointer rounded mx-1',
            group.folder !== null ? 'pl-5 pr-2' : 'px-2',
            props.activeFile?.path === f.path
              ? 'bg-blue-600 text-white'
              : 'hover:bg-gray-700 text-gray-300',
          ]"
          @mouseenter="hoveredPath = f.path"
          @mouseleave="hoveredPath = null"
          @click="renamingPath !== f.path && emit('select', f.path)"
        >
          <span class="flex-shrink-0 text-xs">{{ fileIcon[f.type] }}</span>
          <input
            v-if="renamingPath === f.path"
            v-model="renameValue"
            autofocus
            class="flex-1 min-w-0 bg-gray-900 border border-blue-400 rounded px-1 text-xs text-white outline-none"
            @blur="confirmRename"
            @keydown="handleRenameKey"
            @click.stop
          />
          <span v-else class="flex-1 min-w-0 truncate text-xs" :title="f.path">{{ f.name }}</span>
          <span v-if="hoveredPath === f.path && renamingPath !== f.path" class="flex-shrink-0 flex gap-0.5 ml-auto">
            <button
              title="Rename"
              class="p-0.5 rounded text-xs text-gray-400 hover:text-white hover:bg-gray-600"
              @click="startRename(f, $event)"
            >✏</button>
            <button
              title="Delete"
              class="p-0.5 rounded text-xs text-gray-400 hover:text-red-300 hover:bg-red-900"
              @click="handleDelete(f, $event)"
            >🗑</button>
          </span>
        </div>
      </template>
    </div>
  </div>
</template>
