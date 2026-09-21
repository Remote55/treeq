# AGENTS.md — TreeQ Carbon Platform

> ไฟล์นี้โหลดเข้า context อัตโนมัติ (Codex/Claude/agent อื่น) ทุกครั้งที่เปิด repo นี้
> **ภาษา:** ตอบผู้ใช้เป็น **ภาษาไทย** (technical terms เป็น EN ได้) · ผู้ใช้เป็น team lead (นักศึกษา)

---

## 👉 อ่านก่อนเริ่มงานเสมอ

**`docs/PROJECT_SPEC.md`** = context ฉบับเต็ม (23 numbered sections: §0–§22) — อธิบายทั้งโปรเจกต์: pipeline, allometric,
backend, web, สถานะจริง, known bugs, roadmap. **อ่านไฟล์นั้นก่อนแตะโค้ด**

เอกสารนี้ (AGENTS.md) = orientation สั้นๆ + คำสั่ง build/run/test + กติกา

---

## โปรเจกต์คืออะไร (1 ย่อหน้า)

**TreeQ Carbon Platform** (เดิมชื่อ *CarbonScan AI*) — prototype ประเมินคาร์บอนชีวมวลต้นไม้จาก **3D point cloud**
ด้วย `tlsep` baseline แยก **ลำต้น(wood)/ใบ(leaf)** → วัด **DBH + ความสูง** → คำนวณ
**ชีวมวล→carbon stock→CO₂e estimate** จาก `species_db.csv` หรือ Chave fallback พร้อม provenance
ส่วน PointNet++, photogrammetry, marketplace และ certification ต้องรายงานตามสถานะ Experimental/Planned
เป้าหมายปัจจุบัน: **ถูกวิทยาศาสตร์ ตีพิมพ์ได้ และใช้งานได้จริง** — ดู CLAUDE.md

---

## โครงสร้าง Monorepo

```
apps/web/        Next.js 14 (App Router, TS, Tailwind, shadcn) — landing + dashboard + 3D viewer
services/api/    FastAPI (SQLAlchemy async, asyncpg, Pydantic v2, Alembic) — REST + async-job worker
services/ml/     Point-cloud pipeline — tlsep default, PointNet++ Experimental, 8-step pipeline + allometric
docs/            เอกสาร (PROJECT_SPEC.md, ml/, learning/, decisions/, superpowers/)
proposal/        เอกสารข้อเสนอฉบับเดิม (historical)
memory/          project memory
```

---

## Build / Run / Test (ต่อ service)

### Web (`apps/web`)
```bash
npm install
npm run dev            # ต้องมี NEXT_PUBLIC_SUPABASE_URL + ANON_KEY ใน .env.local
                       #   (ถ้าไม่มี middleware จะข้าม auth ให้ dev เปิดได้ — ดู middleware.ts)
npm run build          # gate ก่อน deploy เสมอ
npx tsc --noEmit       # typecheck
npm run lint
npx vercel --prod --archive=tgz --yes   # deploy → treeqcarbon.vercel.app
```

### API (`services/api`)
```bash
python -m venv .venv && .venv/Scripts/activate     # Windows (หรือ source .venv/bin/activate)
pip install -e .        # หรือ requirements
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pytest                  # 79 tests
```

### ML (`services/ml`)
```bash
python -m venv .venv && .venv/Scripts/activate
pip install -e .
pytest tests/           # allometric 15+ tests ฯลฯ
# sanity check คาร์บอน:
python -c "from pipeline.allometric import calculate_carbon; print(calculate_carbon(30,18,'Tectona grandis').co2eq_kg)"  # ~1233
# pipeline เต็ม: ดู services/ml/pipeline/main.py + services/api/app/services/pipeline_runner.py
```

---

## กติกา / Conventions (สำคัญ — กันพลาดซ้ำ)

1. **Web landing = Tailwind + server component เท่านั้น** — **ห้าม** styled-jsx หรือ canvas 3D
   (styled-jsx ไม่ SSR ใน App Router → เรนเดอร์ unstyled บน prod มาแล้ว)
2. **Vercel env var** ต้องตั้งด้วย `vercel env add NAME production --value "<v>" --no-sensitive --force --yes`
   (pipe/stdin ได้ค่าว่างเมื่อ agent รัน CLI)
