# ML Pipeline Details — TreeQ Carbon Platform

> อธิบายอัลกอริทึมที่โค้ดปัจจุบันรันจริง ไม่ใช่ target architecture

---

<!-- TREEQ_TRUTH_START -->
### Verified truth snapshot (generated)

- Baseline: `tlsep` — **Implemented**.
- PointNet++: **Experimental**, not promoted; reviewed evidence never changes the default automatically.
- Wan 2021 held-out: Wood IoU `0.418`, Leaf IoU `0.808`, Mean IoU `0.613`, accuracy `0.831`. The held-out loader was also used for best-epoch selection.
- Demol isolated-tree validation (65 trees): DBH MAE `0.898318 cm`; Volume MAPE `11.520556%`. This is not an eight-stage or carbon validation.
- Cameroon destructive tropical validation (61 trees, 60 measurable): DBH MAE `1.369868 cm` over the `27` trees the shipped gate passes, `33` refused; `11.254575 cm` if every measurable tree is forced to answer, which is the ceiling and not the error.
- Cameroon allometric, scored against harvested mass: Chave 2014 median APE `13.999223%` against T-VER `20.850468%`, with the measurement contributing `5.800567%` at the median. These clouds arrive leaf-stripped and are single trees, so this validates neither stage 5 nor stages 1-4, and Cameroon is not Thailand.
- Independent PointNet review: verdict `FAIL_METRICS`; candidate/baseline external macro Wood IoU `0.23728726507501768`/`0.1958779956856453`.
- Independent downstream candidate/baseline: DBH MAE `1.1591405814498605`/`1.1339476465903928` cm; Height MAE `0.9508502244897976`/`0.5433234000000015` m; Volume MAPE `21.74924193798788`/`18.928262273343613`%; measurable trees `49`/`65`.
- Deterministic core demo: `3` trees, `1036.09 kg C`, `3798.99 kg CO2e`; analyzed commit `8cf3058c1f61` with a clean worktree.
- Species classification: **Stub**. Carbon stock/CO2e estimates are not certified credits.
<!-- TREEQ_TRUTH_END -->

## Overview

```text
Input .las/.laz/.ply/.txt/.xyz/.csv
  │
  ├─ 1. Percentile-grid ground segmentation
  ├─ 2. KNN-IDW height normalization
  ├─ 3. Max-Z CHM + morphology
  ├─ 4. Local maxima + watershed tree segmentation
  ├─ 5. tlsep/PCA wood-leaf baseline
  │       └─ PointNet++ backend: Experimental, ต้องระบุ checkpoint
  ├─ 6. RANSAC DBH + max-Z height + taper volume
  ├─ 7. Species classification: Stub / caller-supplied default
  └─ 8. species_db allometric or Chave fallback
          ↓
JSON: per-tree geometry, biomass, carbon stock, CO2e + run provenance
```

Algorithm identity ของแต่ละ run ถูกแนบใน `metadata.algorithms` จาก
`services/ml/pipeline/provenance.py` เพื่อไม่ให้ชื่อเชิงวิจัยถูกสับสนกับ implementation จริง

## Input and loading

`process_point_cloud()` อ่านไฟล์ด้วย `pipeline.field_eval.load_point_cloud()` และจำกัดจำนวนจุดด้วย
`max_points` ซึ่ง default เป็น 200,000 จุด เส้นทางนี้ไม่ได้ทำ outlier filtering หรือ voxel downsampling
โดยอัตโนมัติก่อน 8 ขั้น ดังนั้นเอกสารหรือ demo ต้องไม่กล่าวว่าทำ preprocessing สองอย่างนี้แล้ว

## Step 1: Ground segmentation

**Status:** Implemented
**Code identity:** `percentile_grid`
**File:** `services/ml/pipeline/ground_classification.py`

โค้ดแบ่งแกน XY เป็น grid ขนาด default 1 เมตร หา percentile ที่ 5 ของ Z ในแต่ละ cell
แล้วจัดจุดที่สูงไม่เกิน candidate ground + 0.3 เมตรเป็น ground

```python
classify_ground_array(
    points,
    grid_resolution=1.0,
    percentile=5.0,
    z_threshold=0.3,
)
```

นี่เป็น heuristic ที่อ้างอิงแนวคิด ground filtering แต่ **ไม่ใช่ Cloth Simulation Filter (CSF)**
และไม่ได้เรียก PDAL ใน array pipeline ปัจจุบัน CSF เป็น target/future replacement เท่านั้น

