# Project 99llm-X1 — P9 executable protocol package

- Scientific baseline: **P8 remains LOCKED**; MR30 manuscript **untouched**.
- This archive is a **P9 acquisition/decision-lock specification only**, not completed oracle testing or a policy effectiveness result.
- `P9_EVIDENCE_ACQUISITION_PLAN_EN.md` explains sourced ways to obtain task-oracle outcomes without a second human coder, split between naturalistic GitHub CI and prospective executable harnesses.
- `scripts/p9_decide.py` computes three **blinded** ACCEPT/HOLD policies from decision-time-only records and seals the outcomes.
- `scripts/p9_reveal.py` reads **independent later oracle results**, admits only exact-SHA, prespecified independent test outcomes, and reports descriptive errors and missingness.
- `examples/` are **synthetic fixtures, not real cases**.
- `tests/` are software tests of the decision contract, NOT validations of agent repairs.

## Demonstrate the protocol locally (synthetic only)

```bash
python -m unittest discover -s tests -v
python scripts/p9_decide.py --input examples/SYNTHETIC_decision_only.jsonl --out synthetic_sealed
python scripts/p9_reveal.py --sealed-dir synthetic_sealed --oracle examples/SYNTHETIC_oracle_AFTER_SEAL.jsonl --out synthetic_score.json
```

Then use new, untampered source-linked task records with no future data. Never describe synthetic outputs as X1 empirical findings. Do not reuse the 21 already reviewed P8 cases for an unexposed effectiveness test.
