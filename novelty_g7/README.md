# G7 — Recorded local test evidence is not a final-patch certificate

**Research candidate, 24 November 2026.** MR31R9-EP2 and G6 are unchanged. External benchmark cohort; do not pool with Tang et al.'s historical episode corpus.

## Provenance and execution
Cim, Topcu & Kandemir, *Termination Lag: Coding Agents Solve Early but Stop Late*, arXiv:2611.14960. Public dataset [termination-lag-trajectories](https://huggingface.co/datasets/musacim/termination-lag-trajectories), immutable revision 15b2cea1f2bbf8c9945dea1f6311613ccb0b9ebe. All 12 Parquet file SHA-256 hashes and aggregates are in [G7_verified_summary.json](G7_verified_summary.json). [Corrected source replay](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45468524785), computation commit 79e075a3399cce1d8db1f864bb1a8700b1cb9e57. The final parser includes numeric XML return codes; this correction changes no primary counts and enables explicit exit-zero sensitivity. Synthetic tests, complete source join and final/first-correct grade consistency checks pass. No original records, code, commands or quotations redistributed.

## Method
Narrow pytest/unittest commands and numeric summaries from single tool call/observation; reject compound commands (one simple cd permitted), failures and parsed nonzero exits for positive markers. A qualifying receipt is linked to identical nonempty recorded patch IDs at the adjacent pre/post-step snapshots. A sensitivity requires three consecutive identical IDs. Exact match to the submitted patch ID is a stronger filter than merely having a receipt after a recognized edit. No claim that the entire execution environment is identical; the source's offline grades are not re-executed. No causal inference or independent human annotation.

## Results
All six settings: 2,400 runs, 2,275 aligned complete traces; 290 runs have a stable-patch local positive marker. Of 142 with a positive marker linked to the submitted patch, 87 do not pass the benchmark (61.27%). Three-snapshot sensitivity: 70/113 (61.95%). Mini-SWE-agent explicit exit-zero sensitivity: 9/13. Narrow positive marker without recorded skip/deselect/expected-failure qualifiers: 77/131. No eligible positive markers in the two multilingual settings under this Python-specific screen. Counts are descriptive run units; tasks can repeat across settings.

|Setting|Final-ID positive runs|Benchmark nonpass|
|---|---:|---:|
|Qwen3-Coder Verified OpenHands|29|17|
|Laguna Verified OpenHands|71|37|
|Seed-OSS Pro300|29|24|
|Qwen3-Coder Verified mini-SWE-agent|13|9|

## Exploratory multiplicity / within-patch challenge
Repeated positive markers on final patch: 48/84 nonpass. At least two distinct tokenized positive commands: 46/80; three: 20/37; two distinct positive commands and no skip/deselect/expected-failure qualifiers: 39/62. Different commands need not exercise different or independent tests. 77 setting-task-patch units (70 runs) have both positive and negative local markers on the identical recorded patch; 52 of 77 are benchmark nonpassing. Three-snapshot filter: 44/67. Of 19 final-patch runs with both positive and negative markers, 14 are benchmark nonpassing. Two of 77 patch units have both outcomes for the same literal tokenized command; neither proof of flakiness nor environment equivalence. These are post-primary descriptive challenges, not prespecified confirmation.

Retrospective first-positive linked patch selection: 109/290 benchmark passes versus 116/290 final passes; 8 losses and 1 rescue relative to final. Do not claim improved stopping or measured token savings.

## Originality and inclusion
Yang et al., *Done, But Still Working: Anytime Evaluation of When Coding Agents Should Stop* (arXiv:2611.22901, 17 Nov 2026) already study self-test versus hidden-test grades, exact-patch repeated-pass rules and retrospective stopping. Cim et al. already study earlier correct patches and later regressions. Khan & Kumar, Soei (arXiv:2610.39468) already distinguish verification and completion. Do not claim novelty for these general ideas. G7's narrower external evidence is the explicit final-patch-ID-conditioned nonpass counts and same-patch coexistence of opposite local markers, linking the main paper's claim-specific evidence distinction to an independent recorded benchmark cohort. An empirical replication/extension, not a new theorem, verified repair in Tang et al., or validated general-purpose certificate. Benchmark nonpass can include test timeout and other source evaluation failure; not objective patch incorrectness. No prevalence claim outside the screened cohort. No test suites re-run, semantic scope adjudication, or new deployment evaluation.

**Recommendation:** consider a compact external-validation paragraph and supplemental table; leave the locked manuscript untouched until review.
