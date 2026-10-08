import { defineConfig } from 'vitest/config';

export default defineConfig({
  esbuild: {
    jsx: 'automatic',
    jsxImportSource: 'react',
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./setupTests.js'],
    globals: true,
    include: ['src/**/*.test.{js,jsx}'],
  },
});