<script setup lang="ts">
import { computed } from 'vue';
import { parseAimd } from '../../utils/aimdParser.ts';
import type { FileEntry } from '../../types/index.ts';

const props = defineProps<{
  file: FileEntry;
}>();

const html = computed(() => {
  if (props.file.type === 'aimd') return parseAimd(props.file.content);
  return `<pre class="aimd-code"><code>${props.file.content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`;
});
</script>

<template>
  <div class="preview-shell">
    <div class="preview-shell__inner">
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

.aimd-preview {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
}
.aimd-preview .aimd-h {
  color: var(--text-primary);
  font-weight: 700;
  margin: 1em 0 0.4em;
  padding-bottom: 0.2em;
  border-bottom: 1px solid var(--border-color);
}
.aimd-preview .aimd-h1 { font-size: 1.5rem; }
.aimd-preview .aimd-h2 { font-size: 1.25rem; }
.aimd-preview .aimd-h3 { font-size: 1.1rem; }
.aimd-preview .aimd-step {
  display: block;
  margin: 1.2em 0 0.4em;
  padding: 0.45em 0.95em;
  background: var(--accent-soft);
  border-left: 3px solid var(--accent);
  border-radius: 0 10px 10px 0;
  font-weight: 600;
  color: var(--accent);
  font-size: 0.95em;
}
.aimd-preview .aimd-var {
  display: inline-block;
  padding: 1px 6px;
  margin: 0 2px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  border-radius: 4px;
  color: #059669;
  font-size: 0.85em;
  font-family: "IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace;
  cursor: help;
}
.aimd-preview .aimd-para {
  margin: 0.5em 0;
  color: var(--text-secondary);
}
.aimd-preview .aimd-code {
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: 14px;
  padding: 0.95em 1.05em;
  overflow-x: auto;
  margin: 0.8em 0;
  font-family: "IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  color: var(--text-secondary);
}
.aimd-preview .aimd-assigner {
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: 14px;
  padding: 0.95em 1.05em;
  overflow-x: auto;
  margin: 0.8em 0;
  font-family: "IBM Plex Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  color: var(--text-secondary);
  position: relative;
}
.aimd-preview .aimd-assigner::before {
  content: 'assigner';
  position: absolute;
  top: 4px;
  right: 8px;
  font-size: 0.7em;
  color: var(--text-muted);
  font-style: italic;
}
</style>
