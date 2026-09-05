# 🛠 Development Guide

> Setup, conventions, and workflow for daily development

---

## Prerequisites Installation

### macOS / Linux

```bash
# Node.js (via fnm or nvm)
brew install fnm
fnm install 20
fnm use 20

# pnpm
npm install -g pnpm

# Python 3.11
brew install python@3.11

# Flutter
brew install --cask flutter

# Docker (optional)
brew install --cask docker
```

### Windows

```powershell
# Node.js (via nvm-windows)
# Download from https://github.com/coreybutler/nvm-windows
nvm install 20
nvm use 20

# pnpm
npm install -g pnpm

# Python 3.11
# Download from https://www.python.org/downloads/

# Flutter
# Download from https://docs.flutter.dev/get-started/install/windows
# Add to PATH

# Docker Desktop (optional)
# Download from https://www.docker.com/products/docker-desktop
```

### Verify Setup

```bash
node --version    # ≥ v20
pnpm --version    # ≥ 9
python --version  # 3.11.x
flutter --version # 3.x
git --version     # ≥ 2.40
```

---

## Initial Repository Setup

```bash
# 1. Clone
git clone https://github.com/Remote55/treeq.git
cd treeq

# 2. Install JS dependencies
pnpm install

# 3. Setup Python environments
# API
cd services/api
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows PowerShell
pip install -e ".[dev]"
deactivate
cd ../..

# ML
cd services/ml
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
deactivate
cd ../..

# 4. Flutter
cd apps/mobile
flutter pub get
cd ../..

# 5. Environment variables
cp services/api/.env.example services/api/.env
cp apps/web/.env.example apps/web/.env.local
# ⚠️ ขอ secrets จาก User
```

---

## Day-to-Day Commands

### Run Everything (Web + API)

```bash
# Root directory
pnpm dev    # Uses Turborepo to run apps in parallel
```

### Individual Services

```bash
# Web only
pnpm web:dev
# → http://localhost:3000

# API only
pnpm api:dev
# → http://localhost:8000
# → Swagger docs: http://localhost:8000/docs

# Mobile (with device/emulator running)
pnpm mobile:run

# ML notebooks
pnpm ml:notebook
# → http://localhost:8888
```

### Build for Production

```bash
# All
pnpm build

# Individual
pnpm --filter web build
cd services/api && python -m build
cd apps/mobile && flutter build apk
```

### Linting & Formatting

```bash
# JS/TS
pnpm lint
pnpm format

# Python (in services/api or services/ml)
ruff check .
black .
mypy .

# Flutter (in apps/mobile)
dart format .
flutter analyze
```

### Testing

```bash
# All (Turborepo)
pnpm test

# Web
pnpm --filter web test
pnpm --filter web test:e2e

# API
cd services/api && pytest

# ML
cd services/ml && pytest

# Mobile
cd apps/mobile && flutter test
```

---

## Git Workflow

### Branch from `develop`

```bash
git checkout develop
git pull origin develop
git checkout -b feature/web-3d-viewer
```

### Commit Often, Small Commits

```bash
git add apps/web/src/components/PointCloudViewer.tsx
git commit -m "feat(web): scaffold PointCloudViewer component"
```

### Push & PR

```bash
git push -u origin feature/web-3d-viewer
# Open PR via GitHub UI or `gh pr create`
```

📖 ดู [CONTRIBUTING.md](../CONTRIBUTING.md) สำหรับ branching/commit conventions ละเอียด

---

## Environment Variables

### apps/web/.env.local
```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Map
NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxx (optional)
```

### services/api/.env
```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/carbonscan
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxx...

# Storage
SUPABASE_STORAGE_BUCKET=carbonscan-uploads

# JWT
JWT_SECRET=<random-32-byte-string>
JWT_ALGORITHM=HS256

# GPU Worker
RUNPOD_API_KEY=<from-runpod>
RUNPOD_ENDPOINT_ID=<endpoint-id>

# Queue
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,https://treeqcarbon.vercel.app
```

### services/ml/.env
```env
# Hugging Face (model hub)
HF_TOKEN=hf_xxx

# Weights & Biases (optional, for tracking experiments)
WANDB_API_KEY=xxx

# NEON Dataset (optional, only for download script)
NEON_API_TOKEN=xxx
```

⚠️ **NEVER COMMIT `.env` FILES** — only `.env.example`

---

## Database Setup

> [!CAUTION]
> **There is no database.** The API's database layer was deleted in `927ae78` —
> no table backed it, no endpoint read from it. Nothing in this section is
> needed to run or develop anything in this repository, and following it sets up
> a PostGIS container the code will never connect to. See
> [`docs/DATABASE_TEARDOWN.md`](DATABASE_TEARDOWN.md).
>
> Kept because Alembic's migration files are still in the tree and someone will
> eventually wonder what they were for.

### Local PostgreSQL with PostGIS

```bash
# Docker (recommended)
docker run -d --name postgres-postgis \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=carbonscan \
  -p 5432:5432 \
  postgis/postgis:16-3.4

# Verify
docker exec -it postgres-postgis psql -U postgres -d carbonscan -c "SELECT PostGIS_Version();"
```

### Migrations (Alembic)

```bash
cd services/api

# Create new migration
alembic revision --autogenerate -m "add trees table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Common Issues & Fixes

### "Module not found" in Python
```bash
# Make sure venv is activated
source services/api/.venv/bin/activate
pip install -e ".[dev]"
```

### Next.js port conflict
```bash
# Use a different port
pnpm --filter web dev -- -p 3001
```

### Flutter "Pod install failed" (iOS)
```bash
cd apps/mobile/ios
pod repo update
pod install
```

### Out of memory training PointNet++
```python
# Reduce batch size
config.batch_size = 4  # was 16

# Use mixed precision
trainer = Trainer(precision='16-mixed')
```

---

## Debugging Tips

### Web (Next.js)
- Browser DevTools + React DevTools
- `console.log` แล้วลบก่อน commit
- VS Code Debug for Server Components

### API (FastAPI)
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- `import pdb; pdb.set_trace()` for interactive debug

### Mobile (Flutter)
- Flutter Inspector ใน VS Code
- `flutter logs`
- Charles Proxy for network debugging

### ML
- Jupyter Lab interactive
- `print(tensor.shape)` everywhere ก่อนอ่าน paper
- TensorBoard: `tensorboard --logdir runs/`

---

## Performance Profiling

### Web
- Lighthouse (Chrome DevTools)
- Bundle Analyzer: `pnpm --filter web analyze`

### API
- `py-spy` for CPU profiling
- `memory_profiler` for memory leaks

### ML
- `torch.profiler` for GPU
- `nvidia-smi -l 1` for VRAM monitoring

---

## Recommended VS Code Extensions

ดู `.vscode/extensions.json` (จะสร้างใน Phase 1)

หลัก:
- ESLint
- Prettier - Code formatter
- Python (Microsoft)
- Pylance
- Ruff
- Flutter
- Dart
- Tailwind CSS IntelliSense
- shadcn/ui
- GitLens
- Error Lens
- markdownlint
- Even Better TOML

---

## Help & Resources

- **Internal:** ถามใน Line/Discord ทีม
- **Docs:** ดู `docs/` หรือ Each app's README
- **External:**
  - Next.js: https://nextjs.org/docs
  - FastAPI: https://fastapi.tiangolo.com/
  - Flutter: https://docs.flutter.dev/
  - PyTorch: https://pytorch.org/docs/
  - lidR: https://github.com/r-lidar/lidR
