# G19 — exact-node and phase receipt challenge: verified

Same 13 G10 tasks, same source patches, exact base and digest-pinned task images; five cells per task. All 13 CI jobs completed. Stronger admission uses exact collected node set equality, identical node-set digests, no unexpected or missing nodes, three determinate pytest phase receipts for each selected test, consistent exit code, and no collection errors, skips or xfails. The non-test staged tree is checked within each crossover. No replacement and no full historical benchmark regrade.

Aggregate: {"candidate_pairs":{"PASS/PASS":9,"HOLD/HOLD":2,"PASS/HOLD":1,"PASS/FAIL":1},"candidate_pairs_by_source":{"pass":{"PASS/PASS":7},"nonpass":{"HOLD/HOLD":2,"PASS/PASS":2,"PASS/HOLD":1,"PASS/FAIL":1}},"determinate_cells":56,"all_cells":65,"determinate_candidate_pairs":10,"base_version_reversals":10,"base_gold_controls":12,"discrimination_witnesses":7,"controlled_pass_fail_witnesses":1,"complete_task_cell_and_tree_agreement":13,"changed_tasks":[]}.

This check strengthens the identity of test evidence for the existing G10 result. HOLD cases remain unresolved. The result is a same-team repeat in the fixed selected frame, not a population rate or external human/laboratory validation. Source verdicts unchanged.

Verified run: https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45754529116
Run `python novelty_g19/verify_g19.py` for offline aggregate reconciliation with G10. It verifies summary consistency, not a fresh benchmark execution.