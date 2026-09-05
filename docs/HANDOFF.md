# 📋 CarbonScan AI — Master Handoff Document

> [!CAUTION]
> **Historical — snapshot ของ 22 พ.ค. 2569 ห้ามอ่านเป็นสถานะปัจจุบัน**
> เอกสารนี้เรียกตัวเองว่า "single reference doc" แต่บรรยายทีม 3 คน · deadline NSC 2026 ·
> และเว็บที่ยัง deploy ไม่เสร็จ — **ไม่มีข้อไหนเป็นจริงแล้ว** NSC ไม่ผ่าน ทำคนเดียว
> และเว็บ live อยู่ที่ https://treeqcarbon.vercel.app
> สถานะปัจจุบัน: `CLAUDE.md` · [PROJECT_SPEC.md](PROJECT_SPEC.md) · [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md)

> **The single reference doc for everything about this project.**
> Read this if you lose your other notes or onboard a new team member.
>
> **Last updated:** 2026-05-22 (after PR #9 — RLS policies applied)
> **Project Status:** Phase 0 (Proposal Sprint) — 7 days to deadline

---

## ⚡ TL;DR

**CarbonScan AI** — แพลตฟอร์มประเมินคาร์บอนต้นไม้ด้วย LiDAR + AI + B2B Carbon Marketplace
- **Competition:** NSC 2026 หมวด 14 อุดมศึกษา
- **Team:** User (Lead/Backend/ML/Mobile) + Person A (Web) + Person B (Design)
- **Deadlines:** 29 พ.ค. (Proposal) · 17 ก.ค. (Final) · 21 ส.ค. (Pitching)
- **Repo:** https://github.com/Remote55/carbonscan-ai
- **Backend:** https://umuszxwwwxyvqxwhlpxf.supabase.co (Singapore)
- **Web:** ยังไม่ deploy (Vercel pending)

---

## 🗂 Documentation Map (where to find what)

| Want to... | Read |
|---|---|
| Onboard a teammate | [`docs/ONBOARDING.md`](ONBOARDING.md) |
| Understand system design | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) |
| See timeline phases | [`docs/ROADMAP.md`](ROADMAP.md) |
| Setup dev env locally | [`docs/DEVELOPMENT.md`](DEVELOPMENT.md) |
| Deploy to production | [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) |
| Look up API endpoints | [`docs/API.md`](API.md) |
| Check DB schema | [`docs/DATA_MODEL.md`](DATA_MODEL.md) |
| Setup Supabase from scratch | [`docs/SUPABASE_SETUP.md`](SUPABASE_SETUP.md) |
| **Test project by hand (Web + API + Mobile)** | **[`docs/MANUAL_TESTING.md`](MANUAL_TESTING.md)** ⭐ |
| Test Auth flow live (deep dive) | [`docs/AUTH_TESTING.md`](AUTH_TESTING.md) |
| Understand ML pipeline | [`docs/ml/PIPELINE.md`](ml/PIPELINE.md) |
| TGO equations | [`docs/ml/ALLOMETRIC.md`](ml/ALLOMETRIC.md) |
| Why "X" was chosen | [`docs/decisions/`](decisions/) (6 ADRs) |
| Brand guidelines | [`docs/design/BRAND.md`](design/BRAND.md) |
| Daily task list | [`../TASKS.md`](../TASKS.md) |
| NSC Proposal | [`../proposal/outline.md`](../proposal/outline.md) |
| 5 questions for advisor | [`../proposal/5-questions-answers.md`](../proposal/5-questions-answers.md) |
| Email advisor template | [`../proposal/advisor_email.md`](../proposal/advisor_email.md) |

---

## 🛠 Tech Stack (with installed versions)

### Web Frontend
| Tool | Version | Purpose |
|---|---|---|
| Next.js | 14.2.x | App Router framework |
| React | 18.3.1 | UI library |
| TypeScript | 5.4.x | Type system |
| Tailwind CSS | 3.4.x | Utility CSS |
| shadcn/ui | (base-nova style) | Component primitives |
| @supabase/ssr | 0.4.x | Supabase Next.js bindings |
| @supabase/supabase-js | 2.43.x | Supabase JS SDK |
| @react-three/fiber | 8.16.x | Three.js React wrapper (3D viewer) |
| react-leaflet | 4.2.x | GIS map |
| @tanstack/react-query | 5.45.x | Server state |
| Zustand | 4.5.x | Client state |
| Geist | latest | Font (Vercel) |

