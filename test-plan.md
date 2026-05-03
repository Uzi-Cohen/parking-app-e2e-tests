# Test Plan — Parking Manager

## Application Under Test

Pango Parking Manager (v3.1.0, doringber/parking-manager:3.1.0) is a Flask-based web application for managing vehicle parking sessions and billing. Users authenticate with credentials, start/end parking sessions by license plate and slot assignment, and review billing history. The application integrates with external billing and slot services. We accessed the live container at http://localhost:5000 with credentials admin/password and had access to the extracted Flask source code (app.py, forms.py, models.py, billing_service.py).

## Approach & Prioritization

**Risk-based focus:** We prioritized money flows (parking start/end → billing), authorization boundaries (who can access what), and data integrity (duplicate prevention, state consistency) over presentation and cosmetic features. Authentication vulnerabilities and financial transaction integrity are the highest-impact areas for a parking system.

**Time-boxed exploration:** We conducted source-guided HTTP-based exploration rather than brute-force clicking. Access to extracted Flask source allowed us to identify vulnerable routes quickly and verify root causes via code inspection.

**Parallel tracks:** Bug verification and Playwright test scaffolding ran concurrently. We automated the highest-value scenario (happy-path parking lifecycle) and created an explicit bug-demonstration test (test.fail()) for the most critical financial vulnerability (double-billing).

## What We Chose To Test (and Why)

**In scope:**
- **Authentication & authorization** — login, logout, per-route access control, session management
- **Parking lifecycle** — start session, end session, duplicate prevention, active/historical tracking
- **Billing integration** — fee calculation, charge API calls, transaction accuracy
- **User management** — account creation, deletion, admin vs. non-admin boundaries
- **File upload security** — access controls on uploaded vehicle images
- **Input validation** — license plate format, slot name validation, CSRF protection
- **Concurrency** — race conditions in slot reservation and duplicate-plate detection

**Out of scope:**
- Load testing, stress testing, connection pooling limits
- Browser compatibility matrix or mobile responsiveness
- Accessibility deep-dive (WCAG compliance)
- RTL/LTR rendering pixel-perfect alignment (Hebrew UI rendering is correct but not exhaustively tested)
- Historical data purging or long-term storage performance
- Billing service mock behavior (we tested against the live service as deployed)

## Risk Matrix

| Area | Severity | Evidence | Status |
|------|----------|----------|--------|
| Public file disclosure — uploads route missing @login_required | CRITICAL | HTTP 200 + file returned without auth cookie; source confirms no decorator | CONFIRMED (BUG-A) |
| Double-billing on re-end — no guard against re-ending closed session | CRITICAL | Two separate POST /end calls trigger two POST /charge events; fee differs on each call | CONFIRMED (BUG-B) |
| Arbitrary user creation — non-admin can invoke /users/add | HIGH | Regular user successfully created new account; source shows @login_required only | CONFIRMED (BUG-C) |
| Vehicle type & slot routes unavailable — missing templates | HIGH | GET /vehicle-types and /slots return HTTP 500; templates/ missing files | CONFIRMED (BUG-D) |
| Slot reservation race condition — Redis key leaks on duplicate-plate rejection | HIGH | Code analysis: slot key set before DB duplicate check; no cleanup on early return | CODE-CONFIRMED (BUG-E) |
| Hardcoded SECRET_KEY 'change-me' | HIGH | Trivially guessable session signing key in app.py:14 | CONFIRMED (BUG-F) |
| GET-based logout with no CSRF protection | MEDIUM | /logout accepts GET; no POST requirement, no token validation | CONFIRMED (BUG-G) |
| Overly aggressive license plate validation | MEDIUM | Valid real plates (7-digit, sequential patterns) rejected by is_sequential() check | CONFIRMED (BUG-H) |

## Test Cases

### Authentication & Authorization (AUTH)

