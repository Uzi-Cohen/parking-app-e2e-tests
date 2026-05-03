import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/specs',
  retries: 1,
  workers: 1,
  use: {
    baseURL: 'http://localhost:5000',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
  },
  reporter: [['list'], ['html', { open: 'never' }]],
});
