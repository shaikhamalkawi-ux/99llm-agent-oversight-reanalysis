# 99llm — MR31 research extension (public derived artifacts)

**Companion to:** *Resolution Visibility Is Not Recovery: Evidence Limits in Coding-Agent Evaluation After Developer Pushback*.

**Snapshot:** MR31R9 / EP2, 22 November 2026. This is an **author-review working manuscript, not a submitted, accepted or journal-published paper**. It is an editorial GitHub-sync release; no new results, estimands, label assignments or source records were created by this release. The MR26 files in the repository root and `paper/author_review_preprint.pdf` are retained as historical material.

Read the current working copy: [`paper/99llm_MR31R9_EP2_GitHubSynced_AUTHOR_REVIEW.pdf`](../paper/99llm_MR31R9_EP2_GitHubSynced_AUTHOR_REVIEW.pdf). Figures are vector PDFs and SVGs under [`mr31/figures/`](figures/).

## Evidence objects and preserved results

| Question | Current derived result | Interpretation |
| --- | --- | --- |
| Source material | 16,118 annotated episodes; 15,948 with source DS1 or DS2 labels | Original authors' records, not collected or reannotated here. |
| Recorded source-label visibility | DS1 1,174 / 14,587; DS2 330 / 1,361; pooled difference +16.20 percentage points | RS1 is a recorded source-labelled visible resolution; it does not certify a verified final code state. |
| Matched original sessions | 853 of 8,590 eligible DS1/DS2 sessions; 2,775/15,948 episodes | Restricted observational subpopulation; not a representative agent outcome rate. |
| Equal-session RS1 difference | +13.9612 percentage points; repository-nested descriptive percentile band +10.7171 to +17.2998 pp | Source-labelled association, not a causal correction effect. |
| Matched-session sign/ties | 201 positive, 99 negative, 553 ties; 528/553 ties have zero visible resolutions in both groups | A tie in visibility does not imply equivalent eventual recovery. |
| Source-label sensitivity | Exact 121-point budget frontier: at 119 switches +0.01047 pp, at 120 switches −0.10677 pp | A targeted algebraic sensitivity witness; not a measured rate of label error. |
| Eventual RV2 recovery | Broad pooled and matched-session logical intervals cross zero | Outcome sign is not identified without additional assumptions about unknown cases. |

The reported ratios, plotted endpoints and code inputs are copied from the locked MR31R6-derived artifacts and carried through the MR31R9 editorial version without scientific recalculation. Original RS1 and hypothetical eventual RV2 are different endpoints.

## Files

- `data/aggregate_results.json`, `data/matched_coverage_results.json`: byte-identical copies of the existing public root `results/` files, included here so the rendering scripts operate from a self-contained directory.
- `data/matched_RV2_eligibility.json`: fixed 853-session admission frame and logical recovery bounds.
- `data/exact_label_sensitivity.json`: archived exact sensitivity budget frontier 0–120 plus anonymous count-pattern certificate. No original episode rows or session identifiers.
- `data/new_result_values.json`, `data/revised_figure_values.json`: fixed numeric-to-figure trace and figure verification records.
- `code/build_new_results.py`: render N1/N2/N3 from the frozen derived aggregates.
- `code/build_revised_figures.py`: render F1/F2/S1 from the frozen derived aggregates and exact frontier.
- `figures/`: six approved figure pairs, vector PDF and SVG.
- `tests/test_published_results.py`: offline structural, provenance and arithmetic-consistency tests against published derived inputs.
- `SHA256SUMS.txt`: SHA-256 digest of the frozen input/data/code/figure/working-PDF files in this release.

## Run the available offline checks

From the repository root:

```bash
python -m unittest discover -s mr31/tests -p 'test_*.py' -v
python -m pip install -r mr31/code/requirements.txt
python mr31/code/build_new_results.py
python mr31/code/build_revised_figures.py
```

Outputs are written to `mr31/proposed/`, `mr31/previews/`, and `mr31/qa/` in a local checkout. The offline tests and figure-generation scripts were run on the release inputs before publishing. The committed figures are **not** claimed to be bit-identical across plotting-library or PDF metadata versions. A passing synthetic/offline CI check is **not** a complete raw-source recomputation or experimental agent verification.

**Raw-source replay boundary.** Re-deriving all MR31 aggregates from the third-party episode records requires independently retrieving the original authors' source file and verifying its pinned SHA-256, and the original derivation machinery for the new exact frontier. This public snapshot supplies the **derived frozen outputs and scripts to regenerate the six graphics**; it does not claim that the full original raw-to-MR31 calculation is executable from this directory alone. The underlying source-labeled annotations are not redistributed.

Original dataset: [Tang et al. 2026 source repository](https://github.com/ND-SaNDwichLAB/coding-agent-misalignment/tree/c887cc920129b2db0bdf218c8550e98f74f42f7c). Required original `annotated_misalignments.json` SHA-256: `7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57`.

**Citation and licensing:** Cite Tang et al. for the source data and authors' annotations, and cite the working manuscript/repository only for the derivative analysis and public materials. No paper or software DOI has been assigned. The repository's `LICENSE-CODE` applies to code contributed by this project, not to the original dataset, the figures, or the working paper. Author metadata, final journal declarations and native LaTeX production remain pending; no journal submission status is implied.
