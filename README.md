# Parking App E2E Tests

UI end-to-end tests and exploratory QA for a Flask parking-management web app (run locally in Docker).

**What it checks**
- Happy path: log in → start a parking session → end it → session shows as closed in history
- Known bug: ending the same session twice charges twice (kept as `test.fail` so the suite stays green while documenting it)
- `test-plan.md` and `exploration/bugs-verified.md` cover the wider test plan and 8 reproduced bugs (auth, billing, validation, uploads)

**Tools:** Playwright Test, TypeScript, Page Object Model, Docker

## Run it

```bash
# 1. Start the app under test (seeded login: admin / password)
docker run --platform linux/amd64 -d -p 5000:5000 --name parking-manager doringber/parking-manager:3.1.0

# 2. Install and run
npm install
npx playwright install chromium
npm test              # or: npm run test:headed
npx playwright show-report
```