3. **ห้าม emoji ใน `print()` ของ Python บน Windows** (cp874 → uvicorn crash) — ใช้ ASCII
4. **3D viewer:** vertex color ต้องแปลง sRGB→linear ด้วย `THREE.Color` (ไม่งั้นสีเพี้ยน)
5. **Honesty ethos:** รายงานตัวเลขจริง + ข้อจำกัด ห้าม oversell (Wood IoU = `0.418`; ห้ามปัดเป็น marketing claim)
6. **species_db.csv** = source of truth ค่า allometric · **โค้ดคือความจริง** เอกสารเป็น target
7. อย่าทับไฟล์ report ต้นฉบับ — เซฟเป็นไฟล์ใหม่เสมอ

---

## สถานะปัจจุบัน (2026-07-16)

**✅ เสร็จ:** ML core path ขั้น 1–6/8 (species ขั้น 7 = Stub), allometric tests, deterministic `tlsep`
core demo พร้อม hashes/provenance, backend sync+async-job, web landing และ 3D viewer ที่แสดง typed provenance

**หลักฐานที่ต้องพูดครบ:** PointNet++ = Experimental; Wan held-out Wood IoU `0.418`, Leaf IoU `0.808`,
Mean IoU `0.613`, accuracy `0.831` และ held-out loader ถูกใช้เลือก best epoch ด้วย · Demol isolated-tree
65 ต้น DBH MAE `0.898318 cm`, Height MAE `0.543323 m`, Volume MAPE `11.520556%`;
ผล Demol ไม่ใช่ full-pipeline/allometric/carbon validation

**⚠️ ค้าง:**
- Rebrand core surface แล้ว · เหลือ legacy docs/proposal/GitHub-repo-name/logo assets
- Species classifier (ขั้น 7) = stub → ต้องเทรน ResNet จริง
- PointNet++ promotion = ต้องมี verified checkpoint/training provenance, independent real test และ DBH/height/volume non-regression
- Dataset: research+verify open dataset เพิ่มตามคำสั่งอาจารย์ แล้วสร้าง independent final split
- Deploy API+worker จริง (RunPod/Railway) — ตอนนี้ demo ผ่าน Cloudflare tunnel
- verify allometric coefficients กับ TGO Guideline 2017

---

## สิ่งที่ทำร่วมกันมาล่าสุด (session changelog — ให้ Codex เข้าใจ context ต่อเนื่อง)

เรียงใหม่→เก่า (ดู `git log` ประกอบ):
1. **Master spec** `docs/PROJECT_SPEC.md` (d033ed0) — เอกสาร context ฉบับเต็ม
2. **Rebrand → TreeQ Carbon Platform** บน web (aa1ea85) — verify live แล้ว
3. **Rebuild landing เป็น nature-template** Tailwind ไม่มี 3D (68f168b) — แก้บั๊ก styled-jsx ที่เรนเดอร์พังบน prod
4. **Premium landing เดิม (3D canvas)** (bcbeb3a) — *ถูกแทนแล้ว* แต่เป็นที่มาของบทเรียน styled-jsx
5. **แก้ emoji crash** uvicorn บน Windows (6ca8693)
6. **Async-job backend** (Phase 2) — *ถูกถอดออกแล้ว* ไม่มีผู้เรียกและไม่มี deployment ใดสตาร์ท worker; `/jobs/analyze` ตอบ 202 queued ให้งานที่รันไม่ได้
7. **Dataset pivot** — อาจารย์ให้ใช้ open dataset เทรน wood-leaf (เลิกเก็บไม้ไทยเอง)
8. **Wire web viewer → analyze API** + Supabase token (dbcb6df)

> เอกสารเชิงลึกเพิ่มเติม: `docs/ml/PIPELINE.md`, `docs/ml/ALLOMETRIC.md`, `docs/ml/WOODLEAF_RESULTS.md`,
> `docs/superpowers/plans/2026-07-10-async-job-pipeline.md`

---

## Deployment

| ส่วน | Prod | Demo |
|---|---|---|
| Web | Vercel `treeqcarbon.vercel.app` | เหมือนกัน |
| API+ML | (target Railway/RunPod GPU) | Cloudflare quick tunnel → local API |
| DB/Auth | Supabase | เหมือนกัน |

สคริปต์เปิด backend demo: `C:\Users\Acer\OneDrive\Desktop\CarbonScrip\start_backend.bat`

---

## Preferences ของผู้ใช้

- ตอบ **ภาษาไทย** (technical terms EN ได้)
- **ความถูกต้องมาก่อนความน่าประทับใจ** — กรอบ "ทำให้กรรมการว้าว" เลิกใช้แล้ว
- **อย่า over-engineer** — prototype ที่เสร็จ > vision สมบูรณ์แต่ไม่เสร็จ
- ทุก decision ที่มีค่าใช้จ่าย → "นักศึกษาจ่ายไหวไหม"
- verify ก่อนเคลม — รันจริง/ดูผลจริง อย่าเดา
