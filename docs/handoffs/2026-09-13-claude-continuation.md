# Handoff — 13 ก.ย. 2569 · S1 RunRequest/RunReport contract

> **อ่านก่อน:** [`CLAUDE.md`](../../CLAUDE.md) · เอกสารนี้คือ checkpoint ล่าสุด
> **Base commit:** `b68e332` (23 ส.ค. 2569) · **Branch:** `claude/kind-noether-syenrm`
> **ยังไม่ push** — ตามคำสั่งรอบนี้ commit อย่างเดียว

---

## 1. ข้อขัดแย้งที่ต้องรู้ก่อนอื่น

รอบนี้ถูกสั่งให้อ่านเอกสาร 7 ไฟล์ **4 ไฟล์ไม่มีอยู่จริงใน repo**:

| ไฟล์ที่ถูกอ้าง | สถานะจริง |
|---|---|
| `docs/handoffs/2026-09-13-claude-continuation.md` | ไม่มี (ไฟล์นี้เพิ่งถูกสร้างเป็นฉบับแรก) |
| `docs/superpowers/plans/2026-09-13-treeq-next-implementation.md` | ไม่มี — plan ใหม่สุดคือ `2026-08-20-cameroon-tropical-evaluation.md` |
| `docs/superpowers/specs/2026-09-11-treeq-evidence-workbench-design.md` | ไม่มี |
| `docs/audits/2026-09-13-m1-implementation-report.md` | ไม่มี — ไม่มีแม้แต่ directory `docs/audits/` |

และงาน **M0/M1a/M1b ที่ถูกบอกว่า "แก้แล้วแต่ยังไม่ commit" ไม่มีอยู่ในนี้**
`git status` สะอาด 100% ตั้งแต่ต้นรอบ · `git log main..HEAD` ว่างเปล่า
`RunRequest` / `RunReport` / `LegacyAssessment` ไม่ปรากฏใน codebase เลย (grep ทั้ง repo)

**คำอธิบายที่ตรงหลักฐานที่สุด:** session นี้รันบน cloud container ที่ clone
`Remote55/treeq` ใหม่ ไม่ใช่ `D:\Project_Carbon` บนเครื่องผู้ใช้
งานที่ยังไม่ commit ไม่ถูก push จึงเดินทางมาถึงที่นี่ไม่ได้

**ผลที่ตามมาที่คนทำต่อต้องระวัง:** งาน S1 ในรอบนี้สร้างบน `b68e332`
ไม่ได้สร้างทับงาน M0/M1a/M1b — ถ้างานนั้นยังอยู่บนเครื่อง ต้อง merge เอง
S1 เลือกเป็น **package ใหม่ล้วน** ส่วนหนึ่งก็เพราะเหตุนี้: มันไม่แตะไฟล์เดียวกับ
auth protections / parser guards / viewer cancellation ที่ M1 แก้ไว้

---

## 2. สิ่งที่ทำจริงรอบนี้ — S1 ครบทุกเกณฑ์

3 commits ย้อนกลับได้ทีละอัน:

| commit | สิ่งที่แก้ |
|---|---|
| `f4ee12e` | core package: models + semantics + fixtures |
| `ee0b6fd` | generation (JSON Schema / TS / Zod) + drift check + CI |
| `7e3845a` | dependency wiring เข้า API และ ML |

### เกณฑ์ S1 เทียบผลจริง

| เกณฑ์ | สถานะ | หลักฐาน |
|---|---|---|
| strict schemas | ✅ | `extra="forbid"` + `frozen=True` ทุก model · enum ปิดทุกตัว |
| semantic validation | ✅ | `semantics.py` — dependency graph, cycle detection, failed-run rule |
| generated JSON Schema/Zod/TypeScript | ✅ | `schema/*.json`, `typescript/src/{types,zod}.ts` |
| shared valid/invalid fixtures | ✅ | 4 valid + 12 invalid · **ทั้ง Python และ TS อ่านไฟล์ชุดเดียวกัน** |
| package import + dependency config | ✅ | ประกาศใน pyproject ทั้งสอง service · CI ติดตั้งให้ · มี test ฝั่งละไฟล์ |
| generation drift checks | ✅ | `--check` + test ใน pytest + step ใน CI — **พิสูจน์แล้วว่าล้มจริง** |

### กติกาจาก CLAUDE.md ที่ตอนนี้มีกลไกบังคับแล้ว

