# G11 — verified regression contract and identifier representation diagnostics

**Status:** closed as an evidence-bound negative/partial result. MR31R9-EP2 and G10 source verdicts unchanged.

Sphinx-7889 (Laguna nonpass rank 2): exact six required node IDs, base 1 FTP fail and 5 PTP passes, candidate and developer gold 6/6 pass. File-level replay agrees. This does not reproduce the historical whole-task nonpass under the narrower new harness; no PTP-only failure established.

Sphinx-9367 (Laguna nonpass rank 3): direct named invocation yields exit 4 and no collection. File-level execution collects 42 items, 29 extra relative to exact required membership. Base FTP fails, candidate/gold FTP pass; 12/25 exact PTP identifiers pass in all three cells, 13/25 unascertained, 29 extra items pass. Candidate/gold return zero but exact required identity is incomplete. First-token representation maps 11 of the 13 missing IDs uniquely to unused passing items; two remain ambiguous/unmatched. This is a diagnostic, NOT recoding. Historical nonpass cause remains unproven. Two exact candidate applications remain HOLD: Sphinx-10614 context mismatch, pytest-5840 corrupt patch. No fuzzy application, no repair of source patches.

Results support the need to distinguish test identity, test-set completeness and harness transport. They do not establish a new historical misgrading rate, nor a generalized benchmark flaw.

Verified runs: [contract](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45551510016), [file-level](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45551350071), [identifier diagnostics](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45551510130). All original logs preserved. Aggregates: G11_verified_summary.json.