**TC-AUTH-01 — Valid login flow**
- Preconditions: User has credentials admin/password
- Steps: 1) POST /login with username/password 2) Verify redirect to dashboard 3) Verify session cookie set
- Expected: 302 redirect, authenticated session, dashboard accessible

**TC-AUTH-02 — Invalid login rejection**
- Preconditions: None
- Steps: 1) POST /login with wrong credentials 2) Assert error flash message
- Expected: Remain on login page, "Invalid credentials" displayed

**TC-AUTH-03 — Logout via GET request (CSRF vulnerability)**
- Preconditions: Authenticated session
- Steps: 1) GET /logout (no POST, no CSRF token) 2) Verify redirect to /login
- Expected: **Actual:** 302 redirect succeeds. **Issue:** No POST/CSRF required (BUG-G)

**TC-AUTH-04 — Unauthenticated access to dashboard**
- Preconditions: No session cookie
- Steps: 1) GET / 2) Verify redirect to /login
- Expected: 302 Found → /login

### Parking Lifecycle (PARK)

**TC-PARK-01 — Start valid parking session**
- Preconditions: Authenticated, vehicle type "Standard" exists
- Steps: 1) POST /start with plate 55500001, slot X1, vehicle type 1 2) Verify session appears in active-sessions table
- Expected: Session created, visible on dashboard with start_time set, end_time NULL

**TC-PARK-02 — End parking session and verify history**
- Preconditions: Authenticated, active session exists for plate
- Steps: 1) POST /end/<session_id> 2) Verify session removed from active table 3) Navigate to /history 4) Verify session appears with fee calculated
- Expected: Session moved to history, fee ≠ NULL, fee ≠ '-'

**TC-PARK-03 — Duplicate parking detection**
- Preconditions: Authenticated, plate 55500002 has active session
- Steps: 1) POST /start with same plate 55500002, different slot 2) Verify rejection
- Expected: Flash "Duplicate parking prevented: this car is already parked"; session not created

**TC-PARK-04 — Re-ending an already-ended session (double-billing)**
- Preconditions: Authenticated, session exists and is closed (end_time set)
- Steps: 1) POST /end/<id> first time 2) Observe "Parking ended" flash 3) POST /end/<id> second time 4) Observe response body
- Expected: **Actual:** Second call produces new "Parking ended" flash and triggers billing again. **Issue:** No guard (BUG-B)

### Authorization Boundaries (AUTHZ)

**TC-AUTHZ-01 — Non-admin user cannot create accounts**
- Preconditions: Non-admin user authenticated
- Steps: 1) POST /users/add with username/password 2) Verify rejection or admin check
- Expected: **Actual:** User created successfully. **Issue:** No admin check (BUG-C)

**TC-AUTHZ-02 — Non-admin cannot delete users**
- Preconditions: Non-admin user authenticated
- Steps: 1) POST /users/delete/<user_id> 2) Verify rejection
- Expected: **Actual:** User deleted successfully. **Issue:** No admin check (BUG-C)

### File Security (UPLOAD)

**TC-UPLOAD-01 — Unauthenticated user cannot access uploaded files**
- Preconditions: File uploaded and URL known (e.g., test_photo.jpg)
- Steps: 1) No auth cookie 2) GET /uploads/test_photo.jpg 3) Verify 401/302 redirect
- Expected: **Actual:** HTTP 200 + file content returned. **Issue:** No @login_required decorator (BUG-A)

**TC-UPLOAD-02 — Authenticated user can download own uploads**
- Preconditions: Authenticated, image file uploaded
- Steps: 1) GET /uploads/<filename> with auth cookie 2) Verify 200 + file
- Expected: File returned (works because auth check missing entirely)

### Input Validation (VALIDATE)

**TC-VALIDATE-01 — 7-digit Israeli plate rejected**
- Preconditions: Authenticated
- Steps: 1) POST /start with plate "1234567" 2) Observe flash message
- Expected: **Actual:** Validation error "cannot be a sequential pattern" + "must be 8 digits long". **Issue:** Over-strict check (BUG-H)

