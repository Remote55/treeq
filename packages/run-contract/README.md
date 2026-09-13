# `@treeq/run-contract` — สัญญา RunRequest / RunReport v2

> **แหล่งความจริงคือ Python models ใน `python/treeq_run_contract/`**
> JSON Schema, TypeScript types และ Zod validators ถูก **generate** ออกมาจากตรงนั้น
> ห้ามแก้ไฟล์ที่ generate ด้วยมือ — CI มี drift check

แพ็กเกจนี้เป็นชั้นสัญญาเดียวที่ API (`services/api`), ML pipeline (`services/ml`)
และ web client (`apps/web`) ใช้ร่วมกัน เพื่อให้ "ตัวเลขหนึ่งตัว" เดินทางข้าม process
โดยไม่เปลี่ยนความหมายระหว่างทาง

---

## ทำไมต้องมี

API กับ ML **ไม่ได้อยู่ process เดียวกัน** — `services/api/app/services/pipeline_runner.py`
เรียก ML ผ่าน subprocess แล้ว parse JSON กลับมา แปลว่าขอบเขตระหว่างสองฝั่งคือ
**เอกสาร JSON ที่ไม่มีใครตรวจ** จนกว่าจะมีแพ็กเกจนี้

แพ็กเกจจึงต้องเป็น pure-Python และมี dependency เดียวคือ `pydantic`
(ติดตั้งลงทั้ง API venv ที่ตั้งใจให้เบา และ ML venv ที่หนักอยู่แล้ว — อะไรที่หนักกว่านี้จ่ายสองรอบ)

---

## กติกาแกนกลาง 3 ข้อ

### 1. Missing ไม่ใช่ศูนย์ และศูนย์จริงไม่ใช่ missing

`Quantity.status` บังคับคู่กับ `value`:

| status | value | ความหมาย |
|---|---|---|
| `accepted` | ต้องมีตัวเลข + ต้องมี `protocol` | ผ่านเกณฑ์ของ protocol ที่ระบุชื่อไว้ |
| `provisional` | ต้องมีตัวเลข | คำนวณได้ แต่ยังไม่ผ่านเกณฑ์ครบ |
| `unusable` | **ต้องเป็น `null`** + ต้องมี `unusable_reason` | ใช้ไม่ได้ พร้อมเหตุผล |

`value: 0.0` + `accepted` = ศูนย์ที่นับมาจริง · `unusable` = ไม่มีตัวเลขให้ ไม่ใช่ศูนย์
ค่าที่ใช้ไม่ได้จะ **ไม่มีตัวเลขติดมาเลย** เพราะตัวเลขที่อยู่ในฟิลด์ เดี๋ยวก็มีคนเอาไปบวก

### 2. `accepted` ไม่เท่ากับ "แม่นยำ" และไม่เท่ากับคาร์บอนเครดิต

`accepted` = **ผ่านเกณฑ์ของ protocol ที่ชื่อระบุอยู่บน quantity นั้น**
`ProtocolRef` จึงบังคับ — เพื่อให้คนอ่านตามไปดูเกณฑ์และเถียงได้
ไม่ใช่คำรับรองความแม่นยำ ไม่ใช่การรับรอง และไม่ใช่เครดิต

### 3. สถานะไหลลงทางเดียว แย่ลงได้อย่างเดียว

`semantics.py` ตรวจ dependency graph:

- dependency เป็น `unusable` → ตัวที่ derive ต่อ **ต้อง** เป็น `unusable` (reason ต้องชี้กลับไปที่ dependency)
- dependency เป็น `provisional` → ตัวที่ derive ต่อ **ห้าม** เป็น `accepted`
- `execution.status == failed` → ห้ามมี quantity ไหนไม่ใช่ `unusable`

**ไม่มีกฎไหนที่ทำให้ผลลัพธ์ดีกว่า input ที่แย่ที่สุดของมัน**

---

## แยกสองแกนที่คนละเรื่องกัน

| แกน | ฟิลด์ | ตอบคำถาม |
|---|---|---|
| execution status | `RunExecution.status` = `ok` / `partial` / `failed` | โค้ดรันจบไหม |
| scientific completeness | `Quantity.status` | ตัวเลขที่ได้ใช้ได้ไหม |

รันจบโดยไม่ raise แล้วได้ DBH ที่ไม่มี protocol ไหนรับ — เกิดขึ้นได้
รันพังกลางทางแต่ต้นที่วัดไปแล้วยังใช้ได้ — ก็เกิดขึ้นได้

---

## สองชื่อที่ห้ามแก้

