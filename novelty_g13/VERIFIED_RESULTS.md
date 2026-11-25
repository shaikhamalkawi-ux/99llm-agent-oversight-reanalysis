# G13 — fixed Pylint collection closure

Verified run: https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45621655555. Fixed G10 Laguna nonpass rank 1, same recorded patch, base commit and image digest. File-level collection with exact required node selection and setup/call/teardown receipts.

| Cell | Outcome | Collection evidence |
|---|---|---|
| Base/local | PASS | 51 discovered, one exact required test executed |
| Base/reference | HOLD | module-not-found during collection, zero required tests executed |
| Candidate/local | PASS | 51 discovered, one exact required test executed |
| Candidate/reference | HOLD | module-not-found during collection, zero required tests executed |
| Gold/reference | HOLD | exit 4, zero required tests collected |

The base and candidate non-test-tree digests each agree between local/reference arms. The first two G13 attempts failed due to our instrumentation setup, specifically a pytest hook signature error; they are not source outcomes. The corrected run recovers the original positive local receipt and confirms that changing reference test files prevents valid collection under this invocation. The gold control is unresolved, so there is NO new PASS/FAIL crossover witness. Do not treat exit 2/4 as a failed test or infer the historical benchmark cause. Do not install an unpinned dependency or silently map test identities. The G10 cohort remains nine PASS/PASS, one PASS/FAIL, three unresolved. MR31R9-EP2 unchanged.

The current official SWE-bench runner documents repository-specific commands and a Pylint PYTHONPATH workaround. A historically faithful rerun would require the exact original harness/environment and full outcome records; this separate intervention is not such a rerun. This is a bounded closure, not a request for more arbitrary environment tuning.