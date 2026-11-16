# 99llm-X1 — P9 Experimental Bootstrap (PUBLIC STAGING)

**Status: synthetic CI smoke tests only. NOT a coding-agent evaluation and NOT an independent task-oracle run.**

This directory reproduces the original P9 acquisition protocol, as separately locked on 2026-11-16. It is placed on an isolated non-default branch in the existing 99llm reanalysis repository for safe staging only. **The repository's existing main branch, MR26 materials, and the separate locked MR30 manuscript are not modified.**

## Scope

- `scripts/p9_decide.py`: an oracle-blind, timestamp-restricted acceptance decision gate.
- `scripts/p9_reveal.py`: post-seal reporting, subject to strict oracle-admission guards.
- `tests/test_p9.py`: 21 stdlib synthetic and deliberately corrupted-input tests.
- `examples/SYNTHETIC_*`: fabricated fixtures, not observed agent-repair outcomes.
- `P9_EVIDENCE_ACQUISITION_PLAN_EN.md`: the full prespecified acquisition design and scientific limitations.

Run locally from the repository root:

```sh
python3 -m unittest discover -s x1_experiments/tests -v
python3 x1_experiments/scripts/p9_decide.py --input x1_experiments/examples/SYNTHETIC_decision_only.jsonl --out /tmp/x1-p9-seal
python3 x1_experiments/scripts/p9_reveal.py --sealed-dir /tmp/x1-p9-seal --oracle x1_experiments/examples/SYNTHETIC_oracle_AFTER_SEAL.jsonl --out /tmp/x1-p9-synthetic-score.json
```

The GitHub Actions smoke workflow has `push` scoped to `x1-p9-public-bootstrap-20261116`, so a push to the default branch is not required. It exercises **only** the Python protocol and synthetic fixtures on a hosted runner; it does NOT run Docker, download a benchmark, interact with coding agents or execute hidden oracle tests. The existing repository's own workflow may also run on pushes, independently of this X1 workflow.

## What is needed for the real experiment

1. Create a **separate public** repository named `99llm-x1-experiments` (repository creation is not supported by the connected GitHub writing tools). Copy this directory's contents to that new repository's root and the X1 smoke workflow under `.github/workflows/`.
2. Make a **new, disjoint** source/task frame, freeze code and Docker image digests, and prespecify correction scripts and independent test manifests. Do not reuse P8's two known positive cases as an untouched evaluation set.
3. Record and publish the decision seal **before** running hidden task-oracle tests. Keep oracle data out of all pre-decision inputs.
4. Run official benchmark oracles in an isolated Docker-capable runner. Record test logs, manifests, image digests, exact SHA and execution counts. `P9` alone does not install or launch the benchmark.
5. Evaluate with `p9_reveal.py` only after the oracle job has actually completed. Keep missing or compromised endpoints as UNKNOWN/HOLD and preserve the entire frozen denominator.

No author metadata, journal DOI, independent coder, experiment effectiveness or full-task success is inferred. This is a reproducibility scaffold, not a publishable empirical finding.