**`analysed_points_sha256`** — hash ของ XYZ array ที่ **วัดจริงหลัง thinning**
ไม่ใช่ hash ของไฟล์ที่อัปโหลด · ของเดิมชื่อ `input_sha256` ซึ่งอ่านแล้วเหมือน file hash
แต่ `pipeline.main.process_points` เติมค่าจาก `hash_points(points)`
hash ของไฟล์จริงอยู่ที่ `request.source.file_sha256` — คนละค่ากันทุกครั้งที่ cloud ถูก thin

**`biomass_total_kg`** — above-ground **บวก** below-ground ตรงกับที่ legacy `biomass_kg`
เก็บมาตลอด (`allometric.calculate_carbon` เซ็ต `biomass = agb + bgb`)
เขียนเต็มเพื่อไม่ให้มีใคร "แก้ให้ถูก" เป็น AGB ทีหลัง · ใครต้องการครึ่งเดียวใช้ `agb_kg` / `bgb_kg`

---

## `SensitivityRange` ไม่ใช่ 95% CI

`low`/`high` มาจากการคำนวณใหม่ที่ปลายทั้งสองของช่วงสมมติฐาน (ในระบบนี้คือ wood density)
ไม่มี sampling distribution ไม่มี error model ของการวัด ไม่เผื่อว่าสมการ allometric ผิด

`basis` บังคับกรอก และ **validator ปฏิเสธ** ข้อความที่เรียกมันว่า confidence interval

---

## ห้ามเดาจากชื่อไฟล์

`DeclarationSource` **ไม่มี** member ชื่อ `filename` — เป็นกลไกที่ทำให้การเดา
*เขียนลงเอกสารไม่ได้เลย* ถ้า producer อยากบันทึกว่า "ได้ species มาจากชื่อไฟล์"
จะไม่มีค่าที่ valid ให้เขียน และต้องปล่อยให้ declaration หายไป ซึ่งคือความจริง

`length_unit` บังคับเสมอ · `crs` ที่เป็น `null` แปลว่า **ไม่มีใครประกาศ** ไม่ใช่ WGS84

---

## โครงสร้าง

```
packages/run-contract/
  python/treeq_run_contract/   <- แหล่งความจริง
    version.py    enums.py    models.py    semantics.py    fixtures.py
  fixtures/valid/              <- ทั้งสองภาษาอ่านไฟล์ชุดเดียวกัน
  fixtures/invalid/            <- แต่ละไฟล์มี __expect__ บอกว่าผิดตรงไหน
  schema/                      <- GENERATED
  typescript/src/              <- GENERATED
  tools/build_fixtures.py      <- regenerate fixtures
  tools/generate_contract.py   <- regenerate schema + TS (มี --check)
```

---

## คำสั่ง

```bash
cd packages/run-contract
pip install -e ".[dev]"
python -m pytest tests/ -q           # ~1 วินาที ไม่แตะ ML deps

python tools/build_fixtures.py       # regenerate fixtures
python tools/generate_contract.py    # regenerate schema + TypeScript + Zod
python tools/generate_contract.py --check   # CI: ล้มถ้า generated drift
```

---

## เพิ่ม / แก้ฟิลด์

1. แก้ `python/treeq_run_contract/models.py`
2. bump `CONTRACT_VERSION` ใน `version.py` **และ** `version` ใน `pyproject.toml` (test บังคับให้ตรงกัน)
   - **MAJOR** เมื่อฟิลด์เดิมเปลี่ยนความหมายหรือหายไป — รวมถึง *เปลี่ยนชื่อ* แม้ type เหมือนเดิม
   - **MINOR** เมื่อเพิ่มฟิลด์ที่เอกสารเก่าไม่มี
   - **PATCH** เมื่อแก้เอกสาร/ข้อความ validation
3. `python tools/build_fixtures.py && python tools/generate_contract.py`
4. `python -m pytest tests/ -q`

---

## ขอบเขตที่แพ็กเกจนี้ **ไม่** ครอบคลุม

- **ไม่ได้พิสูจน์ความแม่นยำ** — fixtures เป็น synthetic ทั้งหมด พิสูจน์แค่พฤติกรรมของซอฟต์แวร์
  บนต้นไม้จริงยังเป็นเรื่องของ cohort ใน `docs/evidence/`
- **ไม่ใช่ LegacyAssessment** — ผลเก่าไม่มี `accepted` และไม่ใช่ RunReport v2
  ห้ามเติม provenance ย้อนหลังให้ผลเก่าผ่านเกณฑ์ใหม่
- **ยังไม่ได้ต่อเข้า production path** — ดู checkpoint ล่าสุดใน `CLAUDE.md`
