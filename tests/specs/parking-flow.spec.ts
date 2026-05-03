import { test, expect } from '../fixtures/auth';
import { DashboardPage } from '../pages/DashboardPage';
import { HistoryPage } from '../pages/HistoryPage';
import { randomPlate, uniqueSlot } from '../fixtures/testData';

test('happy path: start parking → verify on dashboard → end parking → verify in history with fee', async ({
  page,
}) => {
  const plate = randomPlate();
  const slot = uniqueSlot();

  const dashboard = new DashboardPage(page);
  await dashboard.goto();

  // 1. Start parking
  await dashboard.startParking({ plate, slot });

  // 2. Verify the session appears in the active-sessions table
  const activeRow = dashboard.getActiveSessionsByPlate(plate);
  await expect(activeRow).toBeVisible();
  await expect(activeRow).toContainText(slot);

  // 3. End parking via the "סיים" button
  await dashboard.endParkingByPlate(plate);

  // 4. The plate should no longer be visible in active sessions
  await expect(dashboard.getActiveSessionsByPlate(plate)).toHaveCount(0);

  // 5. Navigate to History
  await dashboard.openHistory();

  const history = new HistoryPage(page);
  const historyRow = history.getRowsByPlate(plate);

  // 6. Verify the session appears in history
  await expect(historyRow).toBeVisible();

  // 7. Verify a fee was calculated (column index 4 = "Fee").
  //    Fee is 0.00 for sub-second sessions; we assert it was set (not '-').
  const feeCell = historyRow.locator('td').nth(4);
  await expect(feeCell).not.toHaveText('-');
});
