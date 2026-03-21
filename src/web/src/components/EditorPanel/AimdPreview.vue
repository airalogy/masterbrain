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
  <div class="h-full overflow-auto p-4">
    <div class="aimd-preview max-w-none" v-html="html" />
  </div>
</template>

<style>
.aimd-preview {
  font-size: 13px;
  line-height: 1.7;
  color: #cdd6f4;
}
.aimd-preview .aimd-h {
  color: #cba6f7;
  font-weight: 700;
  margin: 1em 0 0.4em;
  padding-bottom: 0.2em;
  border-bottom: 1px solid #313244;
}
.aimd-preview .aimd-h1 { font-size: 1.5rem; }
.aimd-preview .aimd-h2 { font-size: 1.25rem; }
.aimd-preview .aimd-h3 { font-size: 1.1rem; }
.aimd-preview .aimd-step {
  display: block;
  margin: 1.2em 0 0.4em;
  padding: 0.3em 0.8em;
  background: #1e3a5f;
  border-left: 3px solid #569cd6;
  border-radius: 0 4px 4px 0;
  font-weight: 600;
  color: #89b4fa;
  font-size: 0.95em;
}
.aimd-preview .aimd-var {
  display: inline-block;
  padding: 1px 6px;
  margin: 0 2px;
  background: #1e4a3a;
  border: 1px solid #4ec9b0;
  border-radius: 4px;
  color: #4ec9b0;
  font-size: 0.85em;
  font-family: 'Consolas', monospace;
  cursor: help;
}
.aimd-preview .aimd-para {
  margin: 0.5em 0;
  color: #cdd6f4;
}
.aimd-preview .aimd-code {
  background: #1e1e2e;
  border: 1px solid #313244;
  border-radius: 6px;
  padding: 0.8em 1em;
  overflow-x: auto;
  margin: 0.8em 0;
  font-family: 'Consolas', monospace;
  font-size: 0.85em;
  color: #a6e3a1;
}
.aimd-preview .aimd-assigner {
  background: #1a1a2e;
  border: 1px solid #6c7086;
  border-radius: 6px;
  padding: 0.8em 1em;
  overflow-x: auto;
  margin: 0.8em 0;
  font-family: 'Consolas', monospace;
  font-size: 0.85em;
  color: #f38ba8;
  position: relative;
}
.aimd-preview .aimd-assigner::before {
  content: 'assigner';
  position: absolute;
  top: 4px;
  right: 8px;
  font-size: 0.7em;
  color: #6c7086;
  font-style: italic;
}
</style>
