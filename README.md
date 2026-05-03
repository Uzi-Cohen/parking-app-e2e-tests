# Pango Parking Manager — QA Automation Submission

Comprehensive QA assessment of the Pango parking management system (v3.1.0). Includes 8 verified bugs, Playwright E2E test suite, test plan, and approach documentation.

## Repository Layout

```
.
├── README.md                    # This file
├── test-plan.md                 # Detailed test plan & bug evidence
├── ai-reflection.md             # Approach & tool rationale
├── package.json                 # Node dependencies (Playwright, TypeScript)
├── playwright.config.ts         # Playwright configuration
├── tsconfig.json                # TypeScript configuration
├── tests/
│   ├── specs/
│   │   ├── parking-flow.spec.ts      # Happy-path: start → end → history
│   │   └── bug-double-end.spec.ts    # Bug #B demo: double-billing (test.fail)
│   ├── pages/
│   │   ├── LoginPage.ts              # POM: login, authentication
│   │   ├── DashboardPage.ts          # POM: start/end parking, active sessions
│   │   └── HistoryPage.ts            # POM: access history, verify closed sessions
│   └── fixtures/
│       ├── auth.ts                   # Extended test with pre-auth fixture
│       └── testData.ts               # Data generators: randomPlate(), uniqueSlot()
└── exploration/
    └── bugs-verified.md              # 8 confirmed bugs with HTTP reproduction
```

## Prerequisites

- **Docker Desktop** — to run the application container
- **Node 20+** — for Playwright and TypeScript
- **~5 minutes** — to start container, install dependencies, and run tests

Verify installations:
```bash
docker --version    # Docker 20+
node --version      # v20+
npm --version       # v10+
```

## Run the App Under Test

The Pango application runs in Docker. Start it before running tests.

```bash
# Pull and run the container (admin / password)
docker pull --platform linux/amd64 doringber/parking-manager:3.1.0
docker run --platform linux/amd64 -d -p 5000:5000 \
  --name parking-manager doringber/parking-manager:3.1.0
```

Verify the app is running:
```bash
curl http://localhost:5000/login -I
# Expected: HTTP 200 (login page)
```

Default credentials: **admin / password**

To stop the container:
```bash
docker stop parking-manager && docker rm parking-manager
```

## Run the Tests

### First time setup

```bash
# from the repository root
npm install

# Install Playwright browser (Chromium)
npx playwright install chromium
```

### Execute tests

```bash
# Headless mode (CI/automated)
npm test

# Headed mode (watch in browser)
npm run test:headed

# Single test file
npx playwright test tests/specs/parking-flow.spec.ts
```

### Expected results

| Test | Status | Notes |
|---|---|---|
| `parking-flow.spec.ts` | ✅ PASS | Happy path: start → verify active → end → verify history |
| `bug-double-end.spec.ts` | ✅ PASS (via `test.fail`) | Demonstrates BUG-B: double charge. Wrapped in `test.fail()` so suite stays green while documenting the bug. |

Test output includes:
- Execution time per test
- Screenshots/videos on failure (stored in `test-results/`)
- Detailed assertion messages

## What's Included

**QA Artifacts:**
- **test-plan.md** — Risk-based test strategy, test cases organized by area (AUTH, PARK, AUTHZ, UPLOAD, VALIDATE), bug summary table with reproduction steps and impact analysis
- **ai-reflection.md** — Approach documentation: source-extraction-first strategy, parallel execution model, tool rationale, and honest limitations
- **exploration/bugs-verified.md** — 8 bugs with HTTP reproduction, root-cause code snippets, impact, and suggested fixes

**Automated Tests:**
- **tests/specs/parking-flow.spec.ts** — End-to-end happy-path scenario
- **tests/specs/bug-double-end.spec.ts** — Explicit bug demonstration (test.fail() marks expected failure)
- **POM layer** — LoginPage, DashboardPage, HistoryPage (stable selectors, reusable)
- **Fixtures** — Pre-authenticated test context, isolated test data generators

## Key Findings

**Critical bugs (2):**
- BUG-A: Uploaded files accessible without authentication (public disclosure)
- BUG-B: Double-billing on re-ending closed parking sessions

**High-severity bugs (4):**
- BUG-C: Non-admin users can create/delete accounts
- BUG-D: Vehicle type & slot admin routes return HTTP 500 (missing templates)
- BUG-E: Slot reservation race condition — leaked Redis keys block legitimate parking
- BUG-F: Hardcoded SECRET_KEY ('change-me') — session forgery possible offline

**Medium-severity bugs (2):**
- BUG-G: Logout via GET request (CSRF vulnerability)
- BUG-H: License plate validation too strict (rejects valid Israeli formats)

All bugs documented with reproduction steps in `test-plan.md` and `exploration/bugs-verified.md`.

## Author Note

This submission demonstrates a **source-aware, risk-driven QA approach** with concrete evidence:
- Bugs verified via HTTP reproduction AND source code root-cause analysis
- Tests automated for the highest-value scenario (happy path + critical bug demo)
- Documentation traces from requirements through implementation to verification

**On clean state:** Tests use isolated per-test data (random plates, unique slots) and require no manual cleanup. The test suite is idempotent and parallel-safe. Database is SQLite with no reset-between-tests; each test operates on independent data.

**On credentials:** Admin account (admin / password) is seeded by the container. No credential rotation required for testing; this is a development/assignment environment.
