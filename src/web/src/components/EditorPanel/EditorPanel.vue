<script setup lang="ts">
import { ref } from 'vue';
import type { FileEntry, PreviewState, ModelConfig, ProtocolDebugResponse } from '../../types/index.ts';
import { debugProtocol } from '../../utils/apiClient.ts';
import CodeEditor from './CodeEditor.vue';
import type { EditorSelection } from './CodeEditor.vue';
import AimdPreview from './AimdPreview.vue';

const props = defineProps<{
  activeFile: FileEntry | null;
  previewState: PreviewState | null;
  isDark: boolean;
  model: ModelConfig;
}>();

const emit = defineEmits<{
  change: [content: string];
  keepPreview: [];
  discardPreview: [];
}>();

interface DebugState {
  loading: boolean;
  result: ProtocolDebugResponse | null;
  error: string | null;
  selectionRange: { startOffset: number; endOffset: number } | null;
  originalText: string;
}

const EMPTY_DEBUG: DebugState = { loading: false, result: null, error: null, selectionRange: null, originalText: '' };

const debugState = ref<DebugState>({ ...EMPTY_DEBUG });
const selection = ref<EditorSelection | null>(null);

function handleSelectionChange(sel: EditorSelection | null) {
  selection.value = sel;
}

function getDisplayFile(): FileEntry | null {
  if (props.previewState) {
    return {
      name: props.previewState.type === 'aimd' ? 'preview.aimd' : 'preview.py',
      path: '__preview__',
      content: props.previewState.content,
      type: props.previewState.type,
    };
  }
  return props.activeFile;
}

async function handleDebug() {
  if (!props.activeFile || props.activeFile.type !== 'aimd' || !selection.value) return;
  const range = { startOffset: selection.value.startOffset, endOffset: selection.value.endOffset };
  debugState.value = { loading: true, result: null, error: null, selectionRange: range, originalText: selection.value.text };
  try {
    const result = await debugProtocol({
      full_protocol: props.activeFile.content,
      suspect_protocol: selection.value.text,
      model: { name: props.model.name, enable_thinking: props.model.enable_thinking, enable_search: false },
    });
    debugState.value = { loading: false, result, error: null, selectionRange: range, originalText: selection.value!.text };
  } catch (e: unknown) {
    const error = e instanceof Error ? e.message : 'Debug failed';
    debugState.value = { loading: false, result: null, error, selectionRange: null, originalText: '' };
  }
}

function handleApplyDebugFix() {
  if (!debugState.value.result || !debugState.value.selectionRange || !props.activeFile) return;
  const { startOffset, endOffset } = debugState.value.selectionRange;
  const content = props.activeFile.content;
  const newContent = content.slice(0, startOffset) + debugState.value.result.fixed_protocol + content.slice(endOffset);
  emit('change', newContent);
  debugState.value = { ...EMPTY_DEBUG };
}

function handleDiscardDebug() {
  debugState.value = { ...EMPTY_DEBUG };
}
</script>

