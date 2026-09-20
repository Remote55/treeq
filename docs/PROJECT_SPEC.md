# TreeQ Carbon Platform — Master Project Spec

> **จุดประสงค์ของเอกสารนี้:** เป็น "context ก้อนเดียวจบ" สำหรับเปิด session ใหม่ (Claude หรือคนใหม่ในทีม)
> อ่านจบแล้วต้องเข้าใจว่า **เรากำลังทำอะไร, ทำถึงไหน, ตัดสินใจอะไรไปแล้ว, และเหลืออะไร**
> อัปเดตล่าสุด: **2026-07-16** · เขียนโดย AI จากการอ่านโค้ด/เอกสารจริงในโปรเจกต์
> ⚠️ ตัวเลข/สถานะในเอกสารนี้เป็น ณ วันที่เขียน — ก่อนอ้างอิงให้ verify กับโค้ดปัจจุบันอีกครั้ง

---

<!-- TREEQ_TRUTH_START -->
### Verified truth snapshot (generated)

- Baseline: `tlsep` — **Implemented**.
- PointNet++: **Experimental**, not promoted; reviewed evidence never changes the default automatically.
- Wan 2021 held-out: Wood IoU `0.418`, Leaf IoU `0.808`, Mean IoU `0.613`, accuracy `0.831`. The held-out loader was also used for best-epoch selection.
- Demol isolated-tree validation (65 trees): DBH MAE `0.898318 cm`; Volume MAPE `11.520556%`. This is not an eight-stage or carbon validation.
- Independent PointNet review: verdict `FAIL_METRICS`; candidate/baseline external macro Wood IoU `0.23728726507501768`/`0.1958779956856453`.
- Independent downstream candidate/baseline: DBH MAE `1.1591405814498605`/`1.1339476465903928` cm; Height MAE `0.9508502244897976`/`0.5433234000000015` m; Volume MAPE `21.74924193798788`/`18.928262273343613`%; measurable trees `49`/`65`.
- Deterministic core demo: `3` trees, `1036.09 kg C`, `3798.99 kg CO2e`; analyzed commit `8cf3058c1f61` with a clean worktree.
- Species classification: **Stub**. Carbon stock/CO2e estimates are not certified credits.
<!-- TREEQ_TRUTH_END -->

## 0. วิธีใช้เอกสารนี้ (สำหรับ session ใหม่)

1. อ่าน §1 (TL;DR) + §17 (สถานะ) ก่อน จะเห็นภาพรวมเร็วสุด
2. งานโค้ด → ดู §7 (โครงสร้าง repo) + §9–16 (แต่ละส่วน)
3. งานวิทยาศาสตร์/คาร์บอน → §10–11
4. อย่าเพิ่งเชื่อทุกอย่าง — ไฟล์จริงคือ source of truth เสมอ (เอกสารบางส่วนเขียนเป็น "target" ไม่ใช่ "สิ่งที่ทำเสร็จ" — §17 บอกความจริง)

---

## 1. TL;DR (Elevator Pitch)

**TreeQ Carbon Platform** = prototype ประเมิน **คาร์บอนชีวมวลต้นไม้** จาก **3D point cloud**
พร้อม provenance และ 3D viewer โดยมี **B2B carbon offset matchmaking เป็น Planned roadmap**

Pipeline ที่รันได้ตอนนี้รับ point cloud (`.las/.laz/.ply`) → แยก **ลำต้น (wood) ออกจากใบ (leaf)**
→ วัด **DBH + ความสูง** → คำนวณ **ชีวมวล → carbon stock → CO₂e estimate** จาก
`species_db.csv` หรือ Chave 2014 fallback พร้อม provenance; เส้นทางภาพถ่ายมือถือ/photogrammetry ยังเป็น Planned
และ coefficients ยังต้อง verify กับ TGO 2017 ต้นฉบับ

**จุดขายต่อกรรมการ NSC:** Deep Tech (point cloud + deep learning) + Visual storytelling (3D viewer)
+ ความ "ซื่อสัตย์เชิงวิศวกรรม" (รายงานตัวเลขจริงพร้อมข้อจำกัด ไม่เคลม overselling)

---

## 2. บริบทการแข่งขัน (NSC 2026)