## Step 2: Height normalization

**Status:** Implemented
**Code identity:** `knn_idw`
**File:** `services/ml/pipeline/height_normalization.py`

สร้าง `cKDTree` จาก ground points แล้วประมาณ terrain Z ใต้แต่ละจุดด้วย inverse-distance weighted mean
ของ ground neighbors ใกล้สุด default 5 จุด จากนั้นคำนวณ `z_normalized = z - terrain_z`

โค้ดปัจจุบัน **ไม่ใช่ TIN interpolation**

## Step 3: Canopy Height Model

**Status:** Implemented
**Code identity:** `max_z_morphology`
**File:** `services/ml/pipeline/canopy_height_model.py`

Rasterize maximum normalized Z ต่อ cell ที่ resolution default 0.5 เมตร แล้วใช้ morphological closing
ขนาด 2×2 เพื่อเติม empty cells บางส่วน

โค้ดปัจจุบัน **ไม่ใช่ full multi-threshold pit-free CHM** ของ Khosravipour et al. 2014;
pit-free เป็น Phase 2 target ที่ระบุใน source comments

## Step 4: Individual-tree segmentation

**Status:** Implemented
**Code identity:** `watershed`
**File:** `services/ml/pipeline/tree_segmentation.py`

1. ตัด CHM ต่ำกว่า `min_height=4.0 m`
2. หา local maxima ด้วย `min_distance=3` pixels
3. ใช้ maxima เป็น markers ของ watershed บน negative CHM
4. map labels กลับไปยัง points และไม่ assign จุดต่ำกว่า 1.5 เมตร

ผลคือ integer tree IDs โดย `0` หมายถึง unassigned

## Step 5: Wood-leaf segmentation

### tlsep baseline

**Status:** Implemented และเป็น default
**Code identity:** `tlsep`
**File:** `services/ml/pipeline/wood_leaf_separation.py`

implementation เป็น TLSeparation-inspired local PCA heuristic: คำนวณ eigenvalue ratios,
linearity, planarity และ verticality จาก K-nearest neighbors แล้วให้ class `0=wood`, `1=leaf`
ไม่ต้องใช้ checkpoint และทำงานบน CPU ได้

### PointNet++ candidate

**Status:** Experimental, not promoted
**Code identity:** `pointnet`
**Files:** `services/ml/pipeline/wood_leaf_separation.py`, `services/ml/training/pointnet2_seg.py`

backend นี้ต้องรับ `.pt` checkpoint อย่างชัดเจน จุดน้อยกว่า 512 จุดจะ fallback ไป heuristic
ผล Wan ที่บันทึกไว้คือ Wood IoU 0.418, Leaf IoU 0.808, Mean IoU 0.613 และ accuracy 0.831
เป็น spatially separated development split with a 2.5 m excluded band; native tree IDs are unavailable,
and the same dev loader selected the epoch. ดังนั้น spatial split นี้ไม่พิสูจน์ unseen-tree separation
และไม่ใช่ independent final-test หรือ promotion evidence; PointNet++ จึงห้ามเรียกว่า production default

Promotion gate อยู่ใน `pipeline.provenance.evaluate_promotion()` และต้องผ่าน Wood IoU improvement,
DBH/height/volume non-regression, measurable-tree count, checkpoint identity, training provenance และ
reproducible independent real test พร้อมกัน

## Step 6: QSM-derived geometry

**Status:** Implemented with limitations
**Code identity:** `ransac_dbh_maxz_height_taper_volume`
**File:** `services/ml/pipeline/qsm.py`

- DBH: RANSAC circle fit จาก wood points ใน slice รอบ 1.3 เมตร หนา 0.3 เมตร
- Height: maximum normalized Z ของ points ที่ส่งเข้า QSM
- Stem volume: `π/4 × DBH² × H × 0.50`
- Branch volume: `0.0`
- `n_cylinders`: `1` ใน default path

ไฟล์มีฟังก์ชัน `estimate_volume_sectional()` สำหรับทดลอง stacked cylinders แต่ `compute_qsm()`
จงใจใช้ taper equation เพราะ sectional method overestimate เมื่อ heuristic wood points ยังมี crown/branch blobs
ดังนั้น implementation นี้ **ไม่ใช่ full TreeQSM**, ไม่มี skeleton/branch-axis cylinders และห้ามเคลม branch volume

