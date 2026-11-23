# 99llm — exact unknown-outcome ascertainment frontier (candidate, NOT in manuscript)

**Research decision (24 November 2026):** The existing MR31R9-EP2 scientific paper is frozen. This candidate answers a *different* question from adversarial relabeling: given the same 853 paired sessions, what is the maximum reduction in the sharp hypothetical eventual-RV2 contrast interval that could be obtained from **perfect independent ascertainment of currently unknown RS2 outcomes** at a specified budget?

## Fixed contract and validated numbers

Original author data: Tang et al., EMNLP 2026; pinned upstream commit \`c887cc920129b2db0bdf218c8550e98f74f42f7c\`, original \`data/core/annotated_misalignments.json\` SHA-256 \`7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57\`. The original source is retrieved for analysis but **not redistributed**.

- 16,118 original episodes; 15,948 DS1/DS2 episodes.
- Exactly 853 original matched sessions, 2,775 matched episodes, 352 represented source-qualified repositories.
- Within these sessions, **2,352** current RS2/unknown resolver statuses: 1,589 DS1 and 763 DS2.
- The already-published source-conditional RV2 identification interval is **[-77.71590, +87.18319] percentage points**, width **164.89910**. This is *not* a confidence interval or an independently established software-repair rate.

For each as-yet-unknown record in severity group \`g\` in matched session \`s\`, let \`n_{s,g}\` be the number of original episodes with that label in that session. A **perfectly determined** subsequent binary RV2/non-RV2 status shrinks the sharp interval width by exactly \`1/(853*n_{s,g})\`, independently of the observed value. With equal hypothetical per-episode ascertainment costs, sorting these nonnegative weights gives the **sharp optimal width-reduction frontier**.

| Hypothetical ideal ascertainment target | Smallest individual unknown episodes |
| --- | ---: |
| 25% narrower sharp interval | 352 |
| 50% narrower sharp interval | 704 |
| 75% narrower sharp interval | 1,257 |
| 90% narrower sharp interval | 1,773 |
| Remaining width at most 50 percentage points | 1,108 |

**Possible sign certificates, not guaranteed outcomes:** Even with perfect *hindsight* selection and every checked result favoring the same sign, no fewer than **663** independent unknown episode outcomes could make the updated lower bound *strictly positive*, and no fewer than **744** could make the updated upper bound *strictly negative*. An unfavorable result or an unauditable episode increases actual requirements or may make a sign certificate impossible. A sign can remain unidentified despite a large reduction in interval width.

Under the different *unit-cost definition* that one verification effort resolves *all* unknowns in a chosen matched session, the optimistic minimum numbers of complete sessions are 332 and 372 for positive and negative certificates. Under a complete source-qualified-repository verification definition they are 49 and 63 respectively. These are distinct, unmeasured cost models: comparing these counts directly as costs would be erroneous.

## Exact proof and scope

Write \`D = d0 + sum_unknown_DS2(w_i*y_i) - sum_unknown_DS1(w_i*y_i)\`, with \`y_i in {0,1}\`, \`w_i=1/(853*n_{s,g})\` and source-fixed observed \`d0\`. Before follow-up, \`L=d0-sum_DS1(w_i)\`, \`U=d0+sum_DS2(w_i)\`. Revealing any one unknown binary outcome moves either \`L\` upward or \`U\` downward by \`w_i\`; the other endpoint does not change. Hence interval width always shrinks by \`w_i\`. Under equal unit cost, for any k the maximum shrinkage is the sum of the k largest weights, by the elementary exchange argument. A *potential* positive sign certificate requires favorable bound movement greater than \`-L\`; a negative certificate requires movement greater than \`U\`. Both are sharp because the original released source places no further constraints on independent missing outcomes.

All comparisons use exact scaled integer arithmetic (scale 2520). These values are **case-specific implications of established partial-identification and follow-up-design principles**, not new general statistical theory.

## Precedents and limitations

- Tang et al., 2026: original source corpus, labels, recorded visibility and missingness: https://aclanthology.org/2026.emnlp-main.1011/
- Manski, 2005: partial identification with missing data: https://doi.org/10.1016/j.ijar.2004.10.006
- Double sampling for informatively missing data (2024): https://pmc.ncbi.nlm.nih.gov/articles/PMC11639654/
- Giordano, Meager and Broderick (2026): finite-sample robustness to data removal; a **different** problem from this ideal ascertainment calculation: https://doi.org/10.1098/rsta.2025.0001
- MR33P1 repository-coherent sensitivity remains a separate candidate.

**No observed follow-up outcomes were acquired.** It is not established that RS2 missing statuses can be independently recovered in practice, nor that RV2 resolver status means independently verified terminal code correctness. The original labels, session eligibility, lack of population sampling, and lack of causal identifiability all remain unchanged. No human coder was added. This should not be called an empirical validation or a field-tested audit plan.

## Reproduction

\`\`\`bash
python novelty_ascertainment/optimal_unknown_outcome_frontier.py --selftest
python novelty_ascertainment/optimal_unknown_outcome_frontier.py --annotations /path/to/original/annotated_misalignments.json --output result.json
\`\`\`

The script refuses a non-matching original SHA-256 and exports only aggregates, never original rows or repository/session IDs. The CI workflow can obtain the original data directly from the original authors' pinned public release and run these tests. Review candidate only: MR31R9-EP2 remains the unchanged manuscript baseline pending source-text correction and author approval.
