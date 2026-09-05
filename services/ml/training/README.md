# Phase 2 — PointNet++ Wood-Leaf Training (Sprint P1 / G2)

Train the deep-learning wood/leaf segmenter that replaces the Phase 1 PCA
heuristic. **Goal: validation wood IoU ≥ 0.70, beating the PCA baseline.**

Training data is generated on the fly from the synthetic forest generator
(`pipeline/synthetic.py`) — no dataset download, fully reproducible.

## Files

| File | What | Needs torch? |
|---|---|---|
| `woodleaf_dataset.py` | Build labelled (wood/leaf) samples from synthetic trees | No |
| `metrics.py` | `iou_score()` per-class IoU | No |
| `pointnet2_seg.py` | PointNet++ SSG segmentation model | Yes |
| `train_woodleaf.py` | Training CLI (Colab/Kaggle-ready) | Yes |

The torch-free parts have unit tests in `../tests/test_woodleaf_training.py`
(run on any machine). The model tests run wherever torch is installed.

## Run on Google Colab / Kaggle (free GPU)

```bash
# 1. clone the repo and cd into the ML service
!git clone https://github.com/Remote55/treeq.git
%cd treeq/services/ml

# 2. minimal deps (Colab already has torch + numpy + scipy)
!pip install scipy

# 3. train (≈ a few min on a T4)
!python -m training.train_woodleaf --epochs 60 --n-train 256 --n-val 48 \
        --n-points 2048 --batch-size 8 --out woodleaf_pn2.pt
```

The script prints per-epoch loss + validation wood IoU and saves the best
checkpoint to `--out`.

## Run locally (CPU — slow, for a smoke check only)

```bash
cd services/ml
pip install -e ".[cpu]"            # installs torch CPU
python -m training.train_woodleaf --epochs 5 --n-train 16 --n-val 4 --out woodleaf_pn2.pt
```

## Use the trained model in the pipeline

```python
from pipeline.wood_leaf_separation import WoodLeafSegmenter

seg = WoodLeafSegmenter(model_path="woodleaf_pn2.pt", backend="pointnet")
seg.load()
labels = seg.segment(points)        # (N,) 0=wood, 1=leaf
# clouds with < 512 points auto-fall back to the rule-based segmenter
```

## Compare against the PCA baseline (G2 acceptance figure)

Once you have a checkpoint, score PointNet++ vs the Phase-1 PCA heuristic on the
same held-out trees → table + `fig17_woodleaf_pca_vs_pointnet.png`:

```bash
python notebooks/compare_woodleaf.py --model woodleaf_pn2.pt
# (omit --model to see just the PCA baseline)
```

## Next steps for G2 (see docs/P1_SPRINT_PLAN.md)

- [ ] Run full training on Colab → confirm val IoU ≥ 0.70
- [ ] Add a small **manually-labelled real tree** test set (CloudCompare) for an honest IoU number
- [x] Comparison harness ready — `notebooks/compare_woodleaf.py` (PointNet++ vs PCA)
- [ ] (optional) export to TFLite for the mobile species/segmentation path

> ⚠️ Checkpoints (`*.pt`) are large — do **not** commit them to git. Publish the
> final model on Hugging Face Hub (per the proposal) or attach to a GitHub Release.