1. **Missing ไม่ใช่ศูนย์** — `unusable` บังคับ `value=None` ไม่ใช่ `0.0`
   ตัวเลขที่ใช้ไม่ได้จะไม่มีตัวเลขติดมาเลย เพราะตัวเลขที่อยู่ในฟิลด์เดี๋ยวก็มีคนเอาไปบวก
2. **provisional ห้ามทำให้ downstream เป็น accepted** — `accepted_from_provisional`
3. **dependency ที่ใช้ไม่ได้ ทำให้ derived ใช้ไม่ได้** — `usable_from_unusable`
4. **ห้ามเดา unit/CRS/species/density จากชื่อไฟล์** — `DeclarationSource`
   **ไม่มี** member ชื่อ `filename` การเดาจึง *เขียนลงเอกสารไม่ได้*
5. **sensitivity range ไม่ใช่ 95% CI** — validator ปฏิเสธ basis ที่อ้างว่าเป็น CI
6. **execution status แยกจาก scientific completeness** — คนละ field คนละ enum

### สองชื่อที่ตั้งใจตั้งใหม่ (และเหตุผล)

- `analysed_points_sha256` — hash ของ XYZ array หลัง thinning **ไม่ใช่ hash ไฟล์**
  ของเดิม `input_sha256` อ่านแล้วเหมือน file hash แต่ `pipeline/main.py:344`
  เติมค่าจาก `hash_points(points)` · hash ไฟล์จริงอยู่ที่ `request.source.file_sha256`
- `biomass_total_kg` — AGB + BGB ตรงกับ legacy `biomass_kg`
  (`allometric.py:560,726` เซ็ต `biomass = agb + bgb`) เขียนเต็มกันคนมา "แก้ให้ถูก" เป็น AGB

**legacy ไม่ถูกแตะเลย** — `AnalyzeResponse` / `biomass_kg` / `input_sha256`
ยังเหมือนเดิมทุกตัว และมี test ฝั่ง API กันไม่ให้ใคร rename ทีหลัง

---

## 3. คำสั่งทดสอบและผลจริง

```bash
# ติดตั้ง (ลำดับสำคัญ — contract ต้องมาก่อน)
pip install -e packages/run-contract

cd packages/run-contract
python -m pytest tests/ -q          # 32 passed in 0.14s
npx vitest run                      # 27 passed (27)
npx tsc --noEmit                    # clean
python tools/generate_contract.py --check   # 5 generated files match the models

cd services/api && python -m pytest tests/ -q -o addopts=""   # 114 passed
cd services/ml  && python -m pytest tests/test_run_contract_available.py -q  # 6 passed
```

**drift check พิสูจน์แล้วว่าล้มจริง** — ทดลองเพิ่ม field ลง `RunProvenance`
โดยไม่ regenerate: exit 1 พร้อมชี้ `run-report.schema.json`, `types.ts`, `zod.ts` ว่า stale
แล้ว restore กลับ → exit 0

---

## 4. สิ่งที่ยังไม่ผ่าน / ยังไม่ได้ตรวจ

### ตรวจแล้วว่าเป็นปัญหาของ container ไม่ใช่ของ repo

- **`services/api` ครั้งแรกได้ 4 failed + 31 errors** — สาเหตุคือ `pytest-asyncio`
  ไม่ได้ติดตั้งใน container **ยืนยันด้วยการ `git stash` แล้วรันบน tree สะอาด: fail เหมือนกันเป๊ะ**
  ติดตั้งแล้วได้ **114 passed** (ก่อนแก้รอบนี้ 108 + ที่เพิ่ม 6)
- **`scripts/sync_truth.py --check` รันไม่ผ่านที่นี่** — clone เป็น **shallow (87 commits)**
  evidence manifest อ้าง commit `c498739a` ที่อยู่นอก history
  diff รอบนี้**ไม่แตะ** `docs/evidence/`, `docs/PROJECT_SPEC.md`, `docs/ml/`, `scripts/` เลย

### ยังไม่ได้ทำ / ยังไม่ได้ตรวจ

- **contract ยังไม่ได้ต่อเข้า production path** — `POST /upload/analyze` ยังคืน
  `AnalyzeResponse` แบบเดิมทุกประการ (ตั้งใจ — S1 เป็น additive ล้วน)
