# G6 — Validation-scope signals and a targeted ascertainment frontier

**Research candidate, 24 November 2026.** MR31R9-EP2 and G5 remain unchanged. G6 is an aggregate-only secondary analysis, not an independent repair adjudication or a submission.

## Source and reproducibility

[Verified source-byte CI run 45466464302](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45466464302), computation commit `b13a793b84fd8514f58ae738441bac480a113a52`. Three original author files are pinned to upstream commit `c887cc920129b2db0bdf218c8550e98f74f42f7c`. Source SHA-1 Git blob and byte counts are enforced, and the annotation SHA-256 is checked; hashes are included in the CI artifact. All 16,118 annotated records join one-to-one to the VALID stage of 29,896 validation records; all 15 shared fields agree per record. All 7,760 excerpt records match their annotation records. [Verified aggregate summary](G6_verified_summary.json) is extracted from successful CI logs. The uploaded CI artifact includes full aggregate JSON and source hashes; no raw records or quotes.

Reproduce with `audit_validation_scope.py` and `compare_targeting.py`, each with `--selftest`, then `--annotations`, `--excerpts`, `--validation`, and `--out` arguments using the upstream files; see [workflow](../.github/workflows/novelty-g6-validation-scope.yml).

## Result 1: claim-scope heterogeneity across stages

The original Tang et al. study already reports the extraction/validation counts and rejection categories (Table 4); these are not our novelty. Before running G6, the strict audit signal was defined as at least one same-session source rejection for `invisible_agent_action` or `session_terminated_before_completion`. It does not mean the accepted episodes in that session are invalid. Of 13,778 rejected claims, 6,694 bear these reasons (4,910 and 1,784). In the fixed 853-session, 2,775-episode frame, 183 sessions contain the strict signal; 60 contain an accepted episode with original RS1, 181 contain RS2, and 58 contain both. The 517 unknowns in these 183 sessions carry 792,687 of 3,544,605 width units (22.36%). Broader evidence rejection categories select 247 sessions and 29.96% of width. No rejected claim is recoded or admitted to the matched cohort.

An independent structural check of source labels (not their truth) finds 6 of the 79 matched sessions with two or more RS1 episodes contain both RV2 and another resolver type (7 discordant pairs among 120 within-session RS1 pairs). Nine unknown episodes coexist with both resolver types. Across the 1,547 within-session pairs in excerpt-released matched sessions, 65 share at least one identical nonempty literal quote; 20 of those have different RS1/RS2 labels. There are zero identical complete literal quote sets; seven pairs share an identical latest literal quote and none of these seven disagree on status. Therefore there is no demonstrated identical-complete-packet contradiction. Episode identity and claim scope matter; no label is transported.

## Result 2: an observed release plus a rejection-targeted hypothetical frontier

The original G5 release covers 936 unknowns, 1,474,407 width units. Among 479 matched sessions without excerpts, the strict signal selects 97 sessions (all SpecStory) with 271 unknowns and 437,472 width units. The disjoint union has 1,207 unknowns, 471 sessions, 1,911,879 units (53.9377% of the total). Under perfect ascertainment of the union, residual width is 75.9563 pp, versus 96.3080 pp with perfect ascertainment restricted to published IDs. Greatest achievable lower endpoint is +11.2269 pp; smallest achievable upper endpoint is -1.7596 pp. These correspond to DIFFERENT favorable assignments. Neither direction is guaranteed or newly observed. Conditional on perfect G5 ascertainment, the additional strict threshold for positive sign is >196,143, for half width >=297,895.5, and for negative sign >399,648 units.

| Objective | Strict restricted minimum sessions | All absent sessions unrestricted minimum | Strict minimum episodes | Unrestricted minimum episodes | Any whole strict sessions that may remain unknown while retaining capacity |
|---|---:|---:|---:|---:|---:|
| Positive possible | 39 | 39 | 78 | 78 | 47 |
| Half width | 60 | 60 | 129 | 119 | 27 |
| Negative possible | 82 | 80 | 218 | 159 | 7 |

All are unit-count optimizations under hypothetical perfect ascertainment, not audit-cost or success estimates. With 97 sessions fixed, the selected signal yields 437,472 units, compared with exact uniform-random expectation 200,809,206/479 = 419,225.90 units and unrestricted top-97 maximum 488,880. Thus it is only 1.0435x the random expectation and 89.48% of the optimum. This comparison is not a randomization test or evidence of superior actual retrieval. Loss tolerance is a worst-case capacity statement (sort losses descending), not a guarantee of scientific direction.

## Originality assessment and boundary

The empirical cross-stage linkage and conditional frontier are the candidate contribution, not the already known validation counts, generic partial-identification algebra, greedy sorting, or distinction between completion claims and proof. Tang et al. (EMNLP 2026, DOI 10.18653/2026.emnlp-main.1011) already discuss blind spots; Baumann et al. (COLM 2026, arXiv:2604.20779) provide session-level assessment; Khan & Kumar (arXiv:2610.39468, preprint) already study verification versus claims of completion. A new mathematical theorem, causal effect, validated predictive classifier, actual rights/access, or verified task recovery is not claimed. SWE-chat full trace access is gated as documented by its original repository. Missing excerpt sessions in this frame are all SpecStory; cannot separate source and release effects. No raw records, identifiers or quotes were exported. Preserve MR31R9-EP2 until a compact G5/G6 insertion passes the manuscript review and production gates.

**Recommended article claim:** Original validation-stage reasons can be used to delineate an additional, disjoint candidate audit frame that crosses the conditional half-width and sign-possibility thresholds, but do not themselves establish outcome truth or audit efficiency. This joins an actual source-release boundary to a claim-specific ascertainment capacity analysis.
