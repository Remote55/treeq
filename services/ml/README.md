# 🧠 ML Pipeline (Python + PyTorch)

> [!CAUTION]
> **Mixed current/target service notes.** Current default wood/leaf backend is `tlsep`.
> PointNet++ is Experimental/not promoted (Wan Wood/Leaf/Mean IoU `0.418/0.808/0.613` with
> selection/provenance caveat). Species classification is Stub. COLMAP/OpenMVS require external
> binaries and are not a verified photo-to-carbon production path; RunPod is a Planned deployment target.
> Use `docs/evidence/core_demo_manifest.json` and `docs/ml/PIPELINE.md` as truth.

> **Owner:** User
> **Tech:** Python 3.11 + PyTorch + Open3D + PointNet++ + COLMAP

---

## Overview

ML Pipeline ทำหน้าที่:
1. รับไฟล์ LiDAR `.las/.laz` หรือ Photogrammetry output `.ply`
2. ประมวลผล point cloud → แยกต้นไม้ทีละต้น
3. แยกใบ vs ลำต้น/กิ่ง (Wood-Leaf Segmentation) ด้วย Deep Learning
4. คำนวณปริมาตรไม้ด้วย QSM (Quantitative Structure Model)
5. แปลงเป็น Biomass + Carbon ด้วย Allometric Equation

**รัน:** Cloud GPU (RunPod Serverless) สำหรับ Production / Google Colab สำหรับ Dev

---

## Folder Structure

```
services/ml/
├── README.md                         (this file)
├── pyproject.toml
├── Dockerfile.gpu                    Production image (CUDA)
├── Dockerfile.cpu                    Dev image (no GPU)
├── .env.example
├── runpod_handler.py                 RunPod serverless entry
├── pipeline/
│   ├── __init__.py
│   ├── ground_classification.py      Step 1: CSF algorithm
│   ├── height_normalization.py       Step 2: DTM subtraction
│   ├── canopy_height_model.py        Step 3: Pit-free CHM
│   ├── tree_segmentation.py          Step 4: Watershed (lidR equivalent)
│   ├── wood_leaf_separation.py       Step 5: PointNet++ DL model
│   ├── qsm.py                        Step 6: Cylinder fitting
│   ├── allometric.py                 Step 7: Biomass + Carbon calc
│   ├── species_classifier.py         Step 8: ResNet RGB classifier
│   └── main.py                       Pipeline orchestrator
├── photogrammetry/
│   ├── __init__.py
│   ├── colmap_wrapper.py             COLMAP SfM
│   └── openmvs_wrapper.py            OpenMVS dense reconstruction
├── models/                           Trained model weights (gitignored if > 50MB)
│   ├── pointnet_wood_leaf_v1.pth
│   └── resnet_species_v1.pth
├── notebooks/                        Jupyter exploration
│   ├── 01_explore_lidR_workflow.ipynb
│   ├── 02_pointnet_wood_leaf_train.ipynb
│   ├── 03_qsm_validation.ipynb
│   ├── 04_photogrammetry_test.ipynb
│   └── 05_species_classifier_train.ipynb
├── scripts/
│   ├── download_neon.py              Download sample LiDAR data
│   ├── train_pointnet.py             Training script
│   ├── train_species.py
│   ├── evaluate_pipeline.py          Benchmark accuracy
│   └── export_tflite.py              Mobile model export
├── data/                             (gitignored)
│   ├── raw/
│   ├── processed/
│   └── annotations/
└── tests/
    ├── test_ground_classification.py
    ├── test_allometric.py
    └── ...
```

---

## Pipeline Overview

```
Input: .las / .laz / .ply
         │
         ▼
┌─────────────────────────────────────┐
│ Step 1: Ground Classification (CSF)  │
│ → Mark ground vs non-ground points   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 2: Height Normalization         │
│ → Subtract DTM, height = 0 at ground │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 3: Canopy Height Model (CHM)    │
│ → Raster of canopy heights           │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 4: Tree Segmentation            │
│ → Watershed on CHM → treeID per pt   │
└─────────────────────────────────────┘
         │
         ▼ (per tree)
┌─────────────────────────────────────┐
│ Step 5: Wood-Leaf Separation         │
│ → PointNet++ → wood/leaf label       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 6: QSM (Cylinder Fitting)       │
│ → Wood points → cylinders → volume   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 7: Allometric → Biomass → C     │
│ → V × ρ × C_frac = Carbon kg         │
└─────────────────────────────────────┘
         │
         ▼
Output: JSON (per tree: DBH, H, V, Biomass, Carbon, CO2eq)
```

