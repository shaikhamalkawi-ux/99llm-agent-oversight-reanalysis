# MR32P1 — Results of completed external endpoint-contract audit

**Status:** completed public-source, independent-cohort observational extension. This report is not part of the locked MR31R9-EP2 manuscript and does not establish new causal or final-repair truths.

**Execution:** GitHub Actions run 44971650335 (external-contract-audit job), completed with success; synthetic rule tests and full-data audit both passed. [Evidence and downloadable generated JSON](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/44971650335).

**External source:** gsmoon97/swe-agent-eval at immutable commit 2b8d930540ddaf0ae1290e718f1bd0741c70005e, one OpenHands/Claude 3.5 Sonnet SWE-bench Verified snapshot. Original trajectories and third-party results file are not redistributed.

## Cohort and integrity

The 500 explicit status IDs form three disjoint classes, each with a matching and readable JSON trajectory: 195 evaluator-resolved, 252 evaluator-unresolved, 53 in the source's no-patch/error ID group. Primary two-status denominator: 447. Exact source commit check passed.

Three inconsistencies exist **in the upstream source's own summary counters**: empty_error_patch_instances=8 but its ID list contains 53; submitted_instances=492 but its submitted_ids list contains 447; completed_instances=492 but completed_ids contains 447. We use the exhaustive disjoint status ID lists and never silently replace the conflicting metadata.

## Full-cohort deterministic result

| Observable in the independent OpenHands trace | Evaluator-resolved cases | Evaluator-unresolved cases | Evaluator-unresolved among observable-positive cases |
| --- | ---: | ---: | ---: |
| Last recorded model response present | 195/195 | 252/252 | 252/447 = 56.38% |
| Last response finish_reason = stop | 195/195 | 250/252 | 250/445 = 56.18% |
| Last response explicitly asserts tests passed (fixed regex) | 81/195 | 37/252 | **37/118 = 31.36%** |
| Last response explicitly asserts fix completion (fixed regex) | 59/195 | 35/252 | **35/94 = 37.23%** |
| Local passing-test receipt appears in tool output anywhere in trajectory | 77/195 | 46/252 | **46/123 = 37.40%** |

The complement matters: among the 118 cases where the last response claimed test success, 81 were benchmark-resolved (68.64%). Thus the model statement provides a **descriptive positive association** with evaluator success within the 447-case set, but does not certify that the task passed the benchmark. The result should not be misreported as if all positive statements were worthless or deceptive.

## Post-hoc joint signal table (same fixed rules)

Both signals must be separately recorded: a last-response affirmative test-pass claim and a tool log local-test-pass receipt. This is a cross-tabulation of the same frozen features, not a new fitted threshold.

| Last response claims tests passed? | Local test-pass receipt anywhere? | Evaluator resolved | Evaluator unresolved | Unresolved fraction |
| --- | --- | ---: | ---: | ---: |
| No | No | 94 | 187 | 187/281 = 66.55% |
| No | Yes | 20 | 28 | 28/48 = 58.33% |
| Yes | No | 24 | 19 | 19/43 = 44.19% |
| **Yes** | **Yes** | **57** | **18** | **18/75 = 24.00%** |

Even when **both** an affirmative final message and a passing local-test receipt are present, **18/75 = 24.00%** have an unresolved benchmark verdict in this single run. Thus combining the two recorded signals is descriptively more informative than either alone, but does not turn local process evidence into the benchmark's external task-status evidence. This joint table is an exploratory, after-the-fact descriptive cross-tab; do not claim confirmation on a new holdout.

## What this adds and what it does not

This separate-source case provides a task-evaluation outcome that was absent from the original Tang et al. conversation corpus; it makes the distinction between recorded model statements, partial local test outputs, and a third-party benchmark test result concrete. It is not verification of the original 16,118 cases and cannot be pooled with MR31 denominators.

The external source's verifier label is **not error-free ground truth**. An independent 2026 audit of SWE-bench Verified documented flawed tests, underspecified tasks and contamination risk (see OpenAI, 23 February 2026, https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/ and Epoch AI 3 September 2026, https://epoch.ai/benchmarks/swe-bench-verified/review). Therefore the reported disagreement is strictly with the benchmark verdict, not proof that the agent's patch was objectively wrong.

The program makes no attempt to validate whether a natural-language claim is sincere, scoped to the benchmark, or tied to the last edit; local test receipts may precede the final patch. False-positive/false-negative regex matches and selection into the 447 evaluable IDs are possible. The source is one model/scaffold and benchmark. No second model, causal intervention, post-hoc threshold-fitting or human/LLM adjudication was carried out.

## Relationship to nearby studies

- Wang et al., *From Faulty Claims to Incorrect Patches* (arXiv:2610.32338, October 2026) analyze task-grounded claims in model reasoning and their relation to patch defects. That is closer than general oversight surveys, but different from the restricted *last-response claim vs benchmark verdict* audit here.
- Cim et al., *Termination Lag* (arXiv:2611.14960, November 2026) test distinct patches at many agent steps and show that reaching correctness and stopping differ. It provides deeper step-level patch verification than our report.
- Qi et al., *Merged, Not Measured* (arXiv:2609.37985, September 2026) rerun performance-claim tests for merged/rejected agent pull requests; it provides another claim-versus-measurement example but at different tasks and endpoints.

**Novelty assessment:** the new empirical check improves MR31's evidence breadth, but the general observation that statements/merges can disagree with executed tests is already known. The defensible value is in a frozen, full-cohort, three-endpoint accounting linked to the narrower inference-control thesis—not in claiming discovery of a new failure mode.

## Publication decision

Candidate for a short robustness subsection or illustrative external validation of the *reporting distinction*, **not** a second primary result or a general theory proof. Keep MR31 science unchanged until full author/reviewer interpretation and native source integration are available.
