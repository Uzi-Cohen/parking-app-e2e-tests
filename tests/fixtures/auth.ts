import { test as base, expect } from '@playwright/test';

/**
 * Extends the base `test` fixture so that every test using this module
 * receives a `page` that is already authenticated as admin.
 * Uses per-test login (simplest stable option — no storageState complexity).
 */
export const test = base.extend<Record<never, never>>({
  page: async ({ page }, use) => {
    await page.goto('/login');
    await page.locator('#username').fill('admin');
    await page.locator('#password').fill('password');
    await page.getByRole('button', { name: 'כניסה' }).click();
    await page.waitForURL('/');
    await use(page);
  },
});

export { expect } from '@playwright/test';