| หัวข้อ | รายละเอียด |
|---|---|
| งาน | **NSC 2026** (National Software Contest ครั้งที่ 28) |
| หมวด | **หมวด 14** — โปรแกรมเพื่องานการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี |
| ระดับ | อุดมศึกษา (ปริญญาตรี) |
| Deadline | Proposal: **29 พ.ค. 2569** · Final Report: **17 ก.ค. 2569** |
| กติกาเสี่ยง | ระบบปิดอัตโนมัติ 17:00 น. — ห้ามเลท · ต้องเดินลายเซ็นที่ปรึกษา + คณบดี (ใช้เวลา 2–3 วัน) |

---

## 3. ทีม

| Role | ผู้รับผิดชอบ | โฟกัส |
|---|---|---|
| **Lead / Core** | User (เจ้าของ repo) | AI/ML, Backend (FastAPI), Team Lead, Proposal |
| **Frontend** | Person A | Next.js Web Dashboard, 3D Viewer; GIS Map เป็น Planned |
| **Design** | Person B | UI/UX (Figma), Branding, Video, Slides |

> ทีมเป็นนักศึกษา — ไม่มีงบซื้อ hardware แพง, ไม่มี iPhone LiDAR, ไม่มี GPU แรง → ทุก decision ต้องดู "นักศึกษาจ่ายไหวไหม"

---

## 4. ตัวโปรดักต์ (ปัญหา → ทางแก้ → คุณค่า)

**ปัญหา:** การประเมินคาร์บอนป่าไม้แบบเดิมต้องใช้ผู้เชี่ยวชาญเดินวัดต้นไม้ทีละต้น (DBH ด้วยสายวัด, ความสูงด้วย clinometer)
→ แพง, ช้า, สเกลไม่ได้, ตรวจสอบย้อนหลังยาก

**ทางแก้และสถานะ:**
1. **Point-cloud carbon assessment — Implemented core path:** วัด geometry และคำนวณค่าประมาณคาร์บอน
2. **Wood-Leaf Segmentation:** `tlsep` เป็น Implemented baseline; PointNet++ เป็น Experimental candidate
3. **3D evidence viewer — Implemented:** แสดง segmented PLY และ provenance ของ analysis run
4. **GIS / anti-fraud / B2B marketplace / certification — Planned** · mobile กับ photogrammetry **ถูกลบทิ้งแล้ว** (ADR 0007)

**คุณค่าที่เคลมได้ตอนนี้:** ทำให้ขั้นคำนวณและ provenance เปิดตรวจสอบได้ใน prototype
ยังไม่มี controlled cost study, production SLA หรือกระบวนการรับรอง carbon credit จึงไม่เคลมลดต้นทุน 100 เท่า

---

## 5. Branding ⚠️ (เปลี่ยนชื่อแล้ว)

- **ชื่อปัจจุบัน: `TreeQ Carbon Platform`** (ทีมตัดสินใจ 2026-07-16)
- **ชื่อเดิม `CarbonScan AI` = historical name** — ยังหลงเหลือใน legacy docs/code metadata บางส่วน
- rebrand core surface แล้วใน **apps/web**, README, master spec และ ML docs
- **GitHub repo เปลี่ยนเป็น `Remote55/treeq` แล้ว** 23 ส.ค. 2569 · slug เก่ายัง redirect อยู่
  (ทดสอบแล้ว: ทั้ง CI badge และ shields.io ตาม redirect ได้) แต่ redirect จะตายทันที
  ถ้ามีใครสร้าง repo ชื่อ `Remote55/carbonscan-ai` ขึ้นมาทับ
- **ยังไม่ rebrand ครบ:** package identifier ในโค้ด
  (`carbonscan-api`, `carbonscan-ml`, `@carbonscan/*`, bucket `carbonscan-uploads`)
  · เอกสาร historical และ ADR **ตั้งใจไม่แก้** เพราะการแก้บันทึกย้อนหลังคือการปลอมบันทึก
  · brand assets แก้แล้ว — โลโก้ไม่มี wordmark จึงย้ายมาใช้ได้ทั้งดุ้น
- Logo bug: `apps/web/public/logo.png` เป็นโลโก้เดิม — ยังไม่เปลี่ยน

---

## 6. Tech Stack

