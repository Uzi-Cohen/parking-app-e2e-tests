/**
 * Bug #B — Double charge on re-end of an already-ended parking session.
 *
 * Root cause: `end_parking()` in app.py has NO guard against calling it on a
 * session that already has end_time set. Calling POST /end/<id> twice:
 *   1. Overwrites end_time with utcnow()
 *   2. Recalculates fee on the updated duration
 *   3. Calls BillingService.charge() a second time → double charge
 *
 * This test is wrapped in test.fail() so the suite stays green while
 * explicitly documenting the bug. The test asserts that a second /end/<id>
 * call does NOT produce a "Parking ended" confirmation — which currently
 * FAILS because the app re-processes the session and re-charges billing.
 *
 * When the bug is fixed (server rejects the second call with 4xx), remove
 * the test.fail() annotation.
 */

import { test, expect } from '../fixtures/auth';
import { DashboardPage } from '../pages/DashboardPage';
import { randomPlate, uniqueSlot } from '../fixtures/testData';

// test.fail() marks this test as "expected to fail".
// If the bug is ever fixed and the assertion starts passing, Playwright will
// flag it as an unexpected pass — a useful CI signal to remove this annotation.
test.fail(
  true,
  'Expected to fail: Bug #B — double charge on re-end. Demonstrates BillingService receives 2 charge calls.',
);

test(
  'Bug #B: ending an already-ended session should NOT re-charge (currently re-charges)',
  async ({ page }) => {
    const plate = randomPlate();
    const slot = uniqueSlot();

    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // Step 1: Start a parking session
    await dashboard.startParking({ plate, slot });

    // Step 2: Capture the session ID from the "סיים" form action BEFORE ending
    const sessionId = await dashboard.getSessionIdByPlate(plate);
    expect(sessionId).not.toBeNull();

    // Step 3: End parking the normal way via the UI (first end)
    await dashboard.endParkingByPlate(plate);

    // Step 4: Call POST /end/<id> a SECOND time via Playwright's request API.
    //         Playwright follows the server's 302 redirect to "/" and returns
    //         the rendered dashboard HTML as the response body.
    //
    //         If the bug exists, end_parking() is processed again:
    //           - end_time is overwritten
    //           - fee is recalculated
    //           - BillingService.charge() is called a second time
    //           - Flash "Parking ended for <plate>…" is set → visible in HTML
    //
    //         If the bug were fixed, the server would return a 4xx error and
    //         the flash would NOT appear.
    const secondEndResponse = await page.request.post(`/end/${sessionId}`, {
      form: {},
    });
    const responseBody = await secondEndResponse.text();

    // Assert: the second call should NOT produce a "Parking ended" confirmation.
    // Bug: the flash IS present in the body → this assertion FAILS.
    // test.fail() above ensures the failure is treated as the documented bug,
    // keeping CI green while surfacing the double-charge issue.
    expect(responseBody).not.toContain(`Parking ended for ${plate}`);
  },
);