### Mobile
| Tool | Version | Purpose |
|---|---|---|
| Flutter | 3.24.5 | Cross-platform framework |
| Dart | 3.5.x | Language |
| Riverpod | 2.5.x | State management |
| go_router | 14.2.x | Routing |
| camera | 0.11.x | Camera access |
| geolocator | 12.0.x | GPS |
| tflite_flutter | 0.10.x | On-device ML |
| supabase_flutter | 2.5.x | Auth + DB |

### Backend
| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11.9 | Runtime |
| FastAPI | 0.111.x | Web framework |
| Pydantic | 2.x | Validation |
| SQLAlchemy | 2.0.x (async) | ORM |
| asyncpg | 0.29.x | Postgres driver |
| GeoAlchemy2 | 0.15.x | PostGIS bindings |
| Alembic | 1.13.x | Migrations |
| supabase-py | 2.5.x | Supabase SDK |
| python-jose | 3.3.x | JWT (kept for future) |
| Uvicorn | 0.47.x | ASGI server |

### ML / AI
| Tool | Version | Purpose |
|---|---|---|
| PyTorch | 2.3+ | Deep learning |
| Open3D | 0.18+ | Point cloud library |
| laspy | 2.5+ | LAS file I/O |
| PDAL | 3.4+ | Point cloud pipeline |
| COLMAP | (external) | Structure from Motion |
| OpenMVS | (external) | Multi-View Stereo |

### Database & Cloud
| Tool | Version | Purpose |
|---|---|---|
| PostgreSQL | 17.6 | Database (hosted on Supabase) |
| PostGIS | 3.3.7 | Spatial extension |
| Supabase | (managed) | DB + Auth + Storage |
| RunPod | (planned) | Serverless GPU for ML worker |

### DevOps
| Tool | Version | Purpose |
|---|---|---|
| pnpm | 9.x | Node package manager |
| Turborepo | 1.13.x | Monorepo orchestrator |
| GitHub Actions | n/a | CI/CD |
| CodeQL | n/a | Security scanning |
| GitHub CLI (gh) | 2.92.x | PR management |

---

## 🔑 Live Services & Accounts

| Service | URL | Owner | Status |
|---|---|---|---|
| **GitHub Repo** | https://github.com/Remote55/carbonscan-ai | Remote55 | ✅ Public |
| **Supabase** | https://umuszxwwwxyvqxwhlpxf.supabase.co | openclaw org | ✅ Active (free tier) |
| Supabase Dashboard | https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf | — | — |
| Vercel | (not yet deployed) | — | ⏳ Pending |
| Railway | (not yet deployed) | — | ⏳ Pending |
| RunPod | (not yet set up) | — | ⏳ Pending |
| Domain | (none) | — | ⏳ Phase 2 |
| Supabase region | aws-1-ap-southeast-1 (Singapore) | — | — |

### Supabase Resources Created
- **Project ref:** `umuszxwwwxyvqxwhlpxf`
- **Tier:** Free (Nano compute, 500MB DB)
- **PostgreSQL:** v17.6 with PostGIS 3.3.7
- **Tables:** users, plots, trees, jobs, transactions, species_db (+ alembic_version)
- **Extensions:** postgis, postgis_topology, pg_trgm, unaccent, pgcrypto
- **Storage buckets:** point-clouds (private, 50MB), photos (private, 20MB), reports (public, 5MB), brand-assets (public, 5MB)
- **RLS:** Enabled on 5 app tables, 15 policies, auto-sync trigger from auth.users → public.users

---

## 🔐 Credentials Checklist

> ⚠️ **All values are in `.env` files (gitignored). Never commit secrets.**

### What you need
| Variable | Where to put | Where to get | Status |
|---|---|---|---|
| `SUPABASE_URL` | All 3 .env | Supabase Dashboard → Settings → API | ✅ Set |
| `SUPABASE_ANON_KEY` (`sb_publishable_*`) | services/api + apps/web | Same as above | ✅ Set |
| `SUPABASE_SERVICE_KEY` (`sb_secret_*`) | services/api + services/ml | Same as above | ⚠️ **ROTATE** (exposed in chat) |
| `DATABASE_URL` (pooler URI) | services/api | Connect → Session pooler | ✅ Set |
| `JWT_SECRET` (legacy) | services/api | Generated random | ✅ Set (dev value) |
| `RUNPOD_API_KEY` | services/api | RunPod dashboard | ⏳ Phase 2 |
| `HF_TOKEN` | services/ml | huggingface.co/settings/tokens | ⏳ When training |
| `WANDB_API_KEY` | services/ml | wandb.ai/authorize | ⏳ When training |

