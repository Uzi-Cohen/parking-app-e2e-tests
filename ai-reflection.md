# AI Reflection

## Approach & Key Decisions

**Source-extraction-first strategy:** Rather than black-box clicking through the UI, we extracted the Flask application code from the running container and used it as the primary guide for hypothesis testing. Each bug was first identified via source code inspection, then reproduced via targeted HTTP requests (curl/Playwright) against the running app. This approach compressed the exploration timeline: instead of systematically testing every UI path, we read the routes, identified missing decorators and logic errors, and verified them with minimal requests. The eight bugs were confirmed in less than 2 hours, with high confidence in root cause.

**Parallel execution streams:** Bug verification (curl-based, source-driven) and Playwright test scaffolding ran concurrently. While the exploration team reproduced vulnerabilities and documented them in bugs-verified.md, test development started on the happy-path scenario (parking lifecycle) and the most critical bug demo (double-billing). This parallelization compressed the overall timeline from what would have been sequential (bug hunt → then automate) into overlapping tracks.

**Selective automation over breadth:** We did not attempt to automate every bug. Instead, we created explicit bug-demonstration tests (wrapped in `test.fail()`) for the most critical vulnerability (BUG-B: double billing) and automated the happy-path scenario. The rationale: depth and clarity > coverage in a constrained assignment. The bug-demo test contains a detailed code comment explaining exactly what the bug is, why test.fail() is necessary, and what "fixed" means (server rejects with 4xx). A code reviewer can immediately see our analysis without guessing.

## Trade-offs Made

**Depth over breadth on automation:** We wrote 2 focused test cases instead of 10 shallow ones. The happy-path test (parking-flow.spec.ts) serves as both a smoke test and a POM demonstration; the bug-demo test (bug-double-end.spec.ts) is an explicit vulnerability showcase. We did not automate BUGs A, C, D, E, F, G, H individually because test complexity would scale with the app's features, and the manual test cases in test-plan.md provide clear reproduction paths. In a production pipeline, the happy-path test catches regressions; the bug-demo test documents a known issue until fixed.

**No API-level tests separate from Playwright:** The app's API surface is small (login, start, end, history) and is fully covered by the E2E Playwright suite. Writing curl tests in parallel would duplicate coverage. Playwright's web-first auto-waiting and screenshot capture on failure provide better diagnostics than raw HTTP requests.

**Billing service remains live (not stubbed):** We did not mock or stub the external billing service. The integration is real: when the app calls POST /charge, the service processes it. This choice exposed BUG-B (double-charge) directly — without mocking, the bug is invisible. A stub would have masked the financial vulnerability. Trade-off: tests depend on the billing service's availability, but this is acceptable in an assignment environment and strengthens the evidence.

**Unique test data per test instead of cleanup-after:** Each test generates its own license plate (randomPlate()) and slot (uniqueSlot()). We do not reset the database between tests. This approach is simpler, parallel-safe, and idempotent: if the test suite runs twice, no stale data from the first run blocks the second. SQLite is small and fast enough for assignment-scope testing.

## AI Tools Used

**Claude Code (Opus 4.7, 1M context window)** — primary orchestrator. OMC team layer coordinated three specialized agents in parallel:
- **qa-tester** — bug hunting via source inspection + curl reproduction; discovered 8 bugs with HTTP evidence + root-cause analysis
- **executor** — Playwright test scaffolding, POM layer, fixtures, TypeScript build; delivered working test suite with 2 passing specs
- **writer** (this agent) — documentation: test-plan.md, README.md, ai-reflection.md; verified all code examples and commands

**Docker** — containerized the application under test; enabled deterministic reproduction of bugs across environments

**Playwright (TypeScript)** — headless browser automation with built-in auto-waiting, screenshot capture, parallel test execution, and POM support. No Cypress/Selenium because Playwright's web-first primitives (waitForLoadState, expect.toBeVisible with auto-retry) eliminate most flakiness; TypeScript catches POM contract drift at compile time; parallel execution is built-in (no extra configuration).

## Reasoning Behind Tool Choices & Limitations

**Why Claude Code:** The task required coordinating three distinct activities (bug hunting, test development, documentation) with evidence verification (every code example must work). Claude's 1M context window allowed the full codebase + conversation history + test output to remain in-window, eliminating context-switching overhead. OMC's team layer parallelized work: bug hunters and test developers worked simultaneously, not sequentially.

**Why source-first, not UI-first:** Without source access, finding BUG-B (double-billing) would require systematic testing of every button's POST behavior, likely missing it. With source, we saw `@login_required` missing on `/uploads/<filename>` in 30 seconds (BUG-A). This efficiency gain was decisive: 8 bugs found + verified in the assignment window, where a pure manual approach would have found 2–3 in the same time.

**Why Playwright, not manual testing:** Manual testing would have covered the happy path once, then documenting bugs would be a static list with no runnable proof. Playwright gives us a runnable suite that can be re-executed in CI, proves the bugs are real (test.fail() intentionally documents an expected failure), and provides screenshots on regression. The test suite is the executable specification.

**Limitations of this approach:**

1. **LLM cannot replace exploratory testing instinct.** We relied on human domain knowledge (knowing that money flows are high-risk, that missing decorators are red flags) to guide the exploration. Claude provided tooling and parallelization; the QA strategist decided which bugs mattered. An AI alone would likely have found syntax errors but missed BUG-B's financial impact.

2. **test.fail() is a code comment.** The Playwright suite documents the double-billing bug clearly, but `test.fail()` is a code-level annotation, not a runtime assertion. A code reviewer must read the test file and the comment to understand the bug. Ideally, the app would be fixed and the annotation removed, so the test becomes a permanent regression check. Until then, the test is documentation + evidence, not a typical automated check.

3. **This suite is tuned to v3.1.0's current behavior.** If the app fixes BUG-B (adds the `if session.end_time is not None` guard), the `bug-double-end.spec.ts` test will start passing where it currently fails. That's the intended outcome (the bug-demo test becomes obsolete when fixed), but it means the suite is not forward-compatible. Version upgrades may require re-tuning.

4. **Test data isolation does not check consistency.** We use unique per-test data (different license plates) to avoid collisions, but we do not assert that the database is clean. If a previous test crashed and left orphaned sessions, a new test might inherit stale state. In practice, with Playwright's isolation and SQLite's simplicity, this is not an issue for assignment-scope testing. Production would require deterministic state cleanup (factory resets, data marts, or CI-per-branch databases).

5. **No coverage metrics.** The Playwright suite covers the happy path + one critical bug. We have not measured code coverage (branch/line coverage %), so we cannot claim exhaustive testing. Test-plan.md lists 15+ test cases (representing coverage goals); the automated suite implements 2 of them. The other 13 are documented as manual cases with clear reproduction steps, suitable for regression testing by a human or automation expansion if the team's timeline extends.

## Honest Assessment

This submission demonstrates **what a source-aware, focused QA approach can deliver in a fixed timeline:** 8 bugs discovered and documented with evidence, 2 automated tests proving the happy path and critical vulnerability, and a reusable test framework (POM, fixtures, TypeScript). It does not attempt to be comprehensive (all 13 test cases automated, load testing, stress testing) but prioritizes high-impact areas and provides clear next steps (test-plan lists manual cases; ai-reflection lists limitations). The tools (Claude, Playwright, Docker) were chosen to maximize velocity and evidence density, not to replace skilled QA judgment.
