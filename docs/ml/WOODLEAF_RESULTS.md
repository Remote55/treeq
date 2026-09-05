# Wood/Leaf Segmentation — Results Log

> เก็บผลทุก variant ตามที่รันทดลองจริง พร้อมแยก synthetic, zero-shot และ same-environment
> ตัวเลข Wan ด้านล่างมาจาก spatial held-out loader แต่ loader เดียวกันถูกใช้เลือก best epoch
> จึงไม่ใช่ independent final test สำหรับ promotion gate
> Wan นี้คือ **spatially separated development split with a 2.5 m excluded band**;
> native tree IDs are unavailable, and the same dev loader selected the epoch.
> จึงไม่พิสูจน์ unseen-tree separation และไม่ใช่ promotion evidence

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

## Production decision

- `tlsep`: **Implemented baseline/default** เพราะไม่ต้องใช้ checkpoint และ core path รันซ้ำได้
- PointNet++: **Experimental candidate** แม้มีผลดีกว่าบน synthetic และมี Wan training result
- ยังไม่ promote PointNet++ เพราะ reviewed independent verdict คือ `FAIL_METRICS`: external macro Wood IoU
  point estimate สูงกว่า `tlsep` แต่ 95% CI ของ delta คร่อมศูนย์ และ formal downstream criteria ไม่ผ่าน

## Synthetic held-out benchmark

| Method | Recorded Mean IoU | Scope |
|---|---:|---|
| PCA heuristic (`tlsep`) | 0.7692083333 | Synthetic only |
| PointNet++ (`pointnet`) | 0.977625 | Synthetic only |
| Delta | +0.2084166667 | Synthetic only |

ผล synthetic แสดงว่า training setup เรียน fixture distribution ได้ แต่ใช้เป็นหลักฐาน production promotion ไม่ได้

## Real TLS — Wan 2021

### Prior runs: synthetic-trained to real

ค่าชุดนี้เป็น approximate historical development/zero-shot observations ไม่ใช่ promotion evidence:

| Run | Init | Augment | Class weight | Wood IoU | Leaf IoU | Mean IoU |
|---|---|---|---|---:|---:|---:|
| zero-shot | synthetic-only | — | — | ~0.18 | ~0.62 | ~0.33 |
| fine-tune | synthetic checkpoint | — | none | ~0.19 | ~0.63 | ~0.41 |
| fine-tune + CW | synthetic checkpoint | — | auto | ~0.24 | ~0.07 | ~0.16 |

### Same-environment matrix — Colab run 2026-06-29

Split นี้เป็น spatially separated development split with a 2.5 m excluded band;
native tree IDs are unavailable, and the same dev loader selected the epoch.
Metrics เป็น pooled per-point IoU จึงไม่ใช่ independent final-test evidence.

| # | Init | Synthetic augment | Class weight | Train tiles | Wood IoU | Leaf IoU | Mean IoU | Accuracy |
|---|---|---:|---|---:|---:|---:|---:|---:|
| 1 | scratch | 0 | none | 339 | 0.285 | 0.803 | 0.544 | 0.817 |
| 2 | scratch | 0 | auto | 339 | 0.381 | 0.790 | 0.585 | 0.814 |
| **3** | scratch | 200 | none | 539 | **0.418** | **0.808** | **0.613** | **0.831** |
| 4 | scratch | 200 | auto | 539 | 0.332 | 0.770 | 0.551 | 0.793 |

Variant 3 เป็น best recorded run ใน matrix นี้ แต่คำว่า best หมายถึง best บน development loader เดียวกับที่ใช้
best-epoch selection ด้วย ไม่ใช่ independent final-test performance หรือ promotion evidence

## Findings ที่รายงานได้

- Same-environment training ยกระดับ best recorded Mean IoU เป็น `0.613` และ Wood IoU เป็น `0.418`
- Synthetic augmentation ใน matrix นี้เพิ่ม Wood IoU จาก `0.285` เป็น `0.418`
- Auto class weighting ช่วย variant ที่ไม่มี augmentation (`0.285 → 0.381`) แต่ลดผลเมื่อใช้ augmentation
- Wood IoU `0.418` ยังต่ำกว่า research target `0.70`
- งานถัดไปห้ามใช้ Cohort A ปัจจุบันหรือ Demol เพื่อ train, tune หรือ model selection; ต้อง freeze candidate/protocol
  ก่อนเปิดผล แล้วใช้ independent final cohort/split ใหม่ที่ไม่เคยเปิดผลเป็น decisive gate รอบถัดไป
- reviewed run ปัจจุบันมี checkpoint/training provenance ครบแต่ไม่ผ่าน downstream non-regression และต้องคงผล
  Cohort A + Demol รอบนี้เป็น immutable historical evidence เท่านั้น

## สิ่งที่ห้ามสรุปจากผลนี้

- ห้ามเรียก `0.613` ว่า Wood IoU; Wood IoU จริงคือ `0.418`
- ห้ามกล่าวว่า PointNet++ เป็น default หรือ production-ready
- ห้ามกล่าวว่า held-out result เป็น independent final test
- ห้ามใช้ synthetic `0.977625` เป็นความแม่นบนต้นไม้จริง
- ห้ามอนุมานว่า Wood IoU ที่ดีขึ้นทำให้ DBH, volume หรือ carbon ดีขึ้นจนกว่าจะวัดร่วมกัน

## Honest reporting arc

```text
synthetic Mean IoU 0.977625
→ real zero-shot approximate Mean IoU 0.33
→ Wan same-environment best recorded Mean IoU 0.613 / Wood IoU 0.418
→ reviewed independent external cohort (10 non-Thai TLS trees) + locked reused Demol downstream:
  `FAIL_METRICS`, no promotion
```
