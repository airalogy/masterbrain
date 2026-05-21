<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, shallowRef } from 'vue';
import * as monaco from 'monaco-editor';
import { aimdTokenColors, completionItemProvider, conf, language } from '@airalogy/aimd-editor/monaco';
import type { EditorSelection, FileEntry } from '../../types/index.ts';

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

function getAimdThemeRules(): monaco.editor.ITokenThemeRule[] {
  return aimdTokenColors.flatMap((tokenColor) => {
    const scopes = Array.isArray(tokenColor.scope) ? tokenColor.scope : [tokenColor.scope];
    return scopes.map((scope) => ({
      token: scope,
      foreground: tokenColor.settings.foreground?.replace('#', ''),
      fontStyle: tokenColor.settings.fontStyle,
    }));
  });
}

function registerAimd() {
  if (registered) return;
  registered = true;

  monaco.languages.register({ id: 'aimd' });
  monaco.languages.setMonarchTokensProvider('aimd', language as monaco.languages.IMonarchLanguage);
  monaco.languages.setLanguageConfiguration('aimd', conf as monaco.languages.LanguageConfiguration);
  monaco.languages.registerCompletionItemProvider(
    'aimd',
    completionItemProvider as monaco.languages.CompletionItemProvider,
  );

  monaco.editor.defineTheme('masterbrain-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: getAimdThemeRules(),
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
    rules: getAimdThemeRules(),
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
  if (props.file.type === 'aimd') return 'aimd';
  if (props.file.type === 'py') return 'python';
  return 'plaintext';
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