| ชั้น | เทคโนโลยี |
|---|---|
| **Web** | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + React Three Fiber/Three.js (3D viewer); Leaflet/GIS เป็น Planned surface |
| ~~**Mobile**~~ | ลบทิ้งแล้วตาม ADR 0007 — ดูหัวข้อ 15 |
| **Backend** | FastAPI (Python) + SQLAlchemy 2.0 async + asyncpg + Pydantic v2 + Alembic + PostgreSQL/PostGIS + Supabase |
| **AI/ML** | NumPy/SciPy/scikit-image + laspy + PyTorch PointNet++ Experimental; PDAL CSF และ COLMAP/OpenMVS เป็น target ไม่ใช่ default path |
| **Cloud** | Vercel (web) + Supabase; Railway/RunPod เป็น target และ API demo ใช้ local backend ผ่าน temporary tunnel |

---

## 7. โครงสร้าง Monorepo

```
D:\Project_Carbon\
├── apps/
│   ├── web/                    Next.js — เว็บ dashboard + landing + 3D viewer
│   │   └── src/
│   │       ├── app/            (App Router) page.tsx=landing, layout.tsx, (auth)/ (dashboard)/
│   │       ├── components/     viewer/point-cloud-viewer.tsx ฯลฯ
│   │       ├── lib/            api.ts (API client), supabase.ts, utils.ts
│   │       └── middleware.ts   Supabase session refresh + guard
├── services/
│   ├── api/                    FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py         entrypoint (lifespan, CORS)
│   │   │   ├── api/v1/         router.py, health.py, auth.py, trees.py, upload.py, jobs.py
│   │   │   ├── api/deps.py     DI (get_db, CurrentUser)
│   │   │   ├── models/         user.py (SQLAlchemy ORM; ไม่มีโค้ดอ่าน/เขียนตารางแล้ว)
│   │   │   ├── schemas/        Pydantic: auth, tree, analyze
│   │   │   ├── services/       pipeline_runner.py, upload_validation.py,
│   │   │   │                   segmented_cloud_store.py, species_catalogue.py, supabase.py
│   │   │   └── core/           config.py, database.py, exceptions.py
│   │   (ไม่มี alembic/ และ models/ แล้ว — ไม่มีฐานข้อมูล ดู docs/DATABASE_TEARDOWN.md)
│   └── ml/                     PyTorch pipeline (heavy deps)
│       ├── pipeline/           8-step pipeline (ดู §9) + main.py orchestrator + allometric.py
│       ├── training/           woodleaf_dataset.py, realdata_dataset.py, train_woodleaf.py
│       ├── data/               species_db.csv (source of truth ค่า allometric)
│       ├── tests/              pytest (allometric 15+, realdata, ฯลฯ)
│       └── notebooks/          Colab notebooks (fine-tune, diagrams, e2e)
├── docs/                       เอกสารทั้งหมด (ml/, learning/, decisions/, proposal/, superpowers/)
├── proposal/                   NSC proposal (outline.md, advisor_email.md)
├── memory/                     project memory (context/, projects/, glossary)
├── assets/brand/               โลโก้/แบรนด์
└── CLAUDE.md                   working memory (โหลดเข้า context อัตโนมัติ)
```

---

## 8. สถาปัตยกรรมระบบ

### Input status (decision 0004 เป็น target)
1. **Point-cloud upload — Implemented:** `.las/.laz/.ply` และ text formats ที่ loader รองรับ
2. **Photogrammetry — Planned:** ถ่ายภาพมือถือ → COLMAP/OpenMVS → point cloud ยังไม่มี reviewed E2E path

### Data Flow (synchronous)
```
Web → POST /api/v1/upload/analyze (อัปโหลดไฟล์ + species ถ้ารู้)
    → API เขียน temp file → รัน ML pipeline (subprocess ผ่าน pipeline_runner)
    → คืน AnalyzeResponse เต็ม (metadata + summary + trees + diagnostics)
      พร้อม segmented_cloud_id สำหรับ 3D viewer
```
งานสั้นพอที่จะจบในคำตอบเดียว: pipeline วัดแปลง 16 ต้น 447,089 จุดใน 10 วินาที
และ API จำกัดการวิเคราะห์ไว้ที่ 200,000 จุด

เคยมีคิว async (`POST /jobs/analyze` → worker → poll) แต่ถูกถอดออก: ไม่มีผู้เรียกใน
web app เลย ไม่มี deployment ใดสตาร์ท worker และ endpoint ตอบ 202 queued ให้งานที่รันไม่ได้

---

## 9. ML Pipeline — 8 ขั้นตอน (หัวใจโปรดักต์)