---

## Setup

### Local (CPU dev)
```bash
cd services/ml

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,cpu]"
```

### Local (GPU)
```bash
pip install -e ".[dev,gpu]"
# Make sure CUDA 11.8+ installed
```

### Google Colab
```python
# In notebook
!pip install -e /content/treeq/services/ml[gpu]
```

---

## pyproject.toml

```toml
[project]
name = "carbonscan-ml"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "numpy>=1.26.0",
    "scipy>=1.13.0",
    "scikit-learn>=1.5.0",
    "pandas>=2.2.0",
    "open3d>=0.18.0",
    "laspy[lazrs]>=2.5.0",
    "pdal>=3.4.0",
    "pyproj>=3.6.0",
    "shapely>=2.0.0",
    "rasterio>=1.3.0",
    "pillow>=10.3.0",
    "tqdm>=4.66.0",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
cpu = [
    "torch>=2.3.0",
    "torchvision>=0.18.0",
]

gpu = [
    "torch>=2.3.0",
    "torchvision>=0.18.0",
    "torch-scatter",
    "torch-sparse",
    "torch-cluster",
]

dev = [
    "jupyterlab>=4.2.0",
    "ipywidgets>=8.1.0",
    "matplotlib>=3.9.0",
    "seaborn>=0.13.0",
    "pytest>=8.2.0",
    "ruff>=0.4.0",
    "black>=24.4.0",
    "wandb>=0.17.0",         # experiment tracking
]
```

---

## Module Implementations (Skeletons)

### `pipeline/ground_classification.py`
```python
"""Ground point classification using CSF (Cloth Simulation Filter)."""
import laspy
import numpy as np
import pdal

def classify_ground(input_path: str, output_path: str) -> None:
    """
    Classify ground vs non-ground points using CSF algorithm.

    Based on Zhang et al. (2016): "An Easy-to-Use Airborne LiDAR Data
    Filtering Method Based on Cloth Simulation"
    """
    pipeline_json = {
        "pipeline": [
            input_path,
            {"type": "filters.csf", "resolution": 0.5, "threshold": 0.5},
            output_path,
        ]
    }
    pipeline = pdal.Pipeline(json.dumps(pipeline_json))
    pipeline.execute()
```

### `pipeline/tree_segmentation.py`
```python
"""Individual Tree Detection using Watershed on CHM."""
import numpy as np
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

def detect_trees(chm: np.ndarray, min_height: float = 4.0) -> np.ndarray:
    """
    Watershed segmentation on Canopy Height Model.

    Returns: 2D array same shape as CHM, with tree IDs (0 = no tree)
    """
    # Find local maxima (treetops)
    maxima = peak_local_max(chm, min_distance=3, threshold_abs=min_height)

    # Markers for watershed
    markers = np.zeros_like(chm, dtype=int)
    for i, (y, x) in enumerate(maxima, start=1):
        markers[y, x] = i

    # Watershed
    labels = watershed(-chm, markers, mask=(chm > min_height))
    return labels
```

### `pipeline/wood_leaf_separation.py`
```python
"""Wood vs Leaf semantic segmentation using PointNet++."""
import torch
from .models.pointnet2 import PointNet2SemSeg

class WoodLeafSegmenter:
    def __init__(self, model_path: str, device: str = "cuda"):
        self.device = device
        self.model = PointNet2SemSeg(num_classes=2)  # wood, leaf
        self.model.load_state_dict(torch.load(model_path, map_location=device))
        self.model.to(device).eval()

    @torch.no_grad()
    def segment(self, points: np.ndarray) -> np.ndarray:
        """
        Args:
            points: (N, 3) array of XYZ coordinates

        Returns:
            labels: (N,) array of 0 (wood) or 1 (leaf)
        """
        # Sample to fixed size (e.g., 4096 points per chunk)
        # Run model in batches
        # Return labels
        ...
```

