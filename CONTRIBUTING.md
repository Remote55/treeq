# Contributing to TreeQ Carbon Platform

> ขอบคุณที่สนใจร่วมพัฒนาโปรเจกต์ NSC 2026 กับเรา! เอกสารนี้สรุปวิธีการ contribute, code conventions และ workflow ของทีม

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Branching Strategy](#branching-strategy)
4. [Commit Conventions](#commit-conventions)
5. [Pull Request Process](#pull-request-process)
6. [Code Style](#code-style)
7. [Testing](#testing)
8. [Documentation](#documentation)

---

## Code of Conduct

- เคารพความคิดเห็นของทุกคนในทีม
- Feedback ที่ Code ไม่ใช่ที่คน
- ถามได้ทุกเรื่อง ไม่มี "คำถามโง่"
- ทำให้ทีมแข็งแกร่งกว่าตัวเอง

---

## Getting Started

1. **อ่าน [docs/ONBOARDING.md](docs/ONBOARDING.md)** ก่อน
2. **ตรวจสอบ [TASKS.md](TASKS.md)** ว่าตัวเองรับผิดชอบอะไร
3. **ดู [docs/decisions/](docs/decisions/)** เพื่อเข้าใจการตัดสินใจหลัก
4. **Setup environment** ตาม [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

---

## Branching Strategy

ใช้ **Git Flow แบบ simplified**:

```
main                  ← Production-ready (protected)
  ↑
develop               ← Integration branch (default)
  ↑
feature/xxx           ← Feature branches
fix/xxx               ← Bug fixes
docs/xxx              ← Docs only
```

### Branch Naming
- `feature/web-3d-viewer` (ฟีเจอร์ใหม่)
- `fix/api-upload-timeout` (แก้บั๊ก)
- `docs/architecture-update` (แก้เอกสาร)
- `refactor/ml-pipeline-cleanup` (refactor)
- `chore/upgrade-deps` (maintenance)

### Rules
- ห้าม push ตรงเข้า `main` หรือ `develop`
- ทุก feature branch ต้องผ่าน PR review
- Merge เข้า `main` เฉพาะตอน release

---

## Commit Conventions

ใช้ **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: ฟีเจอร์ใหม่
- `fix`: แก้บั๊ก
- `docs`: เอกสาร
- `style`: format code (ไม่กระทบ logic)
- `refactor`: refactor โค้ด
- `perf`: ปรับ performance
- `test`: เพิ่ม/แก้ test
- `chore`: maintenance, deps
- `ci`: CI/CD config

### Scopes
- `web` — Web Dashboard
- `mobile` — Mobile App
- `api` — Backend API
- `ml` — ML Pipeline
- `design` — Design System / Tokens
- `docs` — Documentation
- `infra` — DevOps / Cloud

### Examples
```
feat(web): add 3D point cloud viewer with Three.js

Implement react-three-fiber wrapper around potree-core to render
.las files in browser. Supports color-coded wood/leaf classification.

Refs: #42
```

```
fix(api): handle timeout when LAS file > 100MB

Increase nginx client_max_body_size and add streaming upload.

Closes #58
```

```
docs(ml): add TGO allometric equations for 5 species
```

---

## Pull Request Process

### 1. Before Creating PR
- [ ] Pull latest `develop`
- [ ] Run `pnpm lint` และ `pnpm test` ผ่าน
- [ ] อัปเดต docs ที่เกี่ยวข้อง
- [ ] เพิ่ม/แก้ test ตามความเหมาะสม

### 2. Create PR
- Title: ใช้ Conventional Commit format
- Body: ใช้ template `.github/PULL_REQUEST_TEMPLATE.md`
- Link issues ที่เกี่ยวข้อง
- Tag reviewer (อย่างน้อย 1 คน)

### 3. PR Template
```markdown
## Summary
<1-3 bullet points>

## Changes
- ...

## Testing
- [ ] Manual test passed
- [ ] Unit tests added/updated
- [ ] Tested on production-like data

## Screenshots (ถ้ามี UI)
<before/after>

## Checklist
- [ ] Code follows style guide
- [ ] Self-reviewed
- [ ] Docs updated
- [ ] No console.log / print debug

Closes #<issue>
```

### 4. Review & Merge
- รอ approval อย่างน้อย 1 คน
- Resolve all conversations
- Squash & merge (default)

---

## Code Style

### TypeScript / JavaScript (Web, packages/)
- **Linter:** ESLint (airbnb-base)
- **Formatter:** Prettier (2 spaces)
- **Naming:**
  - `camelCase` สำหรับ variables, functions
  - `PascalCase` สำหรับ Components, Types
  - `UPPER_SNAKE_CASE` สำหรับ constants
- **File Naming:** `kebab-case.ts` ยกเว้น Components ใช้ `PascalCase.tsx`

### ลำดับการติดตั้ง Python (สำคัญ)

`packages/run-contract` เป็น workspace package **ไม่ได้อยู่บน PyPI**
ทั้ง `services/api` และ `services/ml` ประกาศมันเป็น dependency
ต้องติดตั้งมันก่อน ไม่งั้น `pip install -e .` จะไปหาบน PyPI แล้วล้ม

```bash
pip install -e packages/run-contract     # จาก repo root ก่อนเสมอ

cd services/api && pip install -e ".[dev]"
cd services/ml  && pip install -e ".[cpu]"
```

แก้ contract แล้วต้อง regenerate ก่อน commit:

```bash
cd packages/run-contract
python tools/generate_contract.py        # schema + TypeScript + Zod
python tools/generate_contract.py --check # CI รันอันนี้ ล้มถ้า drift
```

### Python (services/api, services/ml)
- **Linter:** ruff
- **Formatter:** black (line length 100)
- **Type hints:** บังคับใช้ทุก function public
- **Naming:**
  - `snake_case` สำหรับ functions, variables
  - `PascalCase` สำหรับ Classes
  - `UPPER_SNAKE_CASE` สำหรับ constants

### Dart (Mobile)
- **Linter:** flutter_lints
- **Formatter:** dart format
- **Naming:** ตาม [Effective Dart](https://dart.dev/effective-dart/style)

---

## Testing

### Web (apps/web)
- Unit: Vitest + React Testing Library
- E2E: Playwright (กรณีสำคัญ)

### Mobile (apps/mobile)
- Unit: `flutter test`
- Widget: `flutter test --tags widget`
- Integration: `flutter test integration_test/`

### Backend (services/api)
- Unit + Integration: `pytest`
- Coverage target: > 70%

### ML (services/ml)
- Unit tests for utilities
- Notebook reproducibility checks
- Model performance benchmarks (เก็บใน `tests/benchmarks/`)

---

## Documentation

### When to Write Docs
- **เพิ่ม API endpoint** → update `docs/API.md`
- **เปลี่ยน DB schema** → update `docs/DATA_MODEL.md` + Alembic migration
- **ตัดสินใจ architectural** → เขียน ADR ใน `docs/decisions/`
- **เพิ่มฟีเจอร์ใหญ่** → update README ของ app/service นั้น
- **เพิ่ม dependency หลัก** → อัปเดต README หลัก

### ADR (Architecture Decision Records)
ทุกการตัดสินใจสำคัญต้องมี ADR:
```bash
# Copy template
cp docs/decisions/_template.md docs/decisions/0007-your-decision.md
```

Format:
- **Status:** Proposed / Accepted / Deprecated
- **Context:** สถานการณ์
- **Decision:** สิ่งที่ตัดสินใจ
- **Consequences:** ผลกระทบ + tradeoffs

---

## Questions?

- ทักใน Line/Discord ทีม
- ดู [docs/](docs/)
- ถาม User (Team Lead) สำหรับเรื่อง architectural

**ขอบคุณที่ contribute! 🌲**
