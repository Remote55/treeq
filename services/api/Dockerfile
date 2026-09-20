# syntax=docker/dockerfile:1.7
#
# One image that can actually answer POST /api/v1/upload/analyze.
#
# The previous version copied only services/api, so the API started, reported
# healthy, and failed every analysis: the route shells out to the ML pipeline,
# which was not in the image. The build context is therefore the REPOSITORY
# ROOT, not services/api:
#
#     docker build -f services/api/Dockerfile \
#       --build-arg GIT_COMMIT=$(git rev-parse HEAD) \
#       --build-arg GIT_DIRTY=$(test -z "$(git status --porcelain)" && echo false || echo true) \
#       -t treeq-api .
#
# There is no second interpreter. pipeline_runner falls back to sys.executable
# when it finds no services/ml/.venv, so API and pipeline share one environment.
#
# No GPU, and no torch. The production wood/leaf backend is tlsep - PCA over
# cKDTree neighbourhoods, pure numpy - and torch is imported inside
# WoodLeafSegmenter.load(), which only the pointnet backend calls. Installing it
# would roughly triple the image for code this deployment never executes.

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# build-essential is for wheels with no manylinux build (open3d and laspy's
# lazrs carry C extensions). libpq-dev, libgeos-dev and libproj-dev were here
# too, for asyncpg and geoalchemy2; the database layer is gone, and with it the
# reason to compile against Postgres and GIS headers.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# README.md is not documentation here, it is a build input: pyproject declares
# `readme = "README.md"` and hatchling reads it while generating metadata.
# Copying only pyproject.toml therefore failed the build outright -
#
#     OSError: Readme file does not exist: README.md
#
# - at this line, before anything else in the file could be wrong. Reproduced by
# building from a directory holding just pyproject.toml, which is what this
# stage was.
#
# The install is here for the dependency set, not for the package: `app/` is
# deliberately not in this stage, so the wheel hatchling builds is empty (about
# 1.5 kB) and the application is imported from WORKDIR in the runtime stage.
# That is why only these two files are copied - a layer that changed with every
# source edit would rebuild the whole dependency tree on each commit. It was
# `pip install -e .`, which additionally leaves an editable finder pointing at
# /build, a path the runtime stage does not have.
COPY services/api/pyproject.toml services/api/README.md ./
RUN pip install --upgrade pip && \
    pip install .

# The pipeline's runtime surface, not services/ml/pyproject.toml. That file
# also pulls pandas, geopandas, rasterio, opencv, shapely and torch, none of
# which the eight stages of an analysis import. Kept in step by
# tests/test_runtime_import_surface.py, which fails if a stage starts importing
# something that is not listed here.
RUN pip install \
    "numpy>=1.26.0" \
    "scipy>=1.13.0" \
    "scikit-image>=0.23.0" \
    "open3d>=0.18.0" \
    "laspy[lazrs]>=2.5.0" \
    "click>=8.1.0"

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim AS runtime

# A container has no .git and no git binary, so provenance is baked here.
# resolve_git_commit reads TREEQ_GIT_COMMIT and refuses to start a run without
# it; git_worktree_dirty reports dirty when TREEQ_GIT_DIRTY is unset, because
# "nobody recorded whether the checkout was clean" and "the checkout was clean"
# are not the same claim.
ARG GIT_COMMIT
ARG GIT_DIRTY=true

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    TREEQ_GIT_COMMIT=${GIT_COMMIT} \
    TREEQ_GIT_DIRTY=${GIT_DIRTY} \
    ML_DIR=/app/services/ml

# libegl1, libgl1 and libgomp1 are Open3D's; curl is for HEALTHCHECK.
# libpq5, libgeos-c1v5 and libproj25 went with the database layer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl1 \
    libgl1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# API
COPY --chown=app:app services/api/app/ ./app/

# ML pipeline. `data/` carries species_db.csv, which allometric.load_species_db
# resolves relative to its own file, so the layout under services/ml must match
# the repository's.
COPY --chown=app:app services/ml/pipeline/ ./services/ml/pipeline/
COPY --chown=app:app services/ml/data/ ./services/ml/data/

# /app/job-uploads was created here for the async queue's handoff between the
# API and a worker. The queue is gone: nothing called it and no deployment ever
# started the worker. Analysis is synchronous and writes to the system temp
# directory for the length of one request.

USER app

EXPOSE 8000

# Liveness only. Readiness is /health/pipeline, which probes the ML runtime and
# is deliberately not the healthcheck: a slow first import should not restart a
# container in a loop.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
