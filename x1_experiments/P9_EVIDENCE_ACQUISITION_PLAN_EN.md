# 99llm-X1 — P9 independent endpoint acquisition and blinded decision protocol

**Status:** executable design and source-route feasibility, NOT a completed intervention study. **MR30 stays frozen.** Do not claim a policy effect, population rate, or independent re-execution before oracle jobs actually execute.

## Why P8 alone cannot settle X1

P8 screened 21 Copilot-authored PRs returned by a conditioned search. Two of these contain narrowly certified *same-check-name* CI failure-to-pass episodes: Morrison-Lab/ettbc#8 and burncloud/burncloud#20. These are useful implementation examples, not an untouched test set. P8's third illustrative case (care_fe#13755) illustrates author ambiguity. No P8 case comes with a uniform independent oracle across all 21; no X1 decision was sealed before learning later CI outcomes. Thus P8 is development/diagnosis, not a valid P9 experimental denominator.

## Concrete public data routes (verified 2026-11-16)

**Route 1 — naturalistic GitHub chronology (no new agent needed).** Starting from a **new pre-specified PR frame outside P8**, retrieve human review comments, bot-authored commits, parent-SHAs and GitHub check-runs/check-suites/CI job results using read-only GitHub APIs. Positive attribution requires correction after a demonstrable failure and bot child edit; other contributors must be captured. Lock a decision *as of* a dated commit before obtaining check-runs that finished after the decision. Do not call a merged PR or a zero-test green status a resolved issue. This is a time-restricted observational replay only. CI is admissible as a narrow oracle when the job tests are independently controlled and fixed before decision; otherwise mark partial-verification, not task truth. Avoid conditioning a general population estimand on 'review:changes_requested is:closed'.

**Route 2 — controlled, executable task oracle (preferred for a comparative paper).** Use **SWE-bench-Live** with frozen public task IDs, Docker image hashes and an executable grader, or SWE-bench Verified for infrastructure rehearsal only. The problem statement and repo state are visible to the agent, but `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`, reference patch and raw oracle results MUST be isolated. Generate an initial agent patch; after prespecified *local* failure evidence, deliver one scripted corrective message (clearly label it synthetic developer feedback). The agent then submits a second patch. Save the acceptance decision **after the second patch, before hidden oracle tests**. Execute the hidden test suite in a separate sandbox with immutable manifest. Label from fail-to-pass plus pass-to-pass and zero-test/error exclusions. With the same information budget for all policies, measure false accept and unnecessary hold. The original agentic rollout is not observational evidence of natural human pushback.

**Route 3 — SWE-Together for interaction realism.** Its 109 original sessions provide a feedback-oriented task frame and containerized verifiers. The benchmark's published *agentic judge* and any bridged per-gate results are not interchangeable with raw independent deterministic test execution. Only tasks with pinned, executable, independently verifiable test manifests pass the endpoint gate. Retrain/retest neither on P8 holdouts nor on visible oracle files.

Sources:
- https://github.com/Togetherbench/SWE-Together ; https://huggingface.co/datasets/yfwu/SWE-Together
- https://github.com/microsoft/SWE-bench-Live ; https://huggingface.co/datasets/SWE-bench-Live/SWE-bench-Live
- https://github.com/SWE-bench/SWE-bench ; https://www.swebench.com/SWE-bench/guides/evaluation/
- https://docs.github.com/en/rest/checks/runs

## Freeze-before-reveal operating procedure

