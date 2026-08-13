<script setup lang="ts">
import type * as Monaco from 'monaco-editor';
import { markRaw, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue';

const props = withDefaults(defineProps<{
  original: string;
  modified: string;
  language?: string;
  sideBySide?: boolean;
  height?: string | number;
}>(), {
  language: 'plaintext',
  sideBySide: false,
  height: 360,
});

const container = ref<HTMLElement | null>(null);
const monaco = shallowRef<typeof Monaco | null>(null);
const editor = shallowRef<Monaco.editor.IStandaloneDiffEditor | null>(null);
const originalModel = shallowRef<Monaco.editor.ITextModel | null>(null);
const modifiedModel = shallowRef<Monaco.editor.ITextModel | null>(null);

function disposeModels() {
  originalModel.value?.dispose();
  modifiedModel.value?.dispose();
  originalModel.value = null;
  modifiedModel.value = null;
}

function syncModels() {
  if (!monaco.value || !editor.value) return;
  disposeModels();
  originalModel.value = markRaw(monaco.value.editor.createModel(props.original, props.language));
  modifiedModel.value = markRaw(monaco.value.editor.createModel(props.modified, props.language));
  editor.value.setModel({ original: originalModel.value, modified: modifiedModel.value });
}

function syncOptions() {
  editor.value?.updateOptions({ renderSideBySide: props.sideBySide });
}

onMounted(async () => {
  if (!container.value) return;
  monaco.value = await import('monaco-editor');
  editor.value = markRaw(monaco.value.editor.createDiffEditor(container.value, {
    automaticLayout: true,
    enableSplitViewResizing: true,
    minimap: { enabled: false },
    originalEditable: false,
    readOnly: true,
    renderOverviewRuler: false,
    renderSideBySide: props.sideBySide,
    scrollBeyondLastLine: false,
    wordWrap: 'on',
  }));
  syncModels();
});

watch(() => [props.original, props.modified, props.language], syncModels);
watch(() => props.sideBySide, syncOptions);

onBeforeUnmount(() => {
  editor.value?.setModel(null);
  disposeModels();
  editor.value?.dispose();
});
</script>

<template>
  <div
    ref="container"
    class="masterbrain-monaco-diff"
    :style="{ height: typeof props.height === 'number' ? `${props.height}px` : props.height }"
    :data-view-mode="props.sideBySide ? 'side-by-side' : 'inline'"
  />
</template>

<style scoped>
.masterbrain-monaco-diff { width: 100%; min-height: 12rem; overflow: hidden; border: 1px solid var(--masterbrain-border, #e5e7eb); border-radius: .5rem; }
</style>