Input: `.las/.laz/.ply` point cloud → loader จำกัดจำนวนจุด → 8 ขั้น → JSON ต่อต้น
โค้ด orchestrator: `services/ml/pipeline/main.py` · แต่ละขั้นเป็นไฟล์แยกใน `services/ml/pipeline/`

| # | ขั้นตอน | ไฟล์ | Algorithm / Lib | สถานะจริง |
|---|---|---|---|---|
| 1 | Ground Classification | `ground_classification.py` | Percentile-grid heuristic (**ไม่ใช่ CSF**) | Implemented |
| 2 | Height Normalization | `height_normalization.py` | KNN inverse-distance weighting (**ไม่ใช่ TIN**) | Implemented |
| 3 | Canopy Height Model | `canopy_height_model.py` | Max-Z raster + morphology (**ไม่ใช่ full pit-free**) | Implemented |
| 4 | Tree Segmentation (ITD) | `tree_segmentation.py` | Watershed (scikit-image) | ✅ |
| 5 | **Wood-Leaf Segmentation** | `wood_leaf_separation.py` | `tlsep` baseline; PointNet++ Experimental | Implemented / Experimental |
| 6 | QSM-derived geometry | `qsm.py` | RANSAC DBH + max-Z height + taper volume; branch volume=0 | Implemented with limits |
| 7 | **Species Classification** | `species_classifier.py` | ResNet target | **Stub** — methods raise `NotImplementedError` |
| 8 | Allometric → Carbon | `allometric.py` | `species_db.csv` หรือ Chave fallback | Implemented; TGO verification pending |

- **Class codes:** `0 = wood`, `1 = leaf`, `2 = ground`
- **synthetic.py** = ตัว generate ต้นไม้สังเคราะห์ (ใช้เทรน/augment wood-leaf)
- **ply_export.py** = export point cloud + class ต่อจุด (ให้ 3D viewer / ให้อาจารย์เปิด)
- **realdata_eval.py / field_eval.py** = ประเมินผลบนข้อมูลจริง
- Output JSON: `{tree_id, dbh_cm, height_m, volume_m3, biomass_kg, carbon_kg, co2eq_kg, wood_leaf_iou, ...}` + `summary`
- ยังไม่มี benchmark ที่รองรับ processing-time SLA ต่อแปลง จึงไม่ระบุตัวเลขเวลาเชิงผลิตภัณฑ์

---

## 10. คณิตศาสตร์คาร์บอน (Allometric)

**สมการ species-specific เมื่อ coefficients ใน CSV ครบ:**
```
AGB = a × DBH^b × H^c        (kg)     — DBH เป็น cm, H เป็น m
```
**Fallback เมื่อ species/coefficients ไม่พร้อม — Chave 2014 pantropical:**
```
AGB = 0.0673 × (ρ × DBH² × H)^0.976   — ρ = wood density g/cm³
```
**ต่อยอด:**
```
BGB     = AGB × 0.24         (root:shoot ratio, IPCC 2006; ไผ่ใช้ 0.20)
Biomass = AGB + BGB
Carbon  = Biomass × 0.47     (carbon fraction, IPCC)
CO₂eq   = Carbon × 44/12
```
- **Source of truth ค่า a,b,c,ρ:** `services/ml/data/species_db.csv` (โหลดผ่าน `load_species_db()`)
- **5 ชนิด pilot:** สัก (Tectona), ยางนา (Dipterocarpus), ไผ่ (Bambusa), ยางพารา (Hevea), มะค่าโมง (Afzelia)
- มีฟังก์ชันคำนวณจาก volume แยกต่างหาก แต่ orchestrator ปัจจุบันไม่ได้ทำ dual-method 30% flag อัตโนมัติ
- **ตัวอย่าง unit-tested:** ไม้สัก DBH 30 cm สูง 18 m → ประมาณ **1.233 tCO₂eq**; ไม่แปลงเป็นมูลค่าเครดิต
- ⚠️ **Action ค้าง:** verify ค่าสัมประสิทธิ์กับ **TGO Forestry Guideline 2017** ตัวจริง (มะค่าโมงตอนนี้ใช้ค่า Chave adjusted เพราะขาดงานวิจัยไทย)

---

## 11. Wood-Leaf Model — สถานะจริง + ตัวเลขที่ต้องรายงานอย่างซื่อสัตย์

