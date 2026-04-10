import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig, type PluginOption } from 'vite';
import vue from '@vitejs/plugin-vue';
import monacoEditorPlugin from 'vite-plugin-monaco-editor';

const monacoEditor = monacoEditorPlugin as unknown as {
  default: (options: { languageWorkers: string[] }) => PluginOption;
};

const webRoot = fileURLToPath(new URL('.', import.meta.url));
const aimdRoot = path.resolve(webRoot, '../../../aimd');
const aimdPackagesRoot = path.join(aimdRoot, 'packages');

export default defineConfig({
  resolve: {
    alias: [
      {
        find: /^@airalogy\/aimd-editor\/monaco$/,
        replacement: path.join(aimdPackagesRoot, 'aimd-editor/dist/monaco.js'),
      },
      {
        find: /^@airalogy\/aimd-renderer$/,
        replacement: path.join(aimdPackagesRoot, 'aimd-renderer/dist/index.js'),
      },
      {
        find: /^@airalogy\/aimd-renderer\/styles$/,
        replacement: path.join(aimdPackagesRoot, 'aimd-renderer/src/styles/katex.css'),
      },
      {
        find: /^@airalogy\/aimd-recorder\/styles$/,
        replacement: path.join(aimdPackagesRoot, 'aimd-recorder/src/styles/aimd.css'),
      },
    ],
  },
  plugins: [
    vue(),
    monacoEditor.default({
      languageWorkers: ['editorWorkerService', 'typescript'],
    }),
  ],
  server: {
    fs: {
      allow: [aimdRoot],
    },
    proxy: {
      '/api': 'http://127.0.0.1:8080',
    },
  },
});