- **ยังไม่มี adapter จาก `PipelineResult` → `RunReport`** เมื่อทำ ต้องจำว่า
  **ผลเก่าไม่มี `accepted`** เพราะ legacy ไม่ได้บันทึก protocol conformance ไว้ที่ไหนเลย
  อย่างมากที่สุดคือ `provisional` — ห้ามเติม provenance ย้อนหลัง
- **ยังไม่ได้รัน ML suite เต็ม** ตามกติกา · test ML ที่เพิ่ม import แค่
  `pipeline.provenance` (ต้องการแค่ numpy) ไม่ได้ import `pipeline.main`
- **fixtures เป็น synthetic ทั้งหมด** — พิสูจน์พฤติกรรมซอฟต์แวร์ **ไม่ใช่ความแม่นยำบนต้นไม้จริง**
- **ยังไม่ push** และยังไม่ได้เปิด PR

---

## 5. เอกสารที่ drift ที่เจอระหว่างทาง (ยังไม่แก้ — อยู่นอก scope S1)

- **`AGENTS.md`** ระบุ "สถานะปัจจุบัน (2026-07-16)" ขัดกับ `CLAUDE.md` (23 ส.ค.) หลายจุด:
  ยังบอกว่าเป้าหมายคือ "ทำให้กรรมการ NSC ว้าว" (CLAUDE.md บอกว่าเลิกใช้แล้ว),
  ยังเขียนว่า API ใช้ SQLAlchemy/asyncpg/Alembic + async-job worker (ถอดออกแล้ว),
  และบอกว่า `pytest` = 79 tests (ตอนนี้ 108 ก่อนรอบนี้)
- **`CONTRIBUTING.md`** ยังมีหัวข้อ `apps/mobile` (Flutter) ที่ถูกลบตาม ADR 0007
  และยังสั่งให้ update `docs/DATA_MODEL.md` + Alembic migration เมื่อเปลี่ยน DB schema
- **`memory/projects/carbonscan-ai.md`** ยังเป็นบริบท NSC + marketplace + Flutter ทั้งไฟล์
- **`package.json`** ที่ root ยัง `"name": "carbonscan-ai"`, description ยังเป็น NSC 2026,
  และยังมี script `mobile:run` ที่ชี้ `apps/mobile` ซึ่งไม่มีแล้ว

---

## 6. งานถัดไปที่ลงมือได้ทันที

**ข้อควรระวัง:** "S2" ในแผนที่ถูกอ้างถึง **อ่านไม่ได้** เพราะไฟล์แผนไม่มีใน repo
รายการข้างล่างมาจากการอ่านโค้ดจริง ไม่ใช่การเดาเนื้อหาแผน — **ยืนยันกับแผนตัวจริงก่อนเริ่ม**

1. **Adapter `PipelineResult` → `RunReport`** ใน `services/ml` พร้อม golden test
   เทียบ field ต่อ field กับ legacy · ทุก quantity ได้มากสุด `provisional`
2. **ต่อ contract เข้า `pipeline_runner.py`** — ตอนนี้ API `json.loads` stdout ของ subprocess
   ดิบ ๆ ไม่มีอะไรตรวจ · validate ตรงนั้นคือจุดที่คุ้มที่สุดจุดเดียว
3. **ให้ `apps/web` ใช้ generated types** แทน TS ที่เขียนมือ (เพิ่ม `@treeq/run-contract`
   ลง `apps/web/package.json` — pnpm workspace ครอบ `packages/*` อยู่แล้ว)
4. งาน ML/วิทยาศาสตร์เดิมยังค้างตาม README "งานถัดไป" (buttress circle fit, wood/leaf เขตร้อน,
   species classifier, deploy, verify coefficients) — ไม่ถูกแตะรอบนี้

---

## 7. ตำแหน่งไฟล์สำคัญ

```
packages/run-contract/
  python/treeq_run_contract/models.py      <- แหล่งความจริงของ shape
  python/treeq_run_contract/semantics.py   <- กฎ dependency graph
  typescript/src/semantics.ts              <- HAND-WRITTEN คู่แฝดของ semantics.py
  fixtures/{valid,invalid}/                <- ทั้งสองภาษาอ่านชุดเดียวกัน
  tools/generate_contract.py --check       <- drift gate
  README.md                                <- เหตุผลของทุกการตัดสินใจ
.github/workflows/ci-contract.yml          <- schema + ทั้งสอง binding + ASCII check
```