### Critical Pending Actions
1. **🚨 ROTATE service_role key** — exposed in chat. Reset at https://supabase.com/dashboard/project/umuszxwwwxyvqxwhlpxf/settings/api
2. Set `JWT_SECRET` to production value before deploy

---

## 📁 Critical Files Map

### Repository Structure
```
D:\Project_Carbon\                  ← repo root
├── README.md                        ← project overview
├── TASKS.md                         ← daily task tracker
├── CLAUDE.md                        ← AI assistant memory
├── CONTRIBUTING.md                  ← Git/PR conventions
├── LICENSE                          ← MIT
├── package.json                     ← monorepo root (pnpm workspaces)
├── pnpm-workspace.yaml
├── turbo.json
│
├── apps/
│   ├── web/                         ← Next.js 14 (Person A)
│   │   ├── src/app/
│   │   │   ├── page.tsx             ← Landing
│   │   │   ├── layout.tsx           ← Root layout + SEO
│   │   │   ├── (auth)/              ← Login + Signup (server+client split)
│   │   │   ├── (dashboard)/         ← Protected pages
│   │   │   └── auth/callback/       ← OAuth/email handler
│   │   ├── src/lib/
│   │   │   ├── supabase.ts          ← Browser client
│   │   │   ├── supabase-server.ts   ← Server Components client
│   │   │   ├── auth.ts              ← signUp/signIn/signOut helpers
│   │   │   ├── api.ts               ← Typed fetch wrapper to FastAPI
│   │   │   └── utils.ts             ← cn() + formatters
│   │   ├── src/middleware.ts        ← Route protection + session refresh
│   │   ├── public/
│   │   │   └── logo.png             ← Team logo (Person B)
│   │   ├── .env.local               ← Real secrets (gitignored)
│   │   ├── .env.example             ← Template
│   │   ├── tailwind.config.ts
│   │   ├── next.config.mjs
│   │   └── package.json
│   │
│   └── mobile/                      ← Flutter (User, Phase 3)
│       ├── lib/
│       │   ├── main.dart
│       │   ├── app.dart
│       │   ├── core/                ← theme, config, network
│       │   ├── features/            ← camera, tree_scan, results, species_id
│       │   └── shared/              ← widgets, providers
│       ├── pubspec.yaml
│       ├── scripts/run-dev.sh / .ps1
│       └── SETUP.md
│
├── services/
│   ├── api/                         ← FastAPI (User)
│   │   ├── app/
│   │   │   ├── main.py              ← FastAPI entry
│   │   │   ├── core/
│   │   │   │   ├── config.py        ← Pydantic Settings (env loader)
│   │   │   │   ├── database.py      ← async SQLAlchemy
│   │   │   │   ├── security.py      ← JWT + bcrypt
│   │   │   │   └── exceptions.py    ← Typed errors
│   │   │   ├── api/
│   │   │   │   ├── deps.py          ← FastAPI dependencies
│   │   │   │   └── v1/
│   │   │   │       ├── router.py    ← Endpoint aggregator
│   │   │   │       ├── health.py    ← /health + /health/ready
│   │   │   │       ├── auth.py      ← /me implemented; /signup, /login = 501
│   │   │   │       ├── upload.py    ← stubs
│   │   │   │       ├── jobs.py      ← stubs
│   │   │   │       └── trees.py     ← stubs
│   │   │   ├── models/              ← SQLAlchemy ORM (User, Tree)
│   │   │   ├── schemas/             ← Pydantic schemas
│   │   │   └── services/
│   │   │       └── supabase.py      ← verify_supabase_token()
│   │   ├── alembic/
│   │   │   ├── env.py
│   │   │   └── versions/0001_initial_schema.py
│   │   ├── scripts/
│   │   │   ├── setup_supabase.sql   ← Enable extensions
│   │   │   ├── seed_species_db.sql  ← Insert 5 species
│   │   │   └── rls_policies.sql     ← ⭐ RLS + auth sync trigger
│   │   ├── tests/                   ← pytest fixtures + 3 tests
│   │   ├── .env                     ← Real secrets (gitignored)
│   │   ├── .venv/                   ← Python venv (gitignored)
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── ml/                          ← PyTorch ML Pipeline (User)
│       ├── pipeline/
│       │   ├── main.py              ← 8-step orchestrator
│       │   ├── ground_classification.py    ← Stub (CSF)
│       │   ├── height_normalization.py     ← Stub
│       │   ├── canopy_height_model.py      ← Stub (Pit-free)
│       │   ├── tree_segmentation.py        ← Stub (Watershed)
│       │   ├── wood_leaf_separation.py     ← Stub (PointNet++)
│       │   ├── qsm.py                      ← Stub (Cylinder fit)
│       │   ├── species_classifier.py       ← Stub (ResNet)
│       │   └── allometric.py        ← ⭐ FULLY IMPLEMENTED + 16 tests pass
│       ├── photogrammetry/          ← Stubs (COLMAP, OpenMVS)
│       ├── data/
│       │   └── species_db.csv       ← 5 species (matches DB seed)
│       ├── runpod_handler.py        ← Serverless GPU entry
│       └── tests/test_allometric.py ← 16 tests
│
├── packages/                        ← Shared (mostly placeholder for Phase 1+)
│   ├── design-tokens/
│   ├── ui/
│   └── types/
│
├── docs/                            ← THIS DIRECTORY
│   ├── HANDOFF.md                   ← ⭐ YOU ARE HERE
│   ├── ONBOARDING.md
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── DEVELOPMENT.md
│   ├── DEPLOYMENT.md
│   ├── API.md
│   ├── DATA_MODEL.md
│   ├── SUPABASE_SETUP.md            ← step-by-step Supabase guide
│   ├── AUTH_TESTING.md              ← ⭐ test signup/login live
│   ├── ml/
│   │   ├── PIPELINE.md
│   │   ├── ALLOMETRIC.md            ← verified numbers + 5-species table
│   │   └── DATASETS.md
│   ├── design/
│   │   ├── DESIGN_SYSTEM.md
│   │   └── BRAND.md                 ← official team logo concept
│   └── decisions/                   ← 6 ADRs
│
├── proposal/                        ← NSC submission docs
│   ├── README.md
│   ├── outline.md                   ← ⭐ Proposal v1 ready to copy to Word
│   ├── 5-questions-answers.md       ← Answers to advisor's 5 questions
│   ├── references.md                ← 20+ academic citations
│   └── advisor_email.md             ← ⭐ Email template (NEW)
│
├── data/                            ← Sample datasets (gitignored mostly)
│   ├── samples/
│   └── README.md
│
├── assets/
│   └── brand/
│       ├── logo.png                 ← Master logo
│       └── README.md                ← Brand asset docs
│
├── scripts/
│   ├── setup.sh                     ← One-command setup (mac/linux)
│   └── setup.ps1                    ← One-command setup (Windows)
│
└── .github/
    ├── workflows/                   ← 5 CI workflows
    │   ├── ci-web.yml
    │   ├── ci-api.yml
    │   ├── ci-ml.yml
    │   ├── ci-mobile.yml
    │   └── codeql.yml
    ├── PULL_REQUEST_TEMPLATE.md
    ├── ISSUE_TEMPLATE/
    └── CODEOWNERS
```