**2 โหมดใน `wood_leaf_separation.py`:**
- `tlsep` = PCA/geometric heuristic (ไม่ต้องเทรน — ใช้เป็น baseline/fallback)
- `pointnet` = PointNet++ Experimental candidate; ต้องมี checkpoint และยังไม่ใช่ default

**ผลจริง (`docs/ml/WOODLEAF_RESULTS.md`):**
| ชุดทดสอบ | ผล |
|---|---|
| Synthetic test (in-distribution) | recorded Mean IoU **0.977625** |
| Real TLS zero-shot (synthetic→real) | mean IoU ~**0.33** (wood ~0.19) |
| **Wan 2021 same-environment + synthetic augment** | Wood **0.418** / Leaf **0.808** / Mean **0.613** / accuracy **0.831** |

- Wan held-out loader ถูกใช้เลือก best epoch ด้วย และ checkpoint/tree-ID provenance ยังไม่ครบ จึงไม่ใช่ independent final test
- **Demol geometry validation:** isolated-tree 65 ต้น, DBH MAE **0.898318 cm**, Height MAE **0.543323 m**,
  Volume MAPE **11.520556%**; ไม่ได้ validate ขั้น 1–4, species, allometric หรือ carbon
- ห้ามรวม `0.613` เป็น “Wood/Leaf IoU” ที่ทำให้เข้าใจว่า Wood IoU เท่ากัน และห้ามปัด DBH เพื่อ marketing โดยไม่วางค่าจริงไว้ใกล้กัน

---

## 12. Dataset Strategy ⚠️ (เปลี่ยนทิศตามอาจารย์ 2026-07-15)

**คำสั่งอาจารย์:** **ไม่ต้องเก็บ/สแกนข้อมูลต้นไม้ไทยเอง** — ใช้ **open dataset ดีๆ** มาเทรน wood-leaf แทน
(ตัดเฉพาะ "การเก็บ training data ไทย" — ฟีเจอร์ photogrammetry/มือถือยังอยู่ใน product roadmap แต่สถานะยังเป็น Planned)

**Loader contract (`services/ml/training/realdata_dataset.py`) — สำคัญมากถ้าจะเพิ่ม dataset:**
- รับ per-point `(x, y, z, label)` โดย `label: 0=wood, 1=leaf`
- โค้ด generic (`tile_samples`, `spatial_split`, `build`) reuse ได้ — ที่ผูกกับ Wan มีแค่ `load_wan_plot()`
- **เพิ่ม dataset ใหม่ = เขียน `load_<ชุด>_plot()` เล็กๆ ~20-40 บรรทัด** ไม่ต้องรื้อ pipeline
- ถ้า label เป็น stem/branch/foliage → map: ลำต้น+กิ่ง→0, ใบ→1

**Dataset ปัจจุบัน + candidate:**
| ชุด | label wood/leaf ต่อจุด? | สถานะ |
|---|---|---|
| **Wan et al. 2021** (Dryad `10.5061/dryad.rfj6q5799`, CC-BY, 73 trees/3 species) | ✅ | ใช้แล้ว; best recorded Mean IoU 0.613 มี selection caveat |
| TLSeparation (6 trees) | ✅ | มีในเอกสาร ใช้ validate ข้ามชุด |
| **LeWoS / Wang 2020**, **FOR-instance** | ✅ / semantic (ต้อง verify) | candidate เพิ่ม → ดัน wood IoU |
| NEON Veg Structure | ❌ (มี DBH/H วัดจริง) | ใช้ validate allometric ไม่ใช่ wood-leaf |

> **งานค้างที่อาจารย์ให้ทิศมา:** research + verify open dataset ที่มี label wood/leaf ต่อจุด แล้วสร้าง independent final split,
> checkpoint provenance และ downstream comparison ก่อนพิจารณา promotion

---

## 13. Backend (FastAPI) — synchronous analyze

**Endpoints (`app/api/v1/`):**
- `POST /api/v1/upload/analyze` — รันทันที คืนผลเต็ม (ไม่ต้อง auth; จำกัดด้วย cap + rate limit)
- `GET /api/v1/upload/segmented/{id}` — segmented PLY ของผลนั้น
- `GET /api/v1/upload/species` — ชนิดพันธุ์ที่ deployment นี้คิดค่าได้
- `GET /api/v1/health`, `/api/v1/health/pipeline` — liveness / readiness
- `/api/v1/auth/*` — `/me` ใช้งานได้; `/signup` `/login` ตอบ 501 เพราะเว็บคุยกับ Supabase ตรง
- `/api/v1/trees/*` ถูกถอดออก (migration `0004`) — `Tree.location` เป็น `POINT srid=4326` NOT NULL
  แต่ pipeline ไม่เคยผลิตพิกัดภูมิศาสตร์: `load_point_cloud` ทิ้ง CRS ของ LAS และ
  `TreeResult.location` เป็น `{x, y}` ในระบบพิกัดของก้อน point cloud เอง จึงไม่มีอะไรจะใส่