### `pipeline/allometric.py`
```python
"""Allometric biomass calculation using TGO equations."""
import pandas as pd

# Loaded from species_db.csv (matches DB)
SPECIES_DB = pd.read_csv("data/species_db.csv").set_index("name_sci")

def calculate_biomass(
    species_sci: str,
    dbh_cm: float,
    height_m: float,
) -> dict:
    """
    Compute aboveground biomass + carbon from DBH and height.

    AGB = a × DBH^b × H^c   (from TGO Forestry Sector Guideline 2017)
    BGB = AGB × root_to_shoot_ratio
    Biomass = AGB + BGB
    Carbon = Biomass × C_fraction (0.47 IPCC)
    CO2eq = Carbon × 44/12

    Args:
        species_sci: Scientific name (e.g., "Tectona grandis")
        dbh_cm: Diameter at breast height in cm
        height_m: Total height in meters

    Returns:
        dict with: agb_kg, bgb_kg, biomass_kg, carbon_kg, co2eq_kg
    """
    sp = SPECIES_DB.loc[species_sci]

    agb = sp["agb_a"] * (dbh_cm ** sp["agb_b"]) * (height_m ** sp["agb_c"])
    bgb = agb * sp["root_to_shoot_ratio"]
    biomass = agb + bgb
    carbon = biomass * sp["carbon_fraction"]
    co2eq = carbon * (44 / 12)

    return {
        "agb_kg": agb,
        "bgb_kg": bgb,
        "biomass_kg": biomass,
        "carbon_kg": carbon,
        "co2eq_kg": co2eq,
    }
```

### `runpod_handler.py` (Serverless Entry)
```python
"""RunPod Serverless GPU handler."""
import runpod
from pipeline.main import process_point_cloud

def handler(event):
    """
    RunPod calls this function for each job.
    Input format: { "input": { "job_id": ..., "las_url": ... } }
    """
    job_id = event["input"]["job_id"]
    las_url = event["input"]["las_url"]
    callback_url = event["input"]["callback_url"]

    # Download .las from URL
    local_path = download_file(las_url)

    # Process
    result = process_point_cloud(local_path, progress_callback=lambda p: notify(callback_url, p))

    # Upload result
    output_url = upload_to_storage(result)

    return {"output_url": output_url, "tree_count": len(result["trees"])}

runpod.serverless.start({"handler": handler})
```

---

## Training (Notebooks)

### Wood-Leaf Separation
```bash
# Open notebook
jupyter lab notebooks/02_pointnet_wood_leaf_train.ipynb

# Or run script
python scripts/train_pointnet.py \
    --data-dir data/processed/neon \
    --epochs 100 \
    --batch-size 4 \
    --lr 1e-3 \
    --output models/pointnet_wood_leaf_v1.pth
```

### Species Classifier
```bash
python scripts/train_species.py \
    --data-dir data/processed/species_images \
    --backbone resnet50 \
    --epochs 30
```

### Export TFLite (Mobile)
```bash
python scripts/export_tflite.py \
    --pytorch-model models/resnet_species_v1.pth \
    --output ../../apps/mobile/assets/ml_models/tree_species_v1.tflite \
    --quantize int8
```

---

## Datasets

### NEON (USA — Primary)
```bash
python scripts/download_neon.py --site OSBS --year 2022 --output data/raw/neon/
```

### Sample Thai (จาก GISTDA — ถ้าได้)
- ต้องติดต่อขออนุญาตล่วงหน้า

📖 ดู [docs/ml/DATASETS.md](../../docs/ml/DATASETS.md)

---

## Testing

```bash
pytest

# With GPU benchmarks
pytest --gpu

# Specific module
pytest tests/test_allometric.py -v
```

---

## Performance Targets

| Step | Target Time | Hardware |
|---|---|---|
| Ground classification | 30s/100MB | CPU |
| Tree segmentation | 1 min/plot | CPU |
| Wood-leaf seg | 5 sec/tree | GPU |
| QSM | 2 sec/tree | CPU |
| **End-to-end** | **< 10 min/plot** | **GPU** |

Validation metrics:
- Wood-leaf IoU ≥ 0.70
- DBH RMSE ≤ 5 cm
- Height RMSE ≤ 1 m

---

📖 **See also:**
- [docs/ml/PIPELINE.md](../../docs/ml/PIPELINE.md) — Pipeline details
- [docs/ml/ALLOMETRIC.md](../../docs/ml/ALLOMETRIC.md) — TGO equations
- [docs/ml/DATASETS.md](../../docs/ml/DATASETS.md) — Data sources
