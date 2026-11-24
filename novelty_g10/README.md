# G10 — Controlled test-version crossover and full-frame structural context

**Status:** verified controlled pilot and static whole-frame audit, 25 November 2026. MR31R9-EP2 remains unchanged.

## Controlled execution

Three nonpassing runs were selected deterministically, one per original Verified setting, before the intervention. Exact base commits were restored offline from the official instance images; images and candidate/reference patches are hashed. Five cells used identical named FTP selectors, same image and separate disposable containers. Local/reference intervention touched only reference-test paths. No network access, no host credentials, no transcript command execution. PASS/FAIL requires completed JUnit results without errors or skips.

| Setting | Base/local | Base/reference | Candidate/local | Candidate/reference | Gold/reference |
|---|---|---|---|---|---|
| Qwen3-Coder OpenHands | PASS | FAIL | HOLD | HOLD | PASS |
| Laguna OpenHands | PASS | FAIL | PASS | FAIL | PASS |
| Qwen3-Coder mini-SWE-agent | PASS | FAIL | HOLD | HOLD | PASS |

The Laguna witness uses one FTP node on the official Astropy task image (public source image tag and digest in aggregate). The non-test staged-tree digest is identical across its candidate-local and candidate-reference cells, and identical across the two base cells. Changing the reference test-file version, not the recorded non-test tree, changes the selected test outcome. Gold-reference passes. Two other candidate patches do not apply exactly; they remain HOLD, not failed repairs. Their base/reference and gold/reference controls execute successfully. This establishes a conditional experimental witness, not frequency, a whole benchmark rerun, or proof of objective program correctness. The image differs from the historical agent environment; tracked-tree invariance does not prove all possible runtime state identical.

## Whole-frame structural opportunity

All 500 SWE-bench Verified tasks; 1,516 reference FTP identifiers. Of 364 supported pytest-style identifiers, 98 have changed named-function ASTs, 52 have equal ASTs, 212 have absent or ambiguous base definitions, one has an unfound reference definition and one an unparseable reference diff. The other 1,152 identifiers are unsupported by this narrow parser. At task level, 63/500 have all FTP definitions found in both base and reference versions; 60/500 have at least one changed AST (in fact all their FTP definitions differ), and 3/500 all match. This is a conservative structural finding over a complete frame, not test execution or semantic inequivalence. Parameterized node IDs map to function definitions. Unknowns retained.

## Originality boundary

Prior test-adequacy, hidden-test and repair-overfitting studies establish the general concept. The candidate contribution is the source-linked chain from recorded same-name success (G8) to static identity (G9) to an actual fixed-candidate test-file intervention (G10), with complete-frame structural context and explicit HOLDs. The single witness warrants an existence claim only.

## Reproduction
- Pilot: https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45484175756
- Full-frame static audit: https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45484269694
- [Verified aggregate results](G10_verified_summary.json)

The preliminary pilot encountered a selection/preparation assertion and then image base-commit mismatch; both were corrected without selecting replacement tasks. The two exact-application HOLDs are unresolved. Do not silently use fuzzy patch application.
