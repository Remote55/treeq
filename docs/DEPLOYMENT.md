# 🚀 Deployment Guide

> [!CAUTION]
> **Deployment plan, not proof of production deployment.** Web อยู่บน Vercel แต่ API/ML worker
> ที่ตรวจสอบล่าสุดเป็น local service ผ่าน temporary tunnel; RunPod/Railway production worker
> และ object-storage handoff ยัง Planned. ค่าใช้จ่ายและขั้นตอนด้านล่างเป็นประมาณการ/target
> และต้องตรวจราคาปัจจุบันก่อนตัดสินใจ. ดู `docs/PROJECT_SPEC.md`.

> Production deployment for TreeQ Carbon Platform

---

## Deployment Targets

> [!IMPORTANT]
> **Only the first row exists.** The rest of this table has always been a plan,
> and three of its URLs resolve to nothing. It is kept as the intended shape
> rather than deleted, but nothing below the web row should be read as
> describing something you can visit today.

| Component | Platform | URL | Status |
|---|---|---|---|
| **Web (Next.js)** | Vercel | `https://treeqcarbon.vercel.app` | **Live** |
| **API (FastAPI)** | — | — | **Not deployed.** `NEXT_PUBLIC_API_URL` is unset in production, so the site runs its browser-side work and says the carbon step is unavailable. The Railway URL this table used to name never existed. |
| **Database** | — | — | **Removed.** The database layer was deleted; no table backs the API. See `docs/DATABASE_TEARDOWN.md`. |
| **Auth / Storage** | Supabase | `*.supabase.co` | Live, $0 |
| **ML GPU Worker** | RunPod Serverless | Endpoint URL | ~$6-15 (usage) |
| **Mobile APK** | GitHub Releases | Artifact | $0 |
| **Mobile IPA** | (Optional) Codemagic | TestFlight | $0 (Free tier) |

**Total: ~$11-20/month**

---

## 1. Web Dashboard (Vercel)

### Initial Setup
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from apps/web
cd apps/web
vercel
# Follow prompts → connect to GitHub repo

# Set production env vars in Vercel dashboard:
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY
# - NEXT_PUBLIC_API_URL is deliberately left unset - no public API deployment exists
```

### Auto-deploy on push
GitHub integration → ทุก commit on `main` deploys to production.

### Custom Domain (Optional)
- Buy domain (e.g., Cloudflare Registrar ~$10/year)
- Add CNAME → cname.vercel-dns.com
- Vercel auto-generates SSL

---

## 2. Backend API (Railway)

### Initial Setup
1. Sign up at railway.app (use GitHub login)
2. New Project → Deploy from GitHub Repo → select `treeq`
3. Set **Root Directory:** `services/api`
4. Set **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (from `.env.example`)
6. Generate public domain

### Database URL
ใช้ Supabase connection string:
```env
DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

### Health Check
Railway pings `/health` every 30s. Make sure FastAPI has:
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

### Logs
```bash
railway logs --tail
```

---

## 3. Database & Storage (Supabase)

### Initial Setup
1. Create project at supabase.com (free tier)
2. Region: **Southeast Asia (Singapore)** for low latency
3. Note credentials:
   - Project URL
   - Anon key (public, for Web)
   - Service role key (secret, for API)

### Enable PostGIS
SQL Editor → run:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_Version();
```

### Run Migrations
```bash
# From local machine
cd services/api
alembic upgrade head
```

หรือ Supabase SQL Editor → paste schema directly

### Storage Buckets
สร้าง 3 buckets:
- `point-clouds` (private) — .las/.laz/.ply
- `photos` (private) — JPG/PNG
- `reports` (public) — PDF reports

### Row-Level Security (RLS)
Enable RLS บนทุก table → กำหนด policies:
```sql
-- Trees: users see own + public marketplace
CREATE POLICY "Users see own trees"
ON trees FOR SELECT
USING (owner_id = auth.uid());

CREATE POLICY "Public can see available trees"
ON trees FOR SELECT
USING (is_available = TRUE AND verified_at IS NOT NULL);
```

---

## 4. ML GPU Worker (RunPod Serverless)

### Build Docker Image
```bash
cd services/ml
docker build -f Dockerfile.gpu -t carbonscan-ml:latest .
docker tag carbonscan-ml:latest <your-dockerhub>/carbonscan-ml:latest
docker push <your-dockerhub>/carbonscan-ml:latest
```

### Create Serverless Endpoint
1. RunPod dashboard → Serverless → New Endpoint
2. Container image: `<your-dockerhub>/carbonscan-ml:latest`
3. GPU: **NVIDIA A10G 24GB** (good balance)
4. Container disk: 20GB
5. Volume: 50GB (for model weights)
6. Min workers: 0 (scale to zero when idle)
7. Max workers: 3
8. Idle timeout: 30s
9. Note **Endpoint ID** → add to API env

### Test
```bash
curl -X POST https://api.runpod.ai/v2/<endpoint-id>/runsync \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" \
  -d '{
    "input": {
      "las_url": "https://...test.las"
    }
  }'
