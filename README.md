# Resolution Visibility Is Not Recovery

**Public reproducibility materials for Project 99llm** — original, source-locked secondary reanalysis. Public source and artifact repository: https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis. The working paper is not journal-submitted or peer reviewed.

> **Scientific status:** working research draft, no journal submission or acceptance, not peer reviewed. Authors, contributions, funding and conflict declarations require approval. The manuscript has **no DOI**. The repository is **not** a source of new raw developer-agent annotations.

## What this reanalysis actually supports

- The **pinned original source** has **16,118** admitted annotated episodes (not a random sample of all coding-agent failures), with **1,504 visibly resolved (RS1)** and **14,614 final outcomes not visible/unknown (RS2)**. RS2 must never be recoded as confirmed failure.
- Source-labeled DS1 visible resolution: **1,174 / 14,587 (8.05%)**; DS2: **330 / 1,361 (24.25%)**; difference **+16.20 percentage points**. These are author-assigned categorical-label associations.
- Among **853** sessions with both classes in **352** source-repository clusters, the equal-session mean visible-resolution difference is **+13.96 percentage points**. Repository-nested, deterministic resampling yields a **descriptive band +10.72 to +17.30 pp**; this is **not** a population or causal confidence interval.
- The eventual agent-after-pushback (RV2) contrast is only partially identified, with permissible DS2-minus-DS1 differences from **-77.61 to +90.10 pp** under unrestricted unknown outcomes. The **88.56%** equal-unknown-rate tipping threshold is a conditional scenario, not an estimate of unobserved outcomes.
- The observed positive **visibility** contrast can be erased in a restricted algebraic worst-case example by reclassifying **223 selected DS2/RS1 labels to DS1/RS1**. This is not evidence that those labels are wrong or a calibrated label-error probability.
- Original-author **arXiv v1** per-axis quality audit reports **0.64 severity-axis label accuracy** on a 100-episode test sample, while resolution-status accuracy is **0.96**. The authors' quality metrics are not an independent 99llm validation and supply no DS1/DS2-specific confusion matrix.

**Current repository-facing document: MR25 (8 November 2026), Appendix A integrated after Conclusion.** Prior MR24 separate 3-page supplement remains available in earlier Git history; the primary MR25 paper is a single PDF. Science, counts and claim boundaries are unchanged.

## Folder structure

| Path | Purpose |
|---|---|
| `scripts/reproduce_visibility_robustness.py` | Source hash, counts, repository/session matches, missing-outcome frontier |
| `scripts/reproduce_nested_robustness.py` | Repository-nested resampling, class-error certificate, exploratory checks |
| `scripts/reproduce_sensitivity_figure.py` | Figure regeneration; requires Matplotlib and NumPy |
| `results/aggregate_results.json` | Published **aggregate results only**; no episode-level rows or session IDs |
| `paper/author_review_preprint.pdf` | **MR25 integrated working preprint (22 pages)**: body + Appendix A + references, no assigned DOI |
| `paper/appendix_a.tex` | Integrated technical appendix, subsections A.1–A.5 and tables A1–A3; **no separate supplementary file** |
| `paper/preprint.tex`, `paper/article_body.tex`, `paper/references.tex`, `paper/figures` | Sources for the integrated neutral preprint with Appendix A |
| `tests/` and `.github/workflows/` | Standard-library smoke checks on synthetic fixtures (not source reproduction) |
| `REPRODUCE.md` | Author-source acquisition, hash pin, replay, and limitations |
| `PROVENANCE_AND_LIMITATIONS.md` | Dataset provenance and claim restrictions |

## Source attribution

**Original study**: N. Tang et al., *How Coding Agents Fail Their Users: A Large-Scale Analysis of Developer-Agent Misalignment in 20,574 Real-World Sessions*, EMNLP 2026, DOI [`10.18653/2026.emnlp-main.1011`](https://doi.org/10.18653/2026.emnlp-main.1011). Its [source code/data repository](https://github.com/ND-SaNDwichLAB/coding-agent-misalignment/tree/c887cc920129b2db0bdf218c8550e98f74f42f7c) supplies the original labels. **Never cite this derivative repository as if we collected the original episodes.**

**Original data source file:** [`data/core/annotated_misalignments.json` at commit `c887cc920129b2db0bdf218c8550e98f74f42f7c`](https://github.com/ND-SaNDwichLAB/coding-agent-misalignment/blob/c887cc920129b2db0bdf218c8550e98f74f42f7c/data/core/annotated_misalignments.json).

Frozen file SHA-256: `7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57`.

Archived source validation version: [`arXiv:2605.29442v1` (May 28, 2026)](https://arxiv.org/html/2605.29442v1), Appendix A.2 Table 5. The accepted EMNLP paper and the archived preprint are intentionally version-separated where metadata differ.

## Quick start

Read [`REPRODUCE.md`](REPRODUCE.md). Core scripts use Python **3.10+ standard library** only. The source's raw 16,118 annotation rows are **not** redistributed by this repository. The CI smoke tests exercise only fabricated records and algebra; **a passing GitHub CI badge would not mean the full paper was reproduced from third-party source**.

## Citation and license

Publication author order and final citation metadata are still awaiting author approval; this public GitHub URL identifies the working reanalysis but does not constitute a DOI or a peer-reviewed citation. A persistent repository release/DOI may be added after public verification. Code in `scripts/` and synthetic tests is provided under the MIT license (see `LICENSE-CODE`); the manuscript and third-party annotations are **not** covered by that software license. See [`CITATION_INSTRUCTIONS.md`](CITATION_INSTRUCTIONS.md).
