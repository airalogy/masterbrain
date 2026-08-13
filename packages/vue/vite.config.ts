import { resolve } from 'node:path';
import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [vue()],
  build: {
    lib: {
      entry: {
        index: resolve(__dirname, 'src/index.ts'),
        monaco: resolve(__dirname, 'src/monaco.ts'),
      },
      formats: ['es'],
    },
    rollupOptions: {
      external: ['vue', 'monaco-editor', '@airalogy/masterbrain-client'],
      output: {
        entryFileNames: '[name].js',
        assetFileNames: asset => asset.name === 'style.css' ? 'masterbrain-vue.css' : '[name][extname]',
      },
    },
  },
});
