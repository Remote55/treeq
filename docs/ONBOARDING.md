# 🚀 Onboarding Guide

> **เป้าหมาย:** อ่านเอกสารนี้ภายใน 30 นาที แล้วเริ่มลงมือทำงานได้
>
> **สำหรับ:** Developer ใหม่ที่เพิ่งเข้าร่วม TreeQ Carbon Platform

---

## ⏱ 30-Minute Plan

| เวลา | กิจกรรม |
|---|---|
| **0-5 min** | อ่าน Section 1 "What is TreeQ Carbon Platform?" |
| **5-10 min** | อ่าน Section 2 "Architecture Quick Tour" |
| **10-15 min** | อ่าน Section 3 "Your Role & First Tasks" |
| **15-25 min** | ทำตาม Section 4 "Local Setup" |
| **25-30 min** | อ่าน Section 5 "Tools & Communication" |

---

## 1. What is TreeQ Carbon Platform?

### One-liner
ระบบประเมิน Carbon Credit จากต้นไม้แบบโปร่งใส โดยใช้ LiDAR 3D Point Cloud + AI

### Problem
- **เกษตรกร** มีต้นไม้แต่ขาย Carbon Credit ไม่ได้ เพราะค่าจ้าง Auditor แสน-ล้านบาท
- **โรงงาน** จ่ายเงินทำ CSR แต่ตรวจสอบผลลัพธ์ไม่ได้ เสี่ยงข้อหา Greenwashing
- **Auditor** ใช้เวลาเดินป่าวัด DBH ต้นไม้ทีละต้นด้วยสายวัด — ช้า แพง คลาดเคลื่อน

### Our Solution
**Platform 3 ส่วน:**

```
1. Mobile App  → ถ่ายภาพต้นไม้ + GPS → ส่งขึ้น Cloud
2. Backend     → ประมวลผล LiDAR/Photo → คำนวณ Carbon
3. Web Dashboard → ดูผลลัพธ์ 3D + แผนที่ + ซื้อ Carbon Credit
```

### Why It Wins NSC 2026
- ✅ **Deep Tech** (3D Point Cloud + Deep Learning)
- ✅ **Triple Helix Impact** (Industry + Society + Government)
- ✅ **Trendy** (ESG, CBAM, Climate FinTech)
- ✅ **Demo-able** (มี Live 3D Viewer ที่กรรมการเห็นได้ทันที)

📖 อ่านเพิ่ม: [README.md](../README.md), [proposal/outline.md](../proposal/outline.md)

---

## 2. Architecture Quick Tour

```
┌──────────────────────┐    ┌──────────────────────┐
│   Mobile (Flutter)   │    │  Web (Next.js)       │
│   - ถ่ายภาพ + GPS    │    │  - 3D Viewer         │
│   - Species ID       │    │  - GIS Map           │
└──────────┬───────────┘    │  - Marketplace       │
           │                └──────────┬───────────┘
           │  HTTPS                    │
           └───────────┬───────────────┘
                       ▼
           ┌──────────────────────┐
           │   API (FastAPI)      │
           │   - Auth + REST      │
           │   - Job orchestration│
           └──────────┬───────────┘
                      ▼
           ┌──────────────────────┐
           │   Job Queue          │
           └──────────┬───────────┘
                      ▼
           ┌──────────────────────┐
           │  GPU Worker (RunPod) │
           │  1. Ground class.    │
           │  2. Tree segment     │
           │  3. Wood-leaf AI     │
           │  4. QSM volume       │
           │  5. Allometric → C   │
           └──────────────────────┘
```

📖 ละเอียด: [docs/ARCHITECTURE.md](ARCHITECTURE.md)

---

## 3. Your Role & First Tasks

### 👤 Person A — Frontend / Web Engineer

**You own:** `apps/web/`, `packages/ui/`, `packages/types/`

**First 3 tasks (Day 1-3):**
1. Setup Next.js 14 boilerplate ใน `apps/web/` (ดู [apps/web/README.md](../apps/web/README.md))
2. Implement Landing Page + Routing
3. Setup Tailwind + shadcn/ui

**Read these docs:**
- [apps/web/README.md](../apps/web/README.md)
- [apps/web/PERSON_A_GUIDE.md](../apps/web/PERSON_A_GUIDE.md)
- [docs/API.md](API.md) (สำหรับ Backend integration)

---

### 🎨 Person B — UI/UX Designer

**You own:** `packages/design-tokens/`, `assets/brand/`, `docs/design/`

**First 3 tasks (Day 1-3):**
1. ออกแบบ Logo + Brand Direction (Forest Green + Sky Blue)
2. ทำ Wireframe ของ Web Dashboard ใน Figma
3. Export Design Tokens (colors, typography, spacing) เป็น JSON ใน `packages/design-tokens/`

**Read these docs:**
- [packages/design-tokens/README.md](../packages/design-tokens/README.md)
- [docs/design/DESIGN_SYSTEM.md](design/DESIGN_SYSTEM.md)
- [docs/design/BRAND.md](design/BRAND.md)

---

### 🧠 User — Lead / AI / Mobile / Backend

**You own:** `apps/mobile/`, `services/api/`, `services/ml/`, `proposal/`

