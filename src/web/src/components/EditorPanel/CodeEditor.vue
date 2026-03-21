<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, shallowRef } from 'vue';
import * as monaco from 'monaco-editor';
import type { FileEntry } from '../../types/index.ts';

export interface EditorSelection {
  text: string;
  startOffset: number;
  endOffset: number;
}

const props = defineProps<{
  file: FileEntry;
  isDark: boolean;
  readOnly?: boolean;
}>();

const emit = defineEmits<{
  change: [content: string];
  selectionChange: [selection: EditorSelection | null];
}>();

const containerRef = ref<HTMLDivElement | null>(null);
const editorInstance = shallowRef<monaco.editor.IStandaloneCodeEditor | null>(null);
let suppressChange = false;
let registered = false;

function registerAimd() {
  if (registered) return;
  registered = true;

  monaco.languages.register({ id: 'aimd' });
  monaco.languages.setMonarchTokensProvider('aimd', {
    tokenizer: {
      root: [
        [/\{\{step\|[^}]+\}\}/, 'aimd-step'],
        [/\{\{var\|/, { token: 'aimd-var-open', next: '@varBlock' }],
        [/^```assigner$/, { token: 'aimd-assigner-fence', next: '@assignerBlock' }],
        [/^```\w*$/, { token: 'aimd-fence', next: '@codeBlock' }],
        [/^#{1,6}\s+.*$/, 'aimd-heading'],
        [/\*\*[^*]+\*\*/, 'aimd-bold'],
        [/\*[^*]+\*/, 'aimd-italic'],
      ],
      varBlock: [
        [/\}\}/, { token: 'aimd-var-close', next: '@pop' }],
        [/[^}]+/, 'aimd-var'],
      ],
      assignerBlock: [
        [/^```$/, { token: 'aimd-assigner-fence', next: '@pop' }],
        [/.*/, 'aimd-assigner-code'],
      ],
      codeBlock: [
        [/^```$/, { token: 'aimd-fence', next: '@pop' }],
        [/.*/, 'string'],
      ],
    },
  });

  monaco.editor.defineTheme('masterbrain-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'aimd-step', foreground: '569cd6', fontStyle: 'bold' },
      { token: 'aimd-var-open', foreground: '4ec9b0' },
      { token: 'aimd-var', foreground: '4ec9b0' },
      { token: 'aimd-var-close', foreground: '4ec9b0' },
      { token: 'aimd-heading', foreground: 'dcdcaa', fontStyle: 'bold' },
      { token: 'aimd-bold', fontStyle: 'bold' },
      { token: 'aimd-italic', fontStyle: 'italic' },
      { token: 'aimd-assigner-fence', foreground: '808080' },
      { token: 'aimd-assigner-code', foreground: 'ce9178' },
      { token: 'aimd-fence', foreground: '808080' },
    ],
    colors: {
      'editor.background': '#0b1220',
      'editor.lineHighlightBackground': '#132036',
      'editorGutter.background': '#0b1220',
      'editorIndentGuide.background1': '#1f2e48',
      'editorIndentGuide.activeBackground1': '#3b82f6',
      'editor.selectionBackground': '#1d4ed840',
      'editor.inactiveSelectionBackground': '#1d4ed820',
      'editorCursor.foreground': '#93c5fd',
      'editorLineNumber.foreground': '#5b6b85',
      'editorLineNumber.activeForeground': '#cbd5e1',
    },
  });

  monaco.editor.defineTheme('masterbrain-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'aimd-step', foreground: '1d4ed8', fontStyle: 'bold' },
      { token: 'aimd-var-open', foreground: '065f46' },
      { token: 'aimd-var', foreground: '065f46' },
      { token: 'aimd-var-close', foreground: '065f46' },
      { token: 'aimd-heading', foreground: '7c3aed', fontStyle: 'bold' },
      { token: 'aimd-bold', fontStyle: 'bold' },
      { token: 'aimd-italic', fontStyle: 'italic' },
      { token: 'aimd-assigner-fence', foreground: '6b7280' },
      { token: 'aimd-assigner-code', foreground: '92400e' },
      { token: 'aimd-fence', foreground: '6b7280' },
    ],
    colors: {
      'editor.background': '#fbfdff',
      'editor.lineHighlightBackground': '#eef4ff',
      'editorGutter.background': '#fbfdff',
      'editorIndentGuide.background1': '#dbe5f1',
      'editorIndentGuide.activeBackground1': '#60a5fa',
      'editor.selectionBackground': '#bfdbfe',
      'editor.inactiveSelectionBackground': '#dbeafe',
      'editorCursor.foreground': '#2563eb',
      'editorLineNumber.foreground': '#94a3b8',
      'editorLineNumber.activeForeground': '#0f172a',
    },
  });
}

function getLanguage() {
  return props.file.type === 'aimd' ? 'aimd' : 'python';
}

function getTheme() {
  return props.isDark ? 'masterbrain-dark' : 'masterbrain-light';
}

onMounted(() => {
  if (!containerRef.value) return;
  registerAimd();

  const editor = monaco.editor.create(containerRef.value, {
    value: props.file.content,
    language: getLanguage(),
    theme: getTheme(),
    fontSize: 14,
    fontFamily: '"IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace',
    lineHeight: 22,
    minimap: { enabled: false },
    wordWrap: 'on',
    scrollBeyondLastLine: false,
    lineNumbers: 'on',
    renderWhitespace: 'none',
    automaticLayout: true,
    readOnly: props.readOnly ?? false,
    smoothScrolling: true,
    cursorSmoothCaretAnimation: 'on',
    roundedSelection: true,
    padding: { top: 18, bottom: 18 },
    lineNumbersMinChars: 3,
    glyphMargin: false,
    overviewRulerBorder: false,
    renderLineHighlight: 'all',
    bracketPairColorization: { enabled: true },
    guides: {
      indentation: true,
      bracketPairs: true,
    },
    fixedOverflowWidgets: true,
  });

  editorInstance.value = editor;

  editor.onDidChangeModelContent(() => {
    if (suppressChange) return;
    emit('change', editor.getValue());
  });

  editor.onDidChangeCursorSelection(() => {
    const sel = editor.getSelection();
    const model = editor.getModel();
    if (!sel || !model || sel.isEmpty()) {
      emit('selectionChange', null);
      return;
    }
    const text = model.getValueInRange(sel);
    if (!text.trim()) {
      emit('selectionChange', null);
      return;
    }
    const startOffset = model.getOffsetAt(sel.getStartPosition());
    const endOffset = model.getOffsetAt(sel.getEndPosition());
    emit('selectionChange', { text, startOffset, endOffset });
  });
});

// Sync content from parent
watch(() => props.file.content, (newContent) => {
  const editor = editorInstance.value;
  if (!editor) return;
  if (editor.getValue() !== newContent) {
    suppressChange = true;
    editor.setValue(newContent);
    suppressChange = false;
  }
});

// Sync language and theme
watch([() => props.file.type, () => props.isDark], () => {
  const editor = editorInstance.value;
  if (!editor) return;
  const model = editor.getModel();
  if (model) monaco.editor.setModelLanguage(model, getLanguage());
  monaco.editor.setTheme(getTheme());
});

// Sync readOnly
watch(() => props.readOnly, (val) => {
  editorInstance.value?.updateOptions({ readOnly: val ?? false });
});

onBeforeUnmount(() => {
  editorInstance.value?.dispose();
  editorInstance.value = null;
});
</script>

<template>
  <div ref="containerRef" class="h-full w-full" />
</template>
