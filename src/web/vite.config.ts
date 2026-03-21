import { defineConfig, type PluginOption } from 'vite';
import vue from '@vitejs/plugin-vue';
import monacoEditorPlugin from 'vite-plugin-monaco-editor';

const monacoEditor = monacoEditorPlugin as unknown as {
  default: (options: { languageWorkers: string[] }) => PluginOption;
};

export default defineConfig({
  plugins: [
    vue(),
    monacoEditor.default({
      languageWorkers: ['editorWorkerService', 'typescript'],
    }),
  ],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8080',
    },
  },
});