```

### Cost Optimization
- Set `Idle timeout: 5s` for short jobs
- Use spot pricing if available
- Pre-warm worker if expected traffic

---

## 5. Mobile App

### Android APK
```bash
cd apps/mobile

# Release build
flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Sign APK
```bash
# Generate keystore (once)
keytool -genkey -v -keystore ~/upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias upload

# Configure android/app/build.gradle.kts
# (See Flutter docs for full signing setup)

flutter build apk --release
```

### Upload to GitHub Releases
```bash
gh release create v1.0.0 \
  build/app/outputs/flutter-apk/app-release.apk \
  --title "CarbonScan AI v1.0.0" \
  --notes "First public release"
```

### iOS IPA (Optional, via Codemagic)
- Sign up at codemagic.io
- Connect GitHub repo
- Configure `codemagic.yaml`:
```yaml
workflows:
  ios-workflow:
    name: iOS Build
    instance_type: mac_mini_m1
    integrations:
      app_store_connect: codemagic
    scripts:
      - flutter pub get
      - flutter build ios --release --no-codesign
    artifacts:
      - build/ios/iphoneos/*.app
```

---

## CI/CD Pipeline (GitHub Actions)

### `.github/workflows/ci-web.yml`
```yaml
name: CI Web

on:
  push:
    paths: ['apps/web/**', 'packages/**']
  pull_request:
    paths: ['apps/web/**', 'packages/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter web lint
      - run: pnpm --filter web build
      - run: pnpm --filter web test
```

### `.github/workflows/ci-api.yml`
```yaml
name: CI API

on:
  push:
    paths: ['services/api/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e "services/api[dev]"
      - run: ruff check services/api
      - run: cd services/api && pytest
```

---

## Pre-Deployment Checklist

### Web
- [ ] `pnpm build` ผ่าน
- [ ] Lighthouse score > 80
- [ ] No `console.log` ใน production code
- [ ] Env vars set ครบใน Vercel
- [ ] Sitemap + robots.txt
- [ ] OG images for social sharing

### API
- [ ] `/health` endpoint works
- [ ] Swagger docs accessible
- [ ] CORS configured ถูกต้อง
- [ ] Rate limiting enabled
- [ ] Error logging (Sentry recommended)
- [ ] Database migrations applied
- [ ] Secrets ใน Railway, ไม่ใช่ใน code

### Database
- [ ] RLS policies on ทุก table
- [ ] Indexes สร้างครบ
- [ ] Backups enabled (Supabase auto)
- [ ] PostGIS extension enabled

### ML Worker
- [ ] Docker image < 10GB
- [ ] Model weights downloaded in image (not at runtime)
- [ ] Idle timeout set
- [ ] Memory limit set (24GB for A10G)
- [ ] Logs accessible

### Mobile
- [ ] App icon set
- [ ] Splash screen
- [ ] Permissions in manifest (camera, location)
- [ ] Signed APK
- [ ] Tested on real device

---

## Rollback Strategy

### Web (Vercel)
- Vercel keeps last 10 deployments
- Dashboard → Deployments → "Promote to Production"

### API (Railway)
- Railway keeps deploy history
- CLI: `railway redeploy <deploy-id>`

### Database
- Migrations reversible: `alembic downgrade -1`
- Critical changes: snapshot first

---

## Monitoring

### Recommended Free Tools
- **Vercel Analytics** (built-in, Web Vitals)
- **Sentry** (5K errors/month free) — error tracking
- **Supabase Dashboard** — DB metrics
- **Railway Metrics** — API CPU/memory
- **RunPod Console** — GPU usage

### Alerts
- API down > 1 min → email
- Error rate > 5% → email
- DB CPU > 80% sustained → email
- Cloud GPU bill > $30/mo → email

---

## Cost Tracking

ติดตามใน Google Sheets `Carbon Scan Costs.xlsx`:

| Month | Vercel | Railway | Supabase | RunPod | Total |
|---|---|---|---|---|---|
| มิ.ย. | $0 | $5 | $0 | $3 | $8 |
| ก.ค. | $0 | $5 | $0 | $12 | $17 |
| ส.ค. | $0 | $5 | $0 | $25 | $30 |

**Budget cap:** $30/month — ถ้าใกล้เกิน → review usage + optimize

---

📖 **See also:**
- [docs/DEVELOPMENT.md](DEVELOPMENT.md) — Local development
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [docs/decisions/0005-cloud-gpu-strategy.md](decisions/0005-cloud-gpu-strategy.md) — Why RunPod