1. Register **a new whole frame**, eligibility and exclusions before seeing outcomes. Suggested staged feasibility: 10 tasks; scale to 30–60 or more by a *new* preregistered protocol, not by selectively appending wins. Report sample-size feasibility; do not represent 30–60 as a power guarantee.
2. Freeze task sources, SHA, Docker image digest, test manifest, correction script, information budget, final patch and time of decision `t_decision`. The X1 policy is locked in `scripts/p9_decide.py`. No gate policy may open future oracle files or future timestamps.
3. Run `p9_decide.py` **in a working directory with decision-only records, with no oracle available**. Archive its seal file (`input_sha256`, `script_sha256`, `decisions_sha256`) with timestamp before running hidden tests. Seal decisions on an append-only/public timestamped repository if a strong prospective claim is required: locally computed hashes do not by themselves prove when the seal was made.
4. Run a genuinely independent oracle on exact `head_sha` after the decision, with tests not used in gate and not modified by the agent. Collect full execution output, tests executed, F2P and P2P counts, runner version, manifest SHA, and an immutable source locator. Keep zero tests, errors, absent tests, changed verifiers, unmatched SHA, and missing cases as **unknown/not admitted**, not failures.
5. Run `p9_reveal.py` to check chronology, SHAs, manifest and isolation flags before scoring. Report acceptance, risk among accepted, and unnecessary holds among truly passing tasks; cluster uncertainty by original repo/task if adequate support. Release row-level ledger and scripts, retaining privacy/license restrictions.

## Comparator fairness (three pre-specified policies, same visible record)

- `self_report`: ACCEPT when patch applies and agent claimed completion; otherwise HOLD.
- `local_pass`: ACCEPT when patch applies and any nonempty local test receipt claims success; otherwise HOLD. This deliberately ignores exact-SHA and task coverage as a weak comparator.
- `source_linked` (X1 candidate): ACCEPT only with patch applied, predecision successful local test receipt for *exact patch SHA*, positive test count, prespecified task scope, actor matched, and no intervening unrelated edit; otherwise HOLD. All three use precisely the same record. This is a diagnostic *candidate*, not necessarily a new algorithm or independently superior policy.

Gate features must not include oracle metrics, hidden test patches, `resolved`, future statuses, or postdecision corrections. An automatic predecision hold is not a proven 'false refusal' unless the later independent oracle on that same patch passes.

## Valid independent oracle

For each episode store `episode_id`, exact `head_sha`, `oracle_type`, `oracle_code_sha256`, `source_url`, `started_at`, pre-registered flags `oracle_test_manifest_frozen_before_decision`, `oracle_independent_of_visible_receipts`, `oracle_unmodified_by_agent`, `tests_executed`, `f2p_total`, `f2p_passed`, `p2p_failed`, `status`. The reporter refuses outcome admission if any key guard fails. A merely successful CI check is **not** enough to attest that the complete repository issue was resolved or that the test suite was independent.

## Endpoints and limitations

- **False accept among evaluated accepted:** count(ACCEPT and oracle=FAIL) / count(ACCEPT and independent oracle admitted).
- **Unnecessary hold among evaluated true passes:** count(HOLD and oracle=PASS) / count(oracle=PASS admitted). Report two denominators, non-admission, source and coverage separately.
- Design-based comparisons can be paired because all three gates read the same task evidence; a causal intervention effect on real deployed agents requires randomized gate assignment and a subsequent behavioral outcome, not simply retrospective classification.
- Any CI oracle sharing the gate's local tests is rejected. A green '0 tests' job is rejected. An oracle test script changed by the agent or manifest unknown is rejected. Co-author trailers or a human edit do not prove solely autonomous code ownership.

## Runtime blocker and alternative

This ChatGPT session can read public GitHub records and make the source lock, but its local runtime currently has **no Docker executable** and no agent/test-runner container. It cannot honestly claim to have rerun the SWE-bench task oracle here. To finish Route 2 without hiring anyone, run the official harness on an isolated Docker-enabled workstation/CI machine or cloud environment and return its `results.json`, case `report.json`, `test_output.txt`, `run_instance.log`, `patch.diff`, and run/job metadata. The visible source scripts already support sealing and later scoring without a human coder.

**Recommended next step:** First run a new ten-task, exact-SHA two-stage pilot using publicly available, preregistered tasks and separate hidden tests. Keep the complete frame (including errors) and measure whether there is any evaluable decision variation. Expand only after the feasibility is documented. No change to MR30.
