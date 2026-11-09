# Reproduce MR26 source-locked results

Scientific scope: **released categorical labels**, not unseen outcomes, independent reannotation, causal intervention benefit, or fieldwide failure probability. The original authors reported the unknown-outcome problem; our replication adds original-label matched analyses and mathematical sensitivity checks.

## Step 1 — independently obtain the source

Download `annotated_misalignments.json` from the [exact pinned original-author source](https://github.com/ND-SaNDwichLAB/coding-agent-misalignment/blob/c887cc920129b2db0bdf218c8550e98f74f42f7c/data/core/annotated_misalignments.json). Do **not** commit it into this derivative repository.

Its exact SHA-256 must be `7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57`. Python 3.10+ standard library is sufficient for the numerical workflow.

## Step 2 — from this public GitHub repository root

```bash
python scripts/reproduce_visibility_robustness.py \
  --annotations /path/to/annotated_misalignments.json \
  --output visibility_check.json
python scripts/reproduce_nested_robustness.py \
  --annotations /path/to/annotated_misalignments.json \
  --output nested_check.json
python scripts/verify_replay.py nested_check.json results/aggregate_results.json
python scripts/reproduce_matched_coverage.py \
  --annotations /path/to/annotated_misalignments.json \
  --output matched_coverage_check.json
```

The primary deterministic aggregate JSON must have SHA-256 `2020eafd809b3a6888fefa35c48ad036322f3c4faaab0056303168791b60f7e1` and match `results/aggregate_results.json` byte for byte. The additive coverage check should match `results/matched_coverage_results.json` byte for byte. Both computations verify the original source checksum and never emit episode rows.

The original-label nested interval is descriptive for the *selected finite corpus*, not a population confidence interval. Session matching does not remove within-session measurement/selection bias; the severity-reclassification witness is deliberately adversarial, not a measured error rate.

Run the synthetic-only checks independently:

```bash
python -m unittest discover -s tests -v
```

A passing CI smoke test does **not** constitute a full source-data replay. `scripts/reproduce_sensitivity_figure.py` optionally requires `matplotlib` and `numpy`; its frontier is an algebraic figure, not a fitted curve.

## Step 3 — compile the public integrated paper

```bash
cd paper
pdflatex -interaction=nonstopmode -halt-on-error preprint.tex
pdflatex -interaction=nonstopmode -halt-on-error preprint.tex
```

The preprint imports `appendix_a.tex` (source integrity/technical audit), then `appendix_b.tex` (supplemental cross-study documentary checks). It does **not** require a separate Supplementary PDF. The journal-facing author-review version with MDPI class is provided in a separate author package, not relicensed or deposited here.

**Not reproducible from this repository alone:** original annotation-model decisions, raw agent conversations, hidden eventual outcomes, original source authors' adjudication sample, other cited studies' full experiments, journal peer review, and real human oversight benefit.