**First 3 tasks (Day 1-3):**
1. ร่าง Proposal v1 (8-10 หน้า)
2. Research สูตร TGO Allometric + Wood Density 5 ชนิดต้นไม้
3. Setup `services/ml/` Python environment + Download NEON sample dataset

**Read these docs:**
- [services/ml/README.md](../services/ml/README.md)
- [services/api/README.md](../services/api/README.md)
- [apps/mobile/README.md](../apps/mobile/README.md)
- [docs/ml/PIPELINE.md](ml/PIPELINE.md)

---

## 4. Local Setup

### Prerequisites
ติดตั้งให้ครบก่อนเริ่ม:

| Tool | Version | Required For |
|---|---|---|
| **Node.js** | ≥ 20 | Web Dashboard, packages |
| **pnpm** | ≥ 9 | Package manager |
| **Python** | 3.11 | API + ML |
| **Flutter** | 3.x | Mobile |
| **Git** | ≥ 2.40 | Version control |
| **Docker** | latest | (Optional) Local services |
| **VS Code** | latest | Recommended IDE |

### Step-by-Step

```bash
# 1. Clone repo
git clone https://github.com/Remote55/treeq.git
cd treeq

# 2. Install Node dependencies
pnpm install

# 3. Setup Python for API
cd services/api
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows
pip install -e .[dev]
cd ../..

# 4. Setup Python for ML
cd services/ml
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cd ../..

# 5. Setup Flutter (Mobile)
cd apps/mobile
flutter pub get
cd ../..

# 6. Copy env files
cp services/api/.env.example services/api/.env
cp apps/web/.env.example apps/web/.env.local
# แก้ค่าใน .env (ขอจาก User)

# 7. Run dev environment
pnpm dev   # รัน Web + API พร้อมกัน
```

📖 ละเอียด: [docs/DEVELOPMENT.md](DEVELOPMENT.md)

---

## 5. Tools & Communication

### Communication Channels
- **Line/Discord:** ทีม chat (ขอ link จาก User)
- **GitHub Issues:** Bug tracking + Feature requests
- **GitHub Discussions:** Architectural discussions
- **Figma:** Design files (link จาก Person B)

### Required Accounts
- [ ] GitHub account (add ssh key)
- [ ] Vercel account (สำหรับ Person A)
- [ ] Supabase account
- [ ] Hugging Face account (สำหรับ User — model hosting)

### Recommended VS Code Extensions
```
# Universal
- EditorConfig
- Prettier
- GitLens

# Web
- ESLint
- Tailwind CSS IntelliSense
- Auto Rename Tag

# Python
- Python
- Pylance
- Ruff
- Black Formatter

# Flutter
- Flutter
- Dart

# Markdown
- Markdown All in One
- markdownlint
```

---

## 6. Key Documents To Bookmark

| Document | When to Read |
|---|---|
| [README.md](../README.md) | First |
| [docs/ARCHITECTURE.md](ARCHITECTURE.md) | Before coding |
| [docs/ROADMAP.md](ROADMAP.md) | Weekly check |
| [docs/DEVELOPMENT.md](DEVELOPMENT.md) | When setup issues |
| [docs/decisions/](decisions/) | When confused about "why X?" |
| [TASKS.md](../TASKS.md) | Daily |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Before first PR |

---

## 7. FAQ

### Q: "ทำไมเราไม่ใช้ iPhone LiDAR?"
A: ทีมไม่มี → Pivot ไปใช้ Photogrammetry + Public LiDAR Dataset แทน
ดู [docs/decisions/0002-no-iphone-lidar.md](decisions/0002-no-iphone-lidar.md)

### Q: "ทำไม Flutter ไม่ใช่ React Native?"
A: Flutter render performance ดีกว่าสำหรับ camera-heavy apps + cross-platform ที่ดีกว่า
ดู [docs/decisions/0003-tech-stack-selection.md](decisions/0003-tech-stack-selection.md)

### Q: "Deadline จริง ๆ คือเมื่อไหร่?"
A:
- **29 พ.ค. 2569 17:00** ส่ง Proposal
- **17 ก.ค. 2569 17:00** ส่งงานสมบูรณ์
- **21 ส.ค. 2569** รอบชิงชนะเลิศ

### Q: "ถ้าติดปัญหาควรทำยังไง?"
1. ค้นใน `docs/`
2. Search ใน GitHub Issues
3. ถามใน Line/Discord ทีม
4. Tag User สำหรับเรื่อง architectural

### Q: "ต้องการเงินจ่ายค่า Cloud GPU ไหม?"
A: ใช้ Free tier ของ Colab/Kaggle เป็นหลัก. RunPod ใช้ตอน production demo เท่านั้น (~$10/เดือน)

---

## ✅ Onboarding Checklist

หลังอ่านเอกสารนี้ ให้เช็คทีละข้อ:

- [ ] เข้าใจปัญหาที่โปรเจกต์แก้
- [ ] เห็น Architecture ภาพรวม
- [ ] รู้ว่าตัวเองรับผิดชอบ folder ไหน
- [ ] Setup environment สำเร็จ (run `pnpm dev` ได้)
- [ ] เข้า Line/Discord ทีมแล้ว
- [ ] Clone repo + create branch แรกได้
- [ ] อ่าน [TASKS.md](../TASKS.md) แล้วเห็นงานของตัวเอง

**ยินดีต้อนรับสู่ TreeQ Carbon Platform! 🌲**
