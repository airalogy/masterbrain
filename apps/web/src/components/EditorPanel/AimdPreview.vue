<script setup lang="ts">
import { ref, watch } from 'vue';
import { renderToHtml } from '@airalogy/aimd-renderer';
import type { FileEntry } from '../../types/index.ts';

const props = defineProps<{
  file: FileEntry;
}>();

const html = ref('');
const error = ref<string | null>(null);
const isRendering = ref(false);
let renderSequence = 0;

function escapeHtml(source: string): string {
  return source
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderCodePreview(source: string) {
  html.value = `<pre class="aimd-preview__code"><code>${escapeHtml(source)}</code></pre>`;
}

async function updatePreview(file: FileEntry) {
  const currentSequence = ++renderSequence;
  error.value = null;

  if (file.type !== 'aimd') {
    isRendering.value = false;
    renderCodePreview(file.content);
    return;
  }

  isRendering.value = true;

  try {
    const result = await renderToHtml(file.content, {
      assignerVisibility: 'collapsed',
      groupStepBodies: true,
      groupCheckBodies: true,
    });
    if (currentSequence !== renderSequence) return;
    html.value = result.html;
  } catch (cause: unknown) {
    if (currentSequence !== renderSequence) return;
    error.value = cause instanceof Error ? cause.message : 'AIMD preview failed';
    html.value = '';
  } finally {
    if (currentSequence === renderSequence) {
      isRendering.value = false;
    }
  }
}

watch(
  () => [props.file.path, props.file.type, props.file.content],
  () => {
    void updatePreview(props.file);
  },
  { immediate: true },
);
</script>

<template>
  <div class="preview-shell">
    <div class="preview-shell__inner">
      <div v-if="isRendering" class="preview-shell__status">Rendering AIMD…</div>
      <div v-else-if="error" class="preview-shell__status preview-shell__status--error">{{ error }}</div>
      <div class="aimd-preview" v-html="html" />
    </div>
  </div>
</template>

<style scoped>
.preview-shell {
  height: 100%;
  overflow: auto;
  padding: 20px;
  background: var(--preview-bg);
}

.preview-shell__inner {
  max-width: 920px;
  margin: 0 auto;
  padding: 24px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--panel-solid);
  box-shadow: var(--shadow-md);
}

.preview-shell__status {
  margin-bottom: 16px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--panel-subtle);
  color: var(--text-muted);
  font-size: 0.9rem;
}

.preview-shell__status--error {
  border-color: color-mix(in srgb, var(--danger) 28%, transparent);
  background: color-mix(in srgb, var(--danger) 10%, var(--panel-subtle));
  color: var(--danger);
}

.aimd-preview {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
}

.aimd-preview :deep(h1),
.aimd-preview :deep(h2),
.aimd-preview :deep(h3),
.aimd-preview :deep(h4),
.aimd-preview :deep(h5),
.aimd-preview :deep(h6) {
  color: var(--text-primary);
  margin: 1.25em 0 0.45em;
  line-height: 1.25;
}

.aimd-preview :deep(h1) {
  font-size: 1.85rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.35rem;
}

.aimd-preview :deep(h2) {
  font-size: 1.45rem;
}

.aimd-preview :deep(h3) {
  font-size: 1.15rem;
}

.aimd-preview :deep(p),
.aimd-preview :deep(ul),
.aimd-preview :deep(ol),
.aimd-preview :deep(blockquote),
.aimd-preview :deep(table),
.aimd-preview :deep(.aimd-field),
.aimd-preview :deep(.aimd-ref),
.aimd-preview :deep(.aimd-figure),
.aimd-preview :deep(.aimd-assigner-preview) {
  margin: 0.85em 0;
}

.aimd-preview :deep(ul),
.aimd-preview :deep(ol) {
  padding-left: 1.35rem;
}

.aimd-preview :deep(blockquote) {
  margin-left: 0;
  padding: 0.85rem 1rem;
  border-left: 3px solid var(--accent);
  border-radius: 0 12px 12px 0;
  background: var(--panel-subtle);
  color: var(--text-secondary);
}

.aimd-preview :deep(a) {
  color: var(--accent);
  text-decoration: none;
}

.aimd-preview :deep(a:hover) {
  text-decoration: underline;
}

.aimd-preview :deep(pre) {
  margin: 0.95em 0;
  padding: 1rem 1.1rem;
  border: 1px solid var(--code-border);
  border-radius: 14px;
  background: var(--code-bg);
  overflow-x: auto;
}

.aimd-preview :deep(pre code),
.aimd-preview :deep(code) {
  font-family: "IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace;
}

.aimd-preview :deep(:not(pre) > code) {
  padding: 0.12rem 0.4rem;
  border: 1px solid var(--border-color);
  border-radius: 0.45rem;
  background: var(--panel-subtle);
}

.aimd-preview :deep(table) {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
  border-radius: 12px;
}

.aimd-preview :deep(th),
.aimd-preview :deep(td) {
  padding: 0.65rem 0.8rem;
  border: 1px solid var(--border-color);
  text-align: left;
}

.aimd-preview :deep(th) {
  background: var(--panel-subtle);
  color: var(--text-primary);
}

.aimd-preview :deep(img.aimd-image),
.aimd-preview :deep(.aimd-figure__image) {
  max-width: 100%;
  border-radius: 14px;
}

.aimd-preview :deep(.aimd-step-body),
.aimd-preview :deep(.aimd-check-body) {
  margin-top: 0.85rem;
  padding-left: 1rem;
  border-left: 2px solid var(--border-color);
}

.aimd-preview :deep(.aimd-assigner-preview) {
  border: 1px solid var(--code-border);
  border-radius: 14px;
  background: var(--code-bg);
}

.aimd-preview :deep(.aimd-assigner-preview summary) {
  cursor: pointer;
  padding: 0.8rem 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.aimd-preview :deep(.aimd-assigner-code) {
  display: block;
}

.aimd-preview :deep(.aimd-preview__code) {
  margin: 0;
}
</style>
