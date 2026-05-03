# Pango QA — Playwright E2E Test Suite

## Prerequisites

- Node 20+
- Docker container running the app on `http://localhost:5000`
  (credentials: `admin` / `password`)

To start the app if it's not running:

```bash
docker pull --platform linux/amd64 doringber/parking-manager:3.1.0
docker run --platform linux/amd64 -d -p 5000:5000 \
  --name parking-manager doringber/parking-manager:3.1.0
```

## Setup (first time)

```bash
# from the repository root
npm install
npx playwright install chromium
```

## Running tests

```bash
# Headless (CI mode)
npm test

# Headed (watch the browser)
npm run test:headed

# Single spec
npx playwright test tests/specs/parking-flow.spec.ts
```

## Test structure

```
tests/
  pages/
    LoginPage.ts       — POM: goto, login, assertOnDashboard
    DashboardPage.ts   — POM: startParking, endParkingByPlate, getActiveSessionsByPlate, openHistory
    HistoryPage.ts     — POM: getRowsByPlate
  fixtures/
    auth.ts            — Extends base test with pre-authenticated page (per-test login)
    testData.ts        — randomPlate(), uniqueSlot() — isolated test data generators
  specs/
    parking-flow.spec.ts    — Happy-path: start → dashboard check → end → history check
    bug-double-end.spec.ts  — Bug #B demo: double /end call double-charges billing (test.fail)
```

## Expected results

| Test | Expected outcome |
|---|---|
| `parking-flow.spec.ts` | ✅ PASS |
| `bug-double-end.spec.ts` | ✅ PASS (via `test.fail()` — bug confirmed) |

The `bug-double-end` test uses `test.fail()` to document **Bug #B**:  
calling `POST /end/<id>` on an already-ended session re-runs billing without
any guard, resulting in a double charge. When the bug is fixed, remove `test.fail()`.