---

## 🚀 Setup Commands (from zero)

### One-time bootstrap

```bash
# 1. Clone
git clone https://github.com/Remote55/carbonscan-ai.git
cd carbonscan-ai

# 2. Install Node deps for all workspaces
pnpm install

# 3. Setup Python venv for API
cd services/api
python -m venv .venv
.venv\Scripts\activate                  # Windows
# source .venv/bin/activate              # macOS/Linux
pip install -e ".[dev]"
deactivate
cd ../..

# 4. Setup Python venv for ML
cd services/ml
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,cpu]"
deactivate
cd ../..

# 5. (Optional) Flutter
cd apps/mobile
flutter create . --platforms=android --org=com.carbonscan
flutter pub get
cd ../..

# 6. Copy .env templates and fill secrets
cp services/api/.env.example services/api/.env       # Then edit
cp apps/web/.env.example apps/web/.env.local         # Then edit
cp services/ml/.env.example services/ml/.env         # Then edit
cp apps/mobile/.env.example apps/mobile/.env         # Then edit (optional)
```

### Daily commands

```bash
# Web dev server
pnpm web:dev                    # → http://localhost:3000

# Backend API
cd services/api
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs (Swagger UI)

# ML tests
cd services/ml
.venv/Scripts/python.exe -m pytest tests/ -v

# Mobile (after setup)
cd apps/mobile
./scripts/run-dev.sh            # Or run-dev.ps1 on Windows

# Database migrations
cd services/api
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m alembic downgrade -1    # rollback
.venv/Scripts/python.exe -m alembic revision --autogenerate -m "msg"

# Lint + tests (run before pushing)
pnpm lint                       # Web
cd services/api && ruff check . && pytest
cd services/ml && ruff check pipeline/ tests/ && pytest tests/test_allometric.py
```

