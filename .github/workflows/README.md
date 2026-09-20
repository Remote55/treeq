# GitHub Actions Workflows

Automated checks that run on every push to `main` and every PR.

---

## Workflows

| Workflow | Trigger | What it does | Duration |
|---|---|---|---|
| **CI Web** | `apps/web/**`, `packages/**` changes | Lint + Type-check + Build + Test (Vitest) | ~3-5 min |
| **CI API** | `services/api/**` changes | Ruff + Format + Pytest with PostGIS sidecar | ~3 min |
| **CI ML** | `services/ml/**` changes | Ruff + Pytest (allometric tests) | ~5 min |
| **CI Mobile** | `apps/mobile/**` changes | Flutter analyze + Test + Debug APK build (main only) | ~5-8 min |
| **CodeQL** | Push to main, PRs, weekly | Security scan for JS/TS + Python | ~10 min |

---

## Path Filters

Each workflow uses `paths:` filter to only run when relevant files change.
This saves CI minutes and gives faster feedback.

Example: A PR that only modifies `docs/` won't trigger any CI workflow.

---

## Concurrency

All workflows use `concurrency` groups so that pushing a new commit to a PR
cancels the previous in-progress run for that PR — avoids wasted minutes.

---

## Secrets Required

For Phase 1+ workflows, add these in GitHub repo settings:

| Secret | Used by | Purpose |
|---|---|---|
| `VERCEL_TOKEN` | (future) deploy-preview | Web preview deploys |
| `VERCEL_ORG_ID` | (future) | — |
| `VERCEL_PROJECT_ID` | (future) | — |
| `RAILWAY_TOKEN` | (future) deploy-api | API deploys |
| `RUNPOD_API_KEY` | (future) deploy-ml | ML worker updates |
| `SUPABASE_URL` (build) | ci-web | Build with valid env |
| `SUPABASE_ANON_KEY` (build) | ci-web | Build with valid env |

For now, ci-web uses placeholder env vars to allow the build to succeed.

---

## Adding a New Workflow

1. Copy a similar workflow as template
2. Update `paths:` filter
3. Update `concurrency:` group
4. Add to this README's table
5. Open PR — workflow will validate on itself

---

## Local Testing

Run linters/tests locally before pushing:

```bash
# Web
cd apps/web && pnpm lint && pnpm type-check && pnpm test --run

# API
cd services/api && ruff check . && ruff format --check . && pytest

# ML
cd services/ml && ruff check pipeline/ tests/ && pytest tests/test_allometric.py

# Mobile
cd apps/mobile && dart format --output=none --set-exit-if-changed lib/ test/ && \
  flutter analyze --no-fatal-warnings && flutter test
```

---

## Status Badges

Add to README.md:

```markdown
[![CI Web](https://github.com/Remote55/treeq/actions/workflows/ci-web.yml/badge.svg)](https://github.com/Remote55/treeq/actions/workflows/ci-web.yml)
[![CI API](https://github.com/Remote55/treeq/actions/workflows/ci-api.yml/badge.svg)](https://github.com/Remote55/treeq/actions/workflows/ci-api.yml)
[![CI ML](https://github.com/Remote55/treeq/actions/workflows/ci-ml.yml/badge.svg)](https://github.com/Remote55/treeq/actions/workflows/ci-ml.yml)
[![CI Mobile](https://github.com/Remote55/treeq/actions/workflows/ci-mobile.yml/badge.svg)](https://github.com/Remote55/treeq/actions/workflows/ci-mobile.yml)
[![CodeQL](https://github.com/Remote55/treeq/actions/workflows/codeql.yml/badge.svg)](https://github.com/Remote55/treeq/actions/workflows/codeql.yml)
```
