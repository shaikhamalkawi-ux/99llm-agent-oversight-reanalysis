# G5 — Observed excerpt release and within-session evidence linkage

**Research candidate, 24 November 2026.** The authoritative MR31R9-EP2 manuscript remains unchanged. No new original outcome labels, independently verified repairs, or submission are claimed.

## New empirical result
Three original-author files are pinned to commit c887cc920129b2db0bdf218c8550e98f74f42f7c. All 7,760 published excerpt records join uniquely to the 16,118 annotated episodes and match every shared annotation field. All annotation/session mapping checks pass. In the fixed 853-session matched cohort (2,775 episodes, 2,352 RS2 unknown outcomes), 936 unknowns have excerpt records, covering 1,474,407 of 3,544,605 exact width units (41.595805%). Even hypothetical perfect ascertainment confined to these observed IDs leaves 96.307989 percentage points of width; the greatest possible lower endpoint is -9.124798 pp and the smallest possible upper endpoint is +18.592084 pp. This is a conditional ceiling, not observed ascertainment, a legal-access determination, or a claim about all alternative public sources.

## Nested same-session structural screens
Of the 936 unknowns with excerpts:
* 644 have a later quote in another published episode in the same source-qualified session.
* 144 have a later sibling sharing a turn index.
* 55 have a later sibling sharing an exact nonempty same-turn quote (same count with strict literal role and quote equality).
* 18 have a later exact-linked sibling carrying the original RS1 label.

Each stricter screen requires the same sibling to meet all conditions. These are possible context links, not verified same-focal repair or a necessary condition for semantic relevance. An exploratory AI-assisted review of all 18 identified examples of later answers to focal questions and narrower reversals that do not establish delivery of the original task; it did not reannotate or independently verify outcomes.

## Verification
[Source-byte verified CI run 45342644864](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45342644864) completed successfully. The artifact contains only the executable and aggregate JSON. No original records, identities or quoted material are included. Reproduce using `verify_release_context.py --selftest` and then the three original source files with `--annotations`, `--excerpts`, `--mapping`, `--out`.

The source-specific computation is more empirically grounded than the G3 metadata-only proxy. It is not a new general partial-identification theorem. Tang et al. (EMNLP 2026), Manski (2005), Baltes et al. (online Nov. 2026) and Khan & Kumar (Soei, 2026 preprint) already establish related annotation-scope, missing-data, trace-reporting and provenance concepts. Prefer a single compact G5-centered manuscript insertion over adding G2–G5 as separate sections. Production parity and author approval remain distinct.
