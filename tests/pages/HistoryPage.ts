import { Page } from '@playwright/test';

export class HistoryPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/history');
  }

  /** Returns a locator for all history rows that contain the given plate. */
  getRowsByPlate(plate: string) {
    return this.page.locator('table tbody tr').filter({ hasText: plate });
  }
}
