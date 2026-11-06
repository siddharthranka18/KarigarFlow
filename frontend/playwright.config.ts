import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', workers: 1, fullyParallel: false, timeout: 60000,
  globalSetup: './e2e/wait-for-server.ts',
  use: { baseURL: process.env.E2E_URL || 'http://127.0.0.1:8011', screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  reporter: [['list']],
});