---

## 🔄 Git Workflow

Branch protection on `main`:
- ✅ Require PR
- ✅ Linear history (no merge commits)
- ✅ Resolve conversations before merge
- ✅ Code owner review (CODEOWNERS file)
- ❌ Force push blocked

### Standard flow

```bash
# 1. Branch
git checkout main && git pull origin main
git checkout -b feat/your-feature

# 2. Work + commit
git add <files>
git commit -m "feat(scope): description"

# 3. Push + PR
git push -u origin feat/your-feature
gh pr create --title "..." --body "..."

# 4. After CI green, merge (admin can self-merge solo PRs)
gh pr merge <N> --squash --delete-branch --admin

# 5. Sync local main
git checkout main && git pull origin main
```

### Commit message format (Conventional Commits)
```
<type>(<scope>): <subject>

<body>

Co-Authored-By: ...
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `style`, `perf`
Scopes: `web`, `mobile`, `api`, `ml`, `db`, `design`, `infra`, `proposal`, `tasks`

---

## 📊 Status Snapshot (2026-05-22)

### What works end-to-end
- ✅ Repo on GitHub with branch protection
- ✅ 5 CI workflows (Web, API, ML, Mobile, CodeQL) — all passing
- ✅ Web Landing page boots
- ✅ Supabase project provisioned
- ✅ Database schema deployed (6 tables, PostGIS)
- ✅ 5 species seeded with allometric coefficients
- ✅ RLS policies + auth sync trigger applied
- ✅ FastAPI server runs + connects to live DB
- ✅ `GET /api/v1/auth/me` verifies Supabase JWT
- ✅ Web has login/signup pages (Pattern B)
- ✅ Route protection middleware

### What's tested
- ✅ Allometric calculator: 16/16 pytest passing, 95% coverage
- ✅ API health endpoints: all 200
- ✅ DB connection: confirmed via `/health/ready`
- ✅ Auth verification: 401 for invalid JWTs

### What's not done yet (intentional — Phase 1/2)
- ⏳ ML pipeline steps 1-7 (all stubs except allometric)
- ⏳ File upload + photogrammetry workers
- ⏳ 3D Point Cloud viewer (R3F)
- ⏳ GIS Map (Leaflet)
- ⏳ Marketplace UI
- ⏳ Mobile app (Flutter create not run yet)
- ⏳ Vercel/Railway/RunPod deployment

### What's blocking (User actions)
- 🔴 **Send Proposal v1 to advisor** (deadline: tomorrow 23 พ.ค.)
- 🔴 Register on SIMs (https://www.nstda.or.th/sims)
- 🔴 Answer 7 Open Questions in TASKS.md (team names, advisor info, etc.)
- 🟠 Rotate service_role key (security)

---

## 📅 Critical Dates

| Date | What | Status |
|---|---|---|
| **23 พ.ค. 2569** | Send Proposal v1 → ที่ปรึกษา | ⏳ |
| **24 พ.ค. 2569** | Revise Proposal v2 from feedback | ⏳ |
| **25 พ.ค. 2569** | START signature process (advisor + dean) | ⏳ |
| **28 พ.ค. 2569** | Upload to SIMs (1 day buffer) | ⏳ |
| **🔴 29 พ.ค. 2569 17:00** | **PROPOSAL DEADLINE** | 🔴 |
| 12 มิ.ย. 2569 | Proposal result announcement | ⏳ |
| 17 ก.ค. 2569 17:00 | Final report deadline | ⏳ |
| 7 ส.ค. 2569 | Pitching round announcement | ⏳ |
| 21 ส.ค. 2569 | Final competition (รอบชิงชนะเลิศ) | ⏳ |
| 24 ส.ค. 2569 | Champion announced | ⏳ |

---

## 🎓 Glossary

| Term | Meaning |
|---|---|
| **NSC 2026** | National Software Contest (Thailand), 28th edition, Buddhist year 2569 |
| **หมวด 14** | Competition category 14 — "Programs for science & tech development" (graduate level) |
| **TGO** | Thailand Greenhouse Gas Management Organization (อบก.) |
| **CBAM** | Carbon Border Adjustment Mechanism (EU carbon tax 2026+) |
| **DBH** | Diameter at Breast Height (1.3m) — standard tree measurement |
| **AGB / BGB** | Above-/Below-ground biomass |
| **LiDAR** | Light Detection And Ranging — 3D scanning tech |
| **Point Cloud** | Collection of 3D points captured by LiDAR or photogrammetry |
| **QSM** | Quantitative Structure Model — cylinder fitting to tree wood |
| **Allometric** | Equation relating tree dimensions (DBH, H) to biomass |
| **PointNet++** | Deep learning architecture for point clouds (Qi et al. 2017) |
| **COLMAP** | Open-source Structure-from-Motion software |
| **OpenMVS** | Multi-View Stereo dense reconstruction |
| **PostGIS** | PostgreSQL extension for geographic objects |
| **RLS** | Row-Level Security (PostgreSQL feature) |
| **Supavisor** | Supabase's connection pooler |
| **Pattern B** | Supabase Auth pattern: client uses JS SDK, backend verifies JWT |
| **Pooler (transaction vs session)** | Connection pooling modes — Session for migrations, Transaction for serverless |

---

## ⚠️ Troubleshooting

### "Cannot connect to Supabase"
- DNS issue with `db.xxx.supabase.co` → it's IPv6-only on free tier
- **Fix:** Use pooler URL `aws-1-ap-southeast-1.pooler.supabase.com:5432`
- Username format for pooler: `postgres.<project-ref>` (not `postgres`)

### "DuplicateTableError: idx_X_geometry already exists"
- GeoAlchemy2 auto-creates GIST indexes on Geometry columns
- **Fix:** Don't add explicit `CREATE INDEX` for geometry/location columns
- Already fixed in `0001_initial_schema.py` (PR #7)

### "ImportError: email-validator is not installed"
- **Fix:** `pip install email-validator` or `pip install -e ".[dev]"` reinstall

### "Unknown font 'Geist'" (Web)
- Geist is Vercel's font, not Google's
- **Fix:** `import { GeistSans } from 'geist/font/sans'` (already done in layout.tsx)

### "useSearchParams crashes build" (Next.js)
- Server-rendered pages with `useSearchParams` need Suspense
- **Fix:** Split into server-component page.tsx + client-component login-form.tsx wrapped in `<Suspense>`
- Already done for `/login` page

### "Tenant not found" (Supabase Pooler)
- Wrong region OR wrong username format
- **Fix:** Check region from Dashboard Connect modal → use exact hostname (e.g., `aws-1-ap-southeast-1`)
- Username MUST be `postgres.<project-ref>` for pooler

### "branch protection prohibits merge"
- Code owner self-review block (you can't approve your own PR)
- **Fix:** Use `gh pr merge <N> --admin --squash --delete-branch`
- Or wait for another reviewer

---

## 🔮 Future Roadmap (Beyond Phase 0)

### Phase 1: Foundation (12-30 มิ.ย.)
- Wire Web ↔ FastAPI ↔ Supabase end-to-end
- Implement ML pipeline steps 1-4 (ground → CHM → tree segmentation)
- Deploy preview environments (Vercel + Railway)
- Setup Sentry for error tracking

### Phase 2: Core AI (1-14 ก.ค.)
- Train PointNet++ on NEON dataset (target IoU ≥ 0.70)
- Implement QSM cylinder fitting
- 3D Point Cloud viewer (R3F + potree-core)
- Carbon marketplace UI

### Phase 3: Mobile + Submit (15-17 ก.ค.)
- Flutter camera multi-shot
- Photogrammetry pipeline (COLMAP/OpenMVS)
- Tree species classifier (TFLite)
- Final report submission

### Phase 4: Pitching (7-21 ส.ค.)
- Demo video 3-5 min
- Pitch deck
- Rehearsals + Q&A prep

---

## 📞 Quick Help

- **Stuck on setup?** → [docs/DEVELOPMENT.md](DEVELOPMENT.md)
- **Architectural question?** → [docs/decisions/](decisions/) (6 ADRs)
- **API endpoint?** → [docs/API.md](API.md) or http://localhost:8000/docs
- **DB schema?** → [docs/DATA_MODEL.md](DATA_MODEL.md)
- **Brand colors?** → [packages/design-tokens/README.md](../packages/design-tokens/README.md)
- **Allometric math?** → [docs/ml/ALLOMETRIC.md](ml/ALLOMETRIC.md)

---

**Last commit on main:** check `git log -1 --oneline` for latest
**Repo URL:** https://github.com/Remote55/carbonscan-ai
