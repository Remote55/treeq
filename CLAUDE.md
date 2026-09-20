# TreeQ Carbon Platform — Working Memory

> โหลดเข้า context อัตโนมัติทุกครั้งที่เปิด project นี้
> เดิมชื่อ **CarbonScan AI** — ชื่อเก่ายังอยู่ในเอกสาร historical และใน GitHub repo slug

## Project

ประเมินชีวมวล คาร์บอน และ CO₂e ของต้นไม้จาก 3D point cloud (`.ply` / `.las` / `.laz`)
พร้อม provenance ที่ตรวจสอบย้อนกลับได้ทุกตัวเลข

**ผลลัพธ์ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง** — เป็นค่าประมาณที่บอกที่มาได้

## สถานะจริง (23 ส.ค. 2569)

- **NSC 2026 ไม่ผ่าน** — ไม่ใช่กรอบการทำงานอีกต่อไป
- **ทำคนเดียว** ไม่มีอาจารย์ ไม่มีสถาบัน ไม่มี TLS scanner ไม่มี GPU
- ใช้ได้แต่ **open data** เท่านั้น
- เป้าหมายใหม่: **ถูกวิทยาศาสตร์ + ตีพิมพ์ได้ + ใช้งานได้จริง**

## Tech Stack (เฉพาะที่ใช้จริง)

- **Web:** Next.js 14 + TypeScript + Tailwind + Three.js — deploy บน Vercel
- **API:** FastAPI synchronous · **ไม่มี database layer** (ถอดออกแล้ว ดู `docs/DATABASE_TEARDOWN.md`)
- **ML:** numpy + scipy + scikit-image + laspy · **ไม่มี GPU ไม่มี torch ในเส้นทาง production**
- **Auth/Storage:** Supabase

## Key Architecture Decisions

1. **รับ point cloud จากเครื่องสแกนเท่านั้น** — เส้นทางถ่ายภาพด้วยมือถือและแอป Flutter
   ถูกลบทิ้ง 9 ส.ค. 2569 ([ADR 0007](docs/decisions/0007-drop-the-photo-path.md))
   gate ไม่เคยผ่านเพราะไม่เคยรัน และเรื่อง scale ไม่เคยถูกแก้
2. **`tlsep` เป็น wood/leaf backend ที่ใช้จริง** — PointNet++ เป็น Experimental และถูก
   evidence gate บล็อกอยู่ (verdict `FAIL_METRICS`)
3. **Chave 2014 เป็นสมการหลัก** — T-VER เป็น opt-in และยังไม่เปลี่ยนค่า default
4. **Open-source ทั้งหมด** และข้อมูล validation ต้องเป็น open data

## กติกาที่สำคัญที่สุดของโปรเจกต์นี้

> **ตัวเลขทุกตัวที่เผยแพร่ ต้อง re-derive ได้จาก artefact ที่ commit ไว้**

- `sync_truth.py --check` ผูกเอกสารเข้ากับ manifest — เอกสาร drift จากหลักฐานไม่ได้
- `judge_demo_manifest.py check` ตรวจว่า artefact ที่เผยแพร่ยังตรงกับ pipeline ปัจจุบัน
- evidence gate ใน `provenance.py` เป็น fail-closed
- **ผลลัพธ์ที่ออกมาแย่ก็ commit** — `pointnet_independent_eval/result.json` commit ไว้ทั้งที่เป็น `FAIL_METRICS`
- **ห้าม recalibrate บน cohort ที่ใช้วัดผล** — เป็น defect เดียวกับที่ PointNet++ ถูกบล็อก

## Validation ที่มีอยู่

| cohort | n | ครอบคลุม |
|---|---:|---|
| Demol 2021 (เบลเยียม เขตอบอุ่น) | 65 | geometry เท่านั้น |
| Momo Takoudjou 2018 (แคเมอรูน เขตร้อน) | 61 | geometry + **allometric กับมวลที่ชั่งจริง** |

