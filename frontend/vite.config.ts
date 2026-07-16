import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    target: 'esnext',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        quick: resolve(__dirname, 'quick.html'),
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
});
