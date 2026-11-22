# MR32P1 — Independent endpoint-contract challenge (candidate extension)

**Status:** evidence-first experimental extension, not a replacement for MR31R9-EP2. The MR31 manuscript, numbers and original-source labels are unchanged. This new result must be independently interpreted before it is integrated as a claim.

## Research question

For one public coding-agent benchmark run, do positive assertions in the last recorded model response (e.g., tests passed), or passing local test output anywhere in the trace, imply that the third-party benchmark marked the task as resolved? These endpoints are different. We measure the disagreement; we do not investigate deception, developer-pushback success, or production safety.

## Frozen external source

- Repo: https://github.com/gsmoon97/swe-agent-eval
- Exact commit: 2b8d930540ddaf0ae1290e718f1bd0741c70005e
- Input relative to root: evaluation/python/verified/20250329_OpenHands_Claude-3.5-Sonnet(Oct)/
- One OpenHands / Claude 3.5 Sonnet benchmark snapshot with 500 SWE-bench Verified task IDs.
- Benchmark status: third-party results/results.json, containing resolved, unresolved_ids and empty_error_patch_ids. No benchmark tests are rerun.
- Model statement: the last recorded response. Local receipt: literal tool output beginning EXECUTION RESULT of [ and containing a conservative test-pass marker. Such receipts need not apply to the final patch.

## Full-cohort method

All 500 IDs from the source's disjoint status lists must have one JSON trajectory, or the job fails. The primary comparison includes all records explicitly listed as resolved or unresolved; the other 53 are tracked separately. No sampling, human coding, LLM-based subjective labeling, model fitting, or retrospective cutoff selection. Frozen regex rules are in code/audit_endpoint_contract.py and checked against synthetic-only fixtures.

The workflow retrieves the independent upstream source pinned by exact commit SHA, then generates aggregate-only JSON and a report as Actions artifacts. Third-party transcripts, patch text and original issue content are not republished.

## Reproduce

From this derivative repo root:

    python -m unittest discover -s mr32/tests -p 'test_*.py' -v

After independently fetching the pinned external repository:

    python mr32/code/audit_endpoint_contract.py --source '/path/to/swe-agent-eval/evaluation/python/verified/20250329_OpenHands_Claude-3.5-Sonnet(Oct)' --out mr32/results

## Claim boundaries

Positive agent statements, local tests and third-party benchmark status are distinct observations. A positive tool receipt may concern earlier or narrower tests. An evaluation label is benchmark-defined, not a field safety guarantee. This separate SWE-bench cohort does not observe Tang et al.'s developer-pushback episode labels. Never pool the datasets or imply verification of the 16,118 historical outcomes. Lexical rules can miss paraphrases; false positives remain possible without independent label validation. Source summary numeric counters show inconsistencies with its own exhaustive status-ID lists and are explicitly disclosed.