**ชิ้นส่วนสำคัญ:**
- `services/pipeline_runner.py` — เรียก ML CLI แบบ subprocess
- `services/upload_validation.py` — ตรวจนามสกุล (`ANALYZE_EXTENSIONS`) + vertex cap
- `services/segmented_cloud_store.py` — เก็บ PLY ที่ผลนั้นวัดมา ให้ viewer ดึง
- `services/species_catalogue.py` — อ่าน `services/ml/data/species_db.csv`
- `core/demo_security.py` — token gate (demo mode) + rate limit บน upload
- Migration `0003` ลบตาราง `jobs` พร้อมคิวที่ไม่มีผู้ใช้

**⚠️ Windows gotcha (แก้แล้ว):** emoji ใน `print()` ของ lifespan ทำ uvicorn crash บน cp874 console → เอา emoji ออกหมด (commit `6ca8693`)

---

## 14. Web (Next.js) — landing + viewer + auth

**Landing (`apps/web/src/app/page.tsx`) — rebuild ล่าสุด:**
- ธีม **nature-template** (ป่ายามเย็นวาดด้วย SVG + ฟอนต์สคริปต์ Pacifico + palette เขียว forest)
- **server component + Tailwind ล้วน** (ไม่มี canvas/3D, ไม่มี styled-jsx)
- Sections: Hero → Technology → Pipeline(4 ขั้น) → Validation(ตัวเลขจาก manifest) → CTA → Footer
- ⚠️ **บทเรียนสำคัญ:** เวอร์ชันก่อนใช้ **canvas 3D + styled-jsx → เรนเดอร์ unstyled บน production**
  (styled-jsx ไม่ SSR ใน App Router ถ้าไม่มี style registry) → **ห้ามใช้ styled-jsx/canvas ในหน้า marketing อีก ใช้ Tailwind**

**ส่วนอื่น:**
- `components/viewer/point-cloud-viewer.tsx` — 3D viewer (React Three Fiber) แสดง wood/leaf
  ⚠️ เคยมีบั๊กสี three.js: vertex color เป็น linear-space แต่ canvas output sRGB → ต้องแปลง sRGB→linear ด้วย `THREE.Color`
- `lib/api.ts` — typed API client; viewer แสดง backend/status/Git/input/checkpoint provenance และ species Stub
- `middleware.ts` — refresh Supabase session + **guard**: ถ้าไม่มี Supabase env → ข้าม (ไม่ crash) [ให้ local dev เปิดได้]
- Auth: Supabase (`NEXT_PUBLIC_SUPABASE_URL` + `ANON_KEY`)

**Deploy:** Vercel → production alias **`treeqcarbon.vercel.app`**
- deploy ผ่าน `npx vercel --prod --archive=tgz --yes` (จาก `apps/web`)
- ⚠️ **vercel env gotcha:** ตั้ง env var ต้องใช้ `vercel env add NAME production --value "<v>" --no-sensitive --force --yes`
  (pipe/stdin ใช้ไม่ได้เมื่อรันโดย agent — จะได้ค่าว่าง!) · `--no-sensitive` ให้ pull กลับมา verify ได้

---

## 15. Mobile (Flutter) — ลบออกแล้ว

**`apps/mobile` ไม่มีอยู่แล้ว** ถูกลบที่ commit `8ce6021` เมื่อ 9 ส.ค. 2569 ตาม
[ADR 0007](decisions/0007-drop-the-photo-path.md) พร้อมกับเส้นทาง photogrammetry ทั้งหมด
และ `.github/workflows/ci-mobile.yml`

เหตุผลตาม ADR: แอปมีไว้ถ่ายภาพเพื่อป้อน photogrammetry และ gate ที่ต้องพิสูจน์ว่าภาพถ่ายลำต้นจริง
ให้จุดพอ fit วงกลมที่ 1.3 ม. ได้ไหม **ไม่เคยผ่าน เพราะไม่เคยรัน** — `colmap` ไม่ได้ติดตั้ง และเรื่อง
scale ไม่เคยถูกแก้เลย (SfM คืนรูปทรง ไม่ใช่ขนาด) ทุกเส้นผ่านศูนย์กลางที่มันจะผลิตได้คือตัวเลขที่ไม่มีหน่วย