**TC-VALIDATE-02 — Sequential plate pattern rejected**
- Preconditions: Authenticated
- Steps: 1) POST /start with plate "12345678" 2) Observe flash message
- Expected: **Actual:** "cannot be a sequential pattern" flash. **Issue:** Real plates can be sequential (BUG-H)

**TC-VALIDATE-03 — Valid plate "55500001" accepted**
- Preconditions: Authenticated
- Steps: 1) POST /start with plate "55500001" (non-sequential, 8 digits) 2) Verify success
- Expected: Session created

## Bugs Found

Eight bugs confirmed via HTTP reproduction and source code analysis:

| ID | Title | Severity | Component | Repro | Impact |
|---|---|---|---|---|---|
| **BUG-A** | Public Upload Disclosure | CRITICAL | app.py:283-285 | GET /uploads/<filename> without auth returns HTTP 200 + file | Unauthenticated exfiltration of all vehicle images |
| **BUG-B** | Duplicate Billing on Re-End | CRITICAL | app.py:167-203 | POST /end/<id> twice on closed session; both trigger /charge API calls | Customer charged multiple times per parking session |
| **BUG-C** | No Auth on User Management | HIGH | app.py:217-242 | Non-admin user POSTs to /users/add; account created; no admin check in code | Any user can create/delete accounts, escalate privileges |
| **BUG-D** | Missing Templates → 500 | HIGH | templates/ | GET /vehicle-types or /slots returns HTTP 500; vehicle_types.html and slots.html missing | Admin cannot configure rates or manage slots |
| **BUG-E** | Slot Reservation Redis Leak | HIGH | app.py:110-123 | Slot key set in Redis before DB duplicate check; no cleanup on early return | Legitimate vehicles blocked from slots for up to 1 hour |
| **BUG-F** | Hardcoded SECRET_KEY | HIGH | app.py:14 | SECRET_KEY = 'change-me' in source | Attacker can forge admin session cookies offline |
| **BUG-G** | GET-Based Logout (CSRF) | MEDIUM | app.py:65-69 | GET /logout succeeds; no POST, no CSRF token required | Attacker can embed logout link; force user logout |
| **BUG-H** | Aggressive Plate Validation | MEDIUM | forms.py:7-52 | Plates "12345678" (sequential) and "1234567" (7-digit) rejected; both are valid Israeli formats | Legitimate vehicle owners cannot register |

## Test Data & Environment Strategy

Each test uses isolated, unique test data (randomPlate(), uniqueSlot()) to enable parallel execution without cleanup-after-test contamination. The application runs in a Docker container (doringber/parking-manager:3.1.0) with SQLite backend and in-container Redis. Credentials are admin/password. Billing service integration is real (not mocked); we observed actual billing calls via app logs. No database reset between tests; each test operates on independent data. Historical isolation is achieved through per-test unique license plates, not shared fixtures.

## What We Didn't Test (And Why)

- **Load and concurrency at scale** — Single-user exploratory testing, not load profile. Real concurrency issues (race conditions) identified via code review instead.
- **Browser compatibility** — Playwright/Chromium only; Firefox/Safari not tested. Not a priority for a backend system.
- **Mobile responsiveness** — Desktop Playwright only. Mobile testing would require device emulation and extended timeline.
- **Accessibility (WCAG)** — No axe or screen-reader testing. Would require separate accessibility testing scope.
- **Billing service internals** — We tested the parking app's calls to /charge; billing service itself is a black box (deployed separately).
- **All vehicle types and rates** — Only tested with default "Standard" type. Additional types could have validation issues, but rate_per_hour field is missing from VehicleTypeForm (BUG-D).
- **API client libraries** — Only tested HTTP layer via Playwright and curl; Python SDK integration not tested.
