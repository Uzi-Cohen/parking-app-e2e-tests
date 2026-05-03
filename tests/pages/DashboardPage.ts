import { Page } from '@playwright/test';

export class DashboardPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');
  }

  async startParking({
    plate,
    vehicleType,
    slot,
  }: {
    plate: string;
    vehicleType?: string;
    slot: string;
  }) {
    await this.page.locator('#car_plate').fill(plate);

    const select = this.page.locator('#vehicle_type_id');
    if (vehicleType) {
      await select.selectOption({ label: vehicleType });
    } else {
      // Pick the first available option
      const firstOption = select.locator('option').first();
      const firstValue = await firstOption.getAttribute('value');
      if (firstValue) await select.selectOption(firstValue);
    }

    await this.page.locator('#slot').fill(slot);
    await this.page.getByRole('button', { name: 'Start Parking' }).click();
    // Wait for redirect back to dashboard after form submit
    await this.page.waitForURL('/');
  }

  /**
   * Returns the numeric session ID extracted from the "End" form action
   * for the row matching the given plate. Returns null if not found.
   */
  async getSessionIdByPlate(plate: string): Promise<number | null> {
    const row = this.page.locator('table tbody tr').filter({ hasText: plate });
    const form = row.locator('form');
    const action = await form.getAttribute('action');
    if (!action) return null;
    const match = action.match(/\/end\/(\d+)/);
    return match ? parseInt(match[1], 10) : null;
  }

  /** Locator for the active-session row(s) matching the given plate. */
  getActiveSessionsByPlate(plate: string) {
    return this.page.locator('table tbody tr').filter({ hasText: plate });
  }

  async endParkingByPlate(plate: string) {
    const row = this.page.locator('table tbody tr').filter({ hasText: plate });
    await row.locator('button.btn-danger').click();
    // Wait for redirect back to dashboard
    await this.page.waitForURL('/');
  }

  async openHistory() {
    await this.page.getByRole('link', { name: 'History' }).click();
    await this.page.waitForURL('/history');
  }
}
