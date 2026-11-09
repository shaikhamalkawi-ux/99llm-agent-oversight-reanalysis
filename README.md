# Resolution Visibility Is Not Recovery

**Project 99llm — MR26 source-locked secondary reanalysis** (9 November 2026).  
This is a **public working manuscript and reproducibility repository**, not a submitted, peer-reviewed or accepted article. There is **no assigned manuscript or software DOI**. Author order, affiliations, contributions and disclosures remain under human-author review.

## Scientific identity and core results

The [original study by Tang et al. (EMNLP 2026)](https://aclanthology.org/2026.emnlp-main.1011/) collected and annotated developer-visible coding-agent misalignment episodes. It explicitly reported **90.67% unknown final outcomes** and **91.49% agent-after-pushback resolution only among the visibly resolved subset**. We did **not** discover that missingness, collect agent transcripts, or redo the source authors' annotations. Our added work is restricted to derived label contrasts, matched-cluster analyses, partial-identification bounds and robustness checks.

| Distinct empirical object | Source-locked result and interpretation |
| --- | --- |
| Observed corpus | 16,118 source-annotated episodes; 1,504 recorded visible resolutions and 14,614 unknown final outcomes. Unknown is **not** known failure. |
| Recorded visibility by source severity | DS2 330/1,361 versus DS1 1,174/14,587 (**+16.20 pp**). This is an association of original labels, not a causal effect. |
| Within-session contrast | 853 matched sessions from 352 source-qualified repositories; equal-session mean **+13.96 pp**, repository-nested descriptive resampling band **+10.72 to +17.30 pp**. |
| Match coverage (new MR26 audit) | 853 of 8,590 eligible two-class sessions (**9.93%**) and 2,775 of 15,948 eligible episodes (**17.40%**). The matched subsample cannot be assumed representative. |
| Ties (new MR26 audit) | In 553 session-level ties, 528 had **zero visible resolutions in both severity classes**, 22 had both rates equal to one, and three had equal intermediate rates. |
| Eventual recovery | DS2-minus-DS1 eventual post-pushback fraction logically ranges from **−77.61 to +90.10 pp** with unrestricted unknown outcomes. Sign not identified. |
| Label fragility | Exactly 223 targeted severity-label flips reverse the pooled recorded-visibility ordering in a worst-case algebraic witness: **1.40% of all two-class labels, but 67.6% of visibly resolved DS2 episodes**. These are not observed errors or a plausible randomized error-rate estimate. |

The original DS2 severity code and RS1 visible-resolution code are both inferred from the **same developer-agent trace**; source selection already requires developer pushback. The analysis cannot separate a true severity effect from shared ascertainment or episode-level selection. The original authors' arXiv v1 100-record annotation check reports severity-axis model accuracy of 0.64 and resolution-axis accuracy of 0.96; these do **not** yield a DS1/DS2 confusion matrix or an independent verification by us.

## Files and reproducibility

- `paper/author_review_preprint.pdf` — current neutral **MR26 working preprint with Appendix A and Appendix B integrated**; no journal DOI or MDPI publisher template.
- `paper/preprint.tex`, `paper/article_body.tex`, `paper/appendix_a.tex`, `paper/appendix_b.tex`, `paper/references.tex` and `paper/figures/` — current reader-source document; Appendix A is the technical audit, Appendix B preserves lower-priority cross-paper arithmetic and version checks.
- `scripts/reproduce_visibility_robustness.py` and `scripts/reproduce_nested_robustness.py` — source-locked complete primary results, plus label-flip certificate and repository-nested resampling.
- `scripts/reproduce_matched_coverage.py` — **MR26 additive coverage/tie-composition audit**.
- `results/aggregate_results.json` — byte-identical frozen original-derived aggregate output; `results/matched_coverage_results.json` — additive MR26 aggregates. **Neither contains original episode rows or identifiers.**
- `tests/` and `.github/workflows/` — smoke tests on synthetic fixtures and committed aggregate counts. A CI success does **not** mean a full replay was run against third-party source rows.
- [`REPRODUCE.md`](REPRODUCE.md) — exact original-author source, pinned SHA-256 and replay commands.
- [`PROVENANCE_AND_LIMITATIONS.md`](PROVENANCE_AND_LIMITATIONS.md) — source and inferential boundary.

Original source (obtain independently): [`annotated_misalignments.json`, pinned at upstream commit `c887cc920129b2db0bdf218c8550e98f74f42f7c`](https://github.com/ND-SaNDwichLAB/coding-agent-misalignment/blob/c887cc920129b2db0bdf218c8550e98f74f42f7c/data/core/annotated_misalignments.json). Original file SHA-256: `7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57`.

Cite the **original Tang et al. paper** for the data/annotations and this repository only for **our derivative analyses and software**. The MIT license applies only to our original scripts and synthetic tests; manuscript and original third-party dataset are **not** relicensed. A formal article citation, repository release tag and archival DOI require author-side verification; no identifiers or approvals are invented here.
