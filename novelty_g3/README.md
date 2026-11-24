# G3 — Licence-metadata exclusion gate for hypothetical outcome ascertainment

**Status (24 November 2026): scientifically checked additional candidate; NOT in MR31R9-EP2 or submitted.** G2 remains the exact ideal-information baseline; this independent G3 check adds a source-evidence admission constraint, without changing frozen scientific numbers or source labels.

Original source: Tang et al., EMNLP 2026, DOI 10.18653/2026.emnlp-main.1011, original-author release pinned to commit \`c887cc920129b2db0bdf218c8550e98f74f42f7c\`. Annotated source SHA-256:
\`7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57\`.

The original-author \`ReadMe.md\` explicitly limits raw trace redistribution by repository licenses and describes its \`misalignments.json\` subset as permissively licensed. Its public annotated metadata separately contain \`license_type\`, including the literal \`NO_LICENSE\` value. **This metadata field does not legally prove lack of use rights, lack of public access, or absence of an independent task oracle.** We evaluate an explicitly hypothetical conservative policy that excludes **only** \`NO_LICENSE\` rows when choosing follow-up cases. All other rows are *optimistically treated as if* their unknown outcome could be perfectly independently determined; this is an upper bound, not observed ability.

### Exact result on frozen 853-session cohort

- 2,352 originally unknown (RS2) episode statuses; all calculations concern hypothetical eventual **RV2** categorical status, never independently verified terminal code correctness.
- \`NO_LICENSE\`: 1,347 RS2 unknown statuses across 451 matched sessions, contributing 1,942,518 out of 3,544,605 exact interval-width units (**54.8021%**).
- All non-\`NO_LICENSE\`: 1,005 RS2 unknown statuses across 402 matched sessions, contributing 1,602,087 units (**45.1979%**).
- **No-license-exclusion ceiling:** Even perfect resolution of all 1,005 remaining statuses can shrink the sharp identification interval at most **45.1979%**. Its width remains **90.36817 percentage points** from an initial **164.89910**.
- For every possible assignment of outcomes among the 1,005 eligible statuses, the sharp interval still has lower endpoint at most **−3.18498 percentage points** and upper endpoint at least **+12.65226 percentage points**. Hence the sign cannot be certified in either direction under this exclusion policy.
- With no eligibility exclusions, the source-specific half-width optimum remains **704** unknown statuses. **Any selection of just 704 outcomes that halves the interval must include at least 291 \`NO_LICENSE\` statuses**; at 290 the best possible exact weight sum is 1,771,560, below the necessary 1,772,302.5, while at 291 it is 1,772,820.
- Even after granting access to every one of the other 1,005 statuses, half-width contraction requires at least **68 \`NO_LICENSE\`** statuses as well. These alternative minima have different total work counts; do not compare them as monetary or time estimates.

### Why this is a bounded novelty claim

The original authors already disclose the rights/trace-release limitation; missing-data partial identification and greedy allocation of binary follow-up records are well-established. The new **case-specific** calculation intersects that documented source attribute with the frozen matched-session weights and shows that a transparency/evidence admission gate defeats the ideal G2 half-width and sign possibility certificates.

This is not a newly invented general information-theoretic theorem, not verified licensing or actual accessibility for any individual repository, and not proof of improvement in evaluation practice. Cross-episode unrestricted binary completions remain a hypothetical sensitivity envelope. Do not claim that \`NO_LICENSE\` means the trace could never be accessed or that an explicitly licensed repository contains the necessary final-state evidence.

### How to reproduce using the original authors' source

\`\`\`bash
python novelty_g3/verify_access_gate.py --annotations /path/to/original/annotated_misalignments.json --output /tmp/99llm_g3_aggregates.json
\`\`\`

The script refuses a nonmatching SHA, asserts all cohort values and exact integer thresholds, and emits aggregate fields only. A GitHub Actions workflow executes directly against the pinned upstream original author file. Do not redistribute original rows, repository/session identifiers, source quotes, or underlying transcripts.

### Editorial decision
G3 is stronger than presenting G2's 704 alone because it demonstrates a nontrivial **source-admissibility obstruction**. If and only if a compact, native editable MR31R9-EP2 manuscript is reconstructed with full visible-text parity, consider replacing the separate G2 results text with one compact paragraph juxtaposing the ideal 704 and the conservative metadata-gated 45.20% ceiling. Keep all mathematical proofs, explicit definitions, and the license semantics in the supplement. Hold MR33P1 and MR32 outside the main paper. No scientific baseline changed and no authorship or journal approval was inferred.