<template>
  <!-- Empty state -->
  <div v-if="!getDisplayFile()" class="flex h-full flex-col items-center justify-center bg-gray-950 text-gray-500 text-sm">
    <div class="text-center">
      <div class="text-4xl mb-3">📂</div>
      <p>Select or upload a file from the left panel</p>
    </div>
  </div>

  <div v-else class="flex flex-col h-full bg-gray-950">
    <!-- Tab bar -->
    <div class="flex items-center px-4 py-1.5 bg-gray-900 border-b border-gray-700 text-xs">
      <!-- Preview mode banner -->
      <template v-if="props.previewState">
        <div class="flex items-center w-full gap-2">
          <span class="text-yellow-400 font-medium">👁 Preview</span>
          <span class="text-gray-500 truncate">AI-generated {{ props.previewState.type.toUpperCase() }}</span>
          <div class="ml-auto flex gap-1.5">
            <button
              class="px-2.5 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-xs font-medium transition-colors"
              @click="emit('keepPreview')"
            >✅ Keep</button>
            <button
              class="px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded text-xs transition-colors"
              @click="emit('discardPreview')"
            >✕ Discard</button>
          </div>
        </div>
      </template>
      <!-- Normal file tab -->
      <template v-else>
        <span class="mr-2">{{ getDisplayFile()!.type === 'aimd' ? '📄' : '🐍' }}</span>
        <span class="font-medium text-gray-200">{{ getDisplayFile()!.name }}</span>
        <div class="ml-auto flex items-center gap-3">
          <button
            v-if="props.activeFile?.type === 'aimd' && !props.previewState"
            :disabled="debugState.loading || !selection"
            :class="[
              'px-2.5 py-1 rounded text-xs font-medium transition-colors',
              !debugState.loading && selection
                ? 'bg-blue-600 hover:bg-blue-500 text-white cursor-pointer'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed',
            ]"
            :title="!debugState.loading && selection ? 'Debug selected text for AIMD syntax errors' : 'Select text in the editor to debug'"
            @click="handleDebug"
          >
            {{ debugState.loading ? '⏳ Checking...' : '🔍 Debug' }}
          </button>
          <span class="text-gray-600">{{ getDisplayFile()!.type.toUpperCase() }}</span>
        </div>
      </template>
    </div>

    <!-- Debug result panel: has errors -->
    <template v-if="debugState.result">
      <div v-if="debugState.result.has_errors" class="border-b border-blue-800 text-xs">
        <div class="flex items-center gap-2 px-4 py-2 bg-blue-950">
          <span class="text-yellow-400 font-medium">⚠ Found Errors</span>
          <div class="ml-auto flex gap-1.5">
            <button
              class="px-2.5 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-xs font-medium transition-colors"
              @click="handleApplyDebugFix"
            >✅ Apply Fix</button>
            <button
              class="px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded text-xs transition-colors"
              @click="handleDiscardDebug"
            >✕ Dismiss</button>
          </div>
        </div>
        <div v-if="debugState.result.response" class="px-4 py-2 bg-gray-900 border-t border-blue-900 text-blue-200 max-h-20 overflow-auto">
          <span class="font-medium text-blue-300">Reason: </span>
          {{ debugState.result.response }}
        </div>
        <div class="px-4 py-2 bg-gray-900 border-t border-blue-900 max-h-40 overflow-auto">
          <div class="text-gray-500 mb-1 font-medium">Fixed:</div>
          <pre class="text-green-300 whitespace-pre-wrap font-mono text-xs leading-relaxed">{{ debugState.result.fixed_protocol }}</pre>
        </div>
      </div>
      <!-- No errors -->
      <div v-else class="flex items-center gap-2 px-4 py-2 bg-green-950 border-b border-green-800 text-xs">
        <span class="text-green-400 font-medium">✅ No syntax errors found</span>
        <span v-if="debugState.result.response" class="text-green-300 truncate">— {{ debugState.result.response }}</span>
        <button
          class="ml-auto px-2.5 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded text-xs transition-colors"
          @click="handleDiscardDebug"
        >✕ Dismiss</button>
      </div>
    </template>

    <!-- Debug error -->
    <div v-if="debugState.error" class="px-4 py-2 bg-red-950 border-b border-red-800 text-xs text-red-200">
      <span class="font-medium text-red-300">Error: </span>
      {{ debugState.error }}
      <button class="ml-2 text-red-400 hover:text-red-300 underline" @click="handleDiscardDebug">Dismiss</button>
    </div>

    <!-- Split: Editor left, Preview right -->
    <div class="flex flex-1 min-h-0">
      <div class="flex-1 min-w-0 border-r border-gray-700">
        <CodeEditor
          :file="getDisplayFile()!"
          :is-dark="props.isDark"
          :read-only="!!props.previewState"
          @change="props.previewState ? undefined : emit('change', $event)"
          @selection-change="handleSelectionChange"
        />
      </div>
      <div class="flex-1 min-w-0 bg-gray-950 overflow-auto">
        <AimdPreview :file="getDisplayFile()!" />
      </div>
    </div>
  </div>
</template>