หัวข้อนี้เก็บไว้เป็นบันทึก เพราะเอกสารรุ่นเก่ายังอ้างถึง `apps/mobile` อยู่ ไม่ใช่เพราะยังมีของอยู่

---

## 16. Deployment & Ops

| ส่วน | Prod | Demo (ตอนนี้) |
|---|---|---|
| Web | Vercel `treeqcarbon.vercel.app` | เหมือนกัน |
| API + ML | (target: Railway/RunPod GPU) | **Cloudflare quick tunnel ฟรี** → local API (`*.trycloudflare.com`) |
| DB/Auth/Storage | Supabase | เหมือนกัน |

- **สคริปต์เปิด backend สำหรับ demo:** `C:\Users\Acer\OneDrive\Desktop\CarbonScrip\start_backend.bat` (+ `.ps1`)
  → kill tunnel เก่า → เปิด API (uvicorn) → เปิด cloudflared → ดึง URL → `vercel env add` → redeploy
- Tunnel URL เปลี่ยนทุกครั้งที่ restart → สคริปต์อัปเดต Vercel env อัตโนมัติ (named tunnel ต้องมี domain เสียเงิน)

---

## 17. สถานะปัจจุบัน (ความจริง ณ 2026-07-16)

**✅ เสร็จ/ใช้งานได้:**
- ML core path: ขั้น 1–6 และ 8 Implemented; ขั้น 7 species เป็น Stub
- `tlsep` baseline + deterministic core demo พร้อม provenance/hashes
- PointNet++ มี Wan research result แต่สถานะยังเป็น Experimental และไม่ใช่ default
- Backend async-job + polling + sync endpoint (production hosting ยังไม่มี)
- Web landing ใหม่ (nature-template Tailwind) — live บน `treeqcarbon.vercel.app`
- 3D viewer แสดง wood/leaf point cloud และ analysis provenance ได้
- Reviewed synthetic core demo รันซ้ำได้: 3 ต้น, 1036.09 kg C, 3798.99 kg CO₂e (ไม่ใช่ accuracy benchmark)

**⚠️ กำลังทำ / ค้าง:**
- Rebrand core surface แล้ว; เหลือ legacy docs/proposal/assets/GitHub repo name
- Species classifier (ขั้น 7): ยังเป็น stub — ต้องเทรน ResNet จริง (หลัง proposal)
- PointNet++ reviewed evidence: `FAIL_METRICS`; external Wood IoU point estimate ดีขึ้น แต่ CI คร่อมศูนย์
  และ DBH/height/volume/measurable-tree formal criteria ไม่ผ่าน จึงไม่ promote
- Dataset: research + verify open wood/leaf dataset เพิ่มตามอาจารย์
- Deploy API จริง (Railway / HF Spaces) — ตอนนี้ยังใช้ tunnel
- verify allometric coefficients กับ TGO Guideline 2017 ตัวจริง
- Truth-aligned NSC DOCX copy — สร้างเป็นไฟล์ใหม่โดยห้ามทับต้นฉบับ

สถานะ Git ให้ตรวจจาก branch/PR ปัจจุบัน ไม่ hard-code ใน master spec

---

## 18. Decisions & Constraints หลัก

1. **Dual-input target** (`.las` upload Implemented + photogrammetry Planned) — decision 0004
2. **ไม่ใช้ iPhone LiDAR** (ทีมไม่มี → COLMAP/OpenMVS) — decision 0002
3. **Cloud GPU on-demand** แทนซื้อ workstation — decision 0005
4. **Open-source first** · **Lock scope prototype = 5 ชนิดไม้**
5. **Honesty ethos** — รายงานตัวเลขจริง + ข้อจำกัด (bamboo caveat, stock-vs-credit) ไม่ oversell
6. **Landing = Tailwind server-component** เท่านั้น (ไม่ 3D/styled-jsx — พังบน prod)
7. **ไม่เก็บข้อมูลไม้ไทยเอง** — ใช้ open dataset (อาจารย์สั่ง 2026-07-15)

---

## 19. Known Issues / Gotchas (บทเรียนที่เจ็บมาแล้ว)

