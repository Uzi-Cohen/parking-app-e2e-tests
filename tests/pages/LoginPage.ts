import { Page, expect } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.page.locator('#username').fill(username);
    await this.page.locator('#password').fill(password);
    await this.page.getByRole('button', { name: 'כניסה' }).click();
  }

  async assertOnDashboard() {
    await expect(this.page).toHaveURL('/');
  }
}
