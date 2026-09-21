# What a green CI tick does not mean

At `cf00f98`, `CI ML` reports **658 passed, 47 skipped**. The same suite on a
machine with the data reports **704 passed, 1 skipped**, and the one skip there
is a Windows symlink privilege, not a missing dataset.

The 47 are not marginal. They are the tests that compare this pipeline's output
against trees that were cut down and weighed:

| file | what it checks against ground truth |
|---|---|
| `test_qsm_calibration.py` | DBH from the circle fit vs taped DBH, and the fit-quality gate's motivating failure |
| `test_single_tree.py` | the single-tree path vs tape measurements |
| `test_stem_tracking.py` | tracked stem volume vs harvested stem volume |
| `test_skeleton.py` | crown tracing vs harvested crown volume — the negative result that keeps the tracer out of production |
| `test_plot_pipeline_real_trees.py` | the whole chain on real scans placed in a synthetic plot |
| `test_carbon_uncertainty.py` | the density range vs measured per-tree density |
| `test_backend_promotion_gate.py` | whether PointNet++ measures better than tlsep |
| `test_published_evidence_is_current.py` | whether the accuracy figures in the proposal and on the dashboard are still what the pipeline produces — see [DEMOL_EVIDENCE_CHAIN.md](DEMOL_EVIDENCE_CHAIN.md) |
| `test_dbh_bias_by_species.py` (part) | the control for the bark finding: whether an independent QSM under-reads the same trees — see [DBH_BIAS_AND_BARK.md](DBH_BIAS_AND_BARK.md) |
| `test_cameroon_eval.py` (part) | the cohort loader against the real 1.29 GB archive: the 61-tree keying that excludes `ID_56`, min-Z normalization and the point cap, seeded-sample determinism, and that the five irregularly-formatted clouds parse and are flagged as repaired; the Chave-on-the-tape wiring smoke test and the Chave-vs-T-VER route B comparison, both costed from the real cohort's tape DBH and felled height — see [CAMEROON_EVIDENCE_CHAIN.md](CAMEROON_EVIDENCE_CHAIN.md) |
| `test_cameroon_evidence_is_current.py` (part) | whether the tropical figures on the dashboard and in the truth block still re-derive from the 61 trees — the Cameroon counterpart of the row above it, and the same limitation |

They skip because `services/ml/data/raw/zenodo_belgium/` and
`services/ml/woodleaf_pn2.pt` are not in git — point clouds for 65 trees and a
model checkpoint, far past what belongs in a repository. The skips are correct
behaviour, not a bug.

`test_cameroon_eval.py`'s archive-dependent tests skip for the same reason, one
cohort later: `services/ml/data/raw/dryad_cameroon/` is 1.29 GB and not in git
either. Their skip reason, exactly as `-rs` prints it, is `Cameroon archive not
present: see docs/ml/CAMEROON_EVIDENCE_CHAIN.md`. Most of that file's tests do
not need the archive at all — the irregular-format repair is exercised through
`tmp_path` fixtures that reproduce each shape byte-for-byte, so only the
end-to-end reads against the real clouds are what this skip actually costs.

What was wrong is that they were **invisible**. `pytest -v` prints `SKIPPED` per
line among nearly 700 lines and a count in the summary; nobody reads that as
"the accuracy evidence did not run". The CI step now passes `-rs`, which lists
every skip with its reason in the summary block, so the next person sees what
did not happen.

The counts above are worth re-reading rather than trusting. They were **35 and
683** when this file was written and were already stale by four before anyone
noticed, for the same reason the accuracy figures were: a number written into a
document once and never re-derived. They move whenever a test is added, so what
matters is the gap between the two columns, not either number.

## Some ground truth does now reach CI

`docs/evidence/demol_65/result.json` is committed, 18 KB, and carries the
per-tree predictions beside the per-tree taped measurements for all 65 trees.
Nine assertions in `test_dbh_bias_by_species.py` read it and run on CI —
the species structure of the DBH under-read, and the caveat reaching
`uncertainty_basis` on every route through `calculate_carbon`.

That is a narrow but real change to the sentence at the top of this file.
Conclusions drawn from felled trees can be pinned in a form CI can check; what
cannot cross the gap is anything that has to re-run the pipeline over the point
clouds. The three assertions in that file which need the cohort itself still
skip, and they are listed in the table above.

`docs/evidence/cameroon_61/result.json` is committed for the same reason, and
`scripts/sync_truth.py`'s `validate_cameroon` re-hashes it and compares every
one of the twenty-five figures the manifest publishes against it on each
`--check`. That runs on CI and cannot skip, so the manifest can no longer drift
from its own artefact. It says nothing about whether the artefact still matches
the trees — that is `test_cameroon_evidence_is_current.py`, and it skips here
for the usual reason.

Until both existed, the tropical block was the least guarded evidence in the
repository: `load_manifest` did not require it, nothing re-hashed it, and no
test held the two to each other, while the 65-tree temperate cohort had all
three. The newest and strongest evidence had the weakest gate.

## What this means in practice

- **CI protects the code, not the measurement.** Ruff, mypy, the unit and
  synthetic tests, the doc-truth check, the Docker build and its live
  `/upload/analyze` call all run on every push. Nothing that compares a number
  to a felled tree does.
- **Accuracy claims have to be re-run locally.** Anyone changing
  `qsm.py`, `allometric.py`, `skeleton.py`, `wood_leaf_separation.py` or
  `single_tree.py` should run the full suite where the cohort is present before
  trusting a green tick.
- **A silent skip for the wrong reason would look identical.** A typo in a path,
  a renamed fixture, a missing import inside a `skipif` — all present as a skip.
  `-rs` is what makes those distinguishable from the expected ones.

## Getting the data

`docs/ml/DATASETS.md` has the sources. The Demol cohort is the destructive
dataset behind every number in this document set:

> Demol et al., destructively harvested trees with taped DBH, felled height and
> harvested stem and total volume — `data/raw/zenodo_belgium/`

Fetch it before claiming any accuracy figure has been checked.