Demol isolated-tree validation 65 ต้นให้ DBH MAE 0.898318 cm, Height MAE 0.543323 m
และ Volume MAPE 11.520556% ภายใต้ preprocessing เฉพาะของ evaluation script
ผลนี้ไม่ใช่ full eight-stage หรือ carbon validation

## Step 7: Species classification

**Status:** Stub
**Code identity:** `stub`
**File:** `services/ml/pipeline/species_classifier.py`

`load()`, `classify()` และ `classify_batch()` raise `NotImplementedError` ทั้งหมด
pipeline orchestrator ไม่เรียก ResNet; ใช้ `default_species` ที่ caller ส่งมาเพื่อเลือกสมการ allometric
หรือใช้ unknown-species fallback เมื่อไม่ส่งค่า

ResNet-50/TFLite, iNaturalist training data และ on-device inference เป็น roadmap ไม่ใช่สิ่งที่ทำเสร็จ

## Step 8: Allometric carbon calculation

**Status:** Implemented
**Code identity:** `species_db_or_chave_fallback`
**Files:** `services/ml/pipeline/allometric.py`, `services/ml/data/species_db.csv`

เส้นทาง `auto` เลือกดังนี้:

1. ถ้า species อยู่ใน CSV และมี `agb_a/agb_b/agb_c` ครบ ใช้สมการ species-specific
2. ไม่เช่นนั้นใช้ Chave 2014 pantropical equation กับ wood density จาก species หรือ default 600 kg/m³
3. เพิ่ม below-ground biomass ด้วย root-to-shoot ratio
4. คูณ carbon fraction และ 44/12 เพื่อรายงาน carbon stock กับ CO₂e

```text
AGB_species = a × DBH^b × H^c
AGB_Chave   = 0.0673 × (ρ × DBH² × H)^0.976
BGB         = AGB × root_to_shoot
Carbon      = (AGB + BGB) × carbon_fraction
CO2e        = Carbon × 44/12
```

`species_db.csv` เป็น source of truth ของ coefficients ใน repo ปัจจุบัน การเทียบ coefficients ทุกแถวกับ
TGO Forestry Guideline 2017 ต้นฉบับยังเป็นงานค้าง จึงห้ามกล่าวว่าระบบผ่าน TGO certification

## Output and provenance

`PipelineResult.metadata` มี fields ที่ API validate ด้วย `AnalyzeMetadata`:

```json
{
  "pipeline_version": "0.3.0",
  "git_commit": "<40-character commit>",
  "git_dirty": false,
  "wood_leaf_backend": "tlsep",
  "checkpoint_sha256": null,
  "input_sha256": "<normalized XYZ SHA-256>",
  "algorithms": {
    "ground_segmentation": "percentile_grid",
    "height_normalization": "knn_idw",
    "chm": "max_z_morphology",
    "tree_segmentation": "watershed",
    "wood_leaf": "tlsep",
    "qsm": "ransac_dbh_maxz_height_taper_volume",
    "species": "stub",
    "allometric": "species_db_or_chave_fallback"
  },
  "evidence_status": "baseline",
  "candidate_status": "candidate_not_evaluated",
  "n_input_points": 145123,
  "status": "ok"
}
```

`input_sha256` เป็น hash ของ normalized little-endian float64 XYZ array ไม่ใช่ raw file bytes

## Reproducible core demo

```powershell
cd services/ml
python scripts/run_core_demo.py --output-dir ../../temp/core-demo --repo-root ../..
```

runner สร้าง fixture seed 42, รัน `tlsep` path สองครั้ง แล้วบังคับให้ normalized JSON hash และ PLY hash
เท่ากัน Reviewed result อยู่ใน `docs/evidence/core_demo_manifest.json` และใช้ยืนยัน reproducibility เท่านั้น

## Known limits

- ground step ไม่ใช่ CSF
- CHM ไม่ใช่ full pit-free
- PointNet++ ยัง Experimental; reviewed verdict `FAIL_METRICS` จึงไม่ผ่าน promotion gate
- QSM path ไม่มี branch-level model และใช้ taper volume
- species classifier เป็น Stub
- Demol geometry ไม่ validate carbon
- carbon stock/CO₂e estimates ไม่ใช่ certified credits
- production API/worker deployment ยังไม่พร้อมต่อเนื่อง