| ปัญหา | สาเหตุ | ทางแก้ |
|---|---|---|
| Web landing unstyled บน prod | styled-jsx ไม่ SSR ใน App Router | ใช้ Tailwind (มี CSS `<link>` จริง) |
| Vercel env var ได้ค่าว่าง | pipe/stdin ไม่ทำงานตอน agent รัน CLI | `vercel env add ... --value "<v>" --no-sensitive --force --yes` |
| uvicorn crash บน Windows | emoji ใน print → cp874 UnicodeEncodeError | เอา emoji ออก / `PYTHONIOENCODING=utf-8` |
| 3D viewer สีเพี้ยน (tan) | three.js sRGB/linear vertex color mismatch | แปลง sRGB→linear ด้วย `THREE.Color` |
| MIDDLEWARE_INVOCATION_FAILED | ขาด `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY` | ตั้ง env + guard ใน middleware |
| .bat เด้งปิดทันที | Thai filename ใน path handoff | ใช้ชื่อไฟล์อังกฤษ + `pause` |
| `ndarray.ptp()` error | ถูกถอดใน numpy 2.x | ใช้ `np.ptp()` |

---

## 20. Roadmap (หลัง Proposal)

1. ปรับ PointNet++ candidate โดยห้ามใช้ Cohort A ปัจจุบันหรือ Demol เพื่อ train, tune หรือ model selection;
   freeze candidate/protocol ก่อนเปิดผล และใช้ independent final cohort/split ใหม่ที่ไม่เคยเปิดผลเป็น decisive gate รอบถัดไป
2. เพิ่มและ verify open wood/leaf training data พร้อม checkpoint/training provenance ชุดใหม่;
   ผล Cohort A + Demol ปัจจุบันคงเป็น immutable historical evidence เท่านั้น
3. verify coefficients ของ `species_db.csv` กับ paper ต้นทางของแต่ละสมการ เพื่อปลด gate
   (ตาราง T-VER ของ อบก. ถอดและตรวจแล้วใน `pipeline/tver.py` — ดู `docs/ml/TVER_EQUATIONS.md`)
4. Deploy API บน host ถาวร (เลิกพึ่ง tunnel)
5. เทรน species classifier จริง — ขั้นที่ 7 ยังเป็น Stub
6. B2B marketplace / GIS / certification workflow หลัง core measurement evidence พร้อม

---

## 21. Glossary

| Term | ความหมาย |
|---|---|
| **DBH** | Diameter at Breast Height — เส้นผ่านศูนย์กลางลำต้นที่ 1.3 ม. |
| **QSM-derived geometry** | implementation ปัจจุบันวัด RANSAC DBH + max-Z height + taper volume; ไม่ใช่ full TreeQSM |
| **CHM** | Canopy Height Model |
| **ITD** | Individual Tree Detection |
| **TLS** | Terrestrial Laser Scanning |
| **AGB/BGB** | Above/Below-Ground Biomass |
| **Allometric** | สมการแปลง dimension ต้นไม้ → biomass |
| **IoU** | Intersection over Union (วัดความแม่น segmentation) |
| **TGO** | องค์การบริหารจัดการก๊าซเรือนกระจก |
| **SfM/MVS** | Structure from Motion / Multi-View Stereo (photogrammetry) |
| **CSF** | Cloth Simulation Filter; เป็น target/reference ไม่ใช่ ground implementation ปัจจุบัน |

---

## 22. Reference Files

- `AGENTS.md` — working rules และสถานะย่อ (โหลดโดย agent)
- `docs/ml/PIPELINE.md` — 8 ขั้นละเอียด
- `docs/ml/ALLOMETRIC.md` — สมการ + species DB + references
- `docs/ml/WOODLEAF_RESULTS.md` — ผลทดลอง wood-leaf ทุก variant
- `docs/ml/DATASETS.md` · `docs/ml/FINETUNE_REALDATA.md` — ข้อมูล + วิธี fine-tune
- `services/ml/data/species_db.csv` — source of truth ค่า allometric
- Memory: `C:\Users\Acer\.claude\projects\D--Project-Carbon\memory\` (MEMORY.md + ไฟล์ย่อย)

---

_จบ Master Spec — ถ้าตัวเลข/สถานะไม่ตรงกับโค้ดปัจจุบัน ให้เชื่อโค้ดและอัปเดตเอกสารนี้_