ตัวเลขที่ผู้ใช้ได้รับ: **DBH MAE 1.37 ซม.** (27 ต้นที่ผ่าน gate) · รายละเอียดใน
[`docs/ml/CAMEROON_EVIDENCE_CHAIN.md`](docs/ml/CAMEROON_EVIDENCE_CHAIN.md)

**ยังไม่ validate:** ขั้น 1–4 (ยังไม่เคยทดสอบบน plot จริง) · ขั้น 5 บนต้นไม้เขตร้อน ·
ขั้น 7 species classifier ยังเป็น Stub · และยังไม่เคยทดสอบกับต้นไม้ในไทย

## ⚠️ ข้อจำกัดของเครื่องผู้ใช้

**โน้ตบุ๊ก Acer Predator PHN16-71 ค้างตายสนิท 19 ครั้ง** (15 ครั้งใน 3 วัน 21-23 ส.ค.)
ไม่มี bugcheck ไม่มี dump ไม่มี WHEA

**บันทึกการตรวจ 23 ส.ค.: ไฟ AC หลุดเข้าหลุดออก + แบตเสื่อม 72% ที่ 53 cycles**
Event 105 บันทึก AC หลุด/กลับ 4 ครั้งใน 10 วินาที (20:00:01-20:00:11) แล้วเครื่องตาย 20:13:03
Memory Diagnostic 23 ส.ค. 13:24 รายงาน no errors ผลครั้งเดียวไม่ได้ตัดความเป็นไปได้ของปัญหา RAM หรือซอฟต์แวร์ทั้งหมด
รายละเอียดเดิมอยู่ใน memory `machine-freeze-root-cause` รอบตรวจ PR นี้ไม่ได้ตรวจ hardware ใหม่ จึงไม่ยืนยันว่าสาเหตุถูกพิสูจน์ครบหรือแก้ปัญหาแล้ว

- **ห้ามรัน full test suite บนเครื่องนี้** (`pytest tests/` ชุดเต็มใช้ ~29 นาที และเคยทิ้ง
  scratch ไว้ 93 GB จนเครื่องอืด) — ให้ GitHub Actions รับไป
- รันเฉพาะไฟล์ที่เกี่ยวข้องได้ (1–2 นาที) และบอกล่วงหน้าเสมอถ้าจะรันอะไรหนัก
- คู่มือแก้ปัญหา: artifact "Predator Freeze Triage"

## Glossary

| Term | Meaning |
|---|---|
| **DBH** | Diameter at Breast Height — เส้นผ่านศูนย์กลางลำต้นที่ 1.3 ม. |
| **QSM** | Quantitative Structure Model — โมเดลทรงกระบอกคำนวณปริมาตรไม้ |
| **CHM** | Canopy Height Model |
| **TLS** | Terrestrial Laser Scanning |
| **TGO / อบก.** | องค์การบริหารจัดการก๊าซเรือนกระจก |
| **T-VER** | โครงการลดก๊าซเรือนกระจกภาคสมัครใจของไทย · `T-VER-S-TOOL-01-01` คือคู่มือคำนวณคาร์บอนต้นไม้ |
| **Allometric** | สมการแปลง dimension ของต้นไม้ → biomass |
| **Chave 2014** | สมการ pantropical ที่ใช้เป็นเส้นทางหลัก |
| **ITD** | Individual Tree Detection |

## Preferences

- **ตอบเป็นภาษาไทย** (technical terms ใช้ EN ได้)
- **ความถูกต้องมาก่อนความน่าประทับใจ** — กรอบ "ทำให้กรรมการว้าว" เลิกใช้แล้ว
- ตัวเลขที่พูดต้องมาจากการวัด ไม่ใช่ความจำ — **รันแล้วดู อย่าอ่านแล้วเดา**
- commit message บอกว่า *อะไรผิด* ไม่ใช่ *เพิ่มอะไร*
- **ไม่มี non-ASCII ใน Python source** (console เป็น cp874 — UnicodeEncodeError ทำให้ process ตาย)
  เอกสาร markdown เป็นภาษาไทยได้ตามปกติ
