# MR33P1 candidate — exact repository-coherent sensitivity (NOT YET IN MAIN MANUSCRIPT)

**New verified empirical calculation (23 November 2026):** A finite-source sensitivity to entire-repository disturbances for the existing 853-session DS2-minus-DS1 recorded-RS1 result. This is a **candidate additive result, not a newly discovered general statistical method**, and does not replace any MR31R9-EP2 numbers.

## Originality compared with the locked paper

The locked analysis measures a positive +13.9612 percentage point mean RS1 visibility contrast over 853 paired sessions, reports repository-nested descriptive resampling, and finds a 120-record targeted *within-session* severity-change certificate. That calculation does not model **correlated errors or exclusion at the repository level**. This candidate computes two additional *exact* source-specific certificates for distinct systematic disturbances.

- **Whole-repository label reversal:** Reverse every original DS1/DS2 label in each selected source-qualified repository, preserve RS1/RS2 and all 853 matched sessions. The smallest number of repositories that can make the mean non-positive is **20 of 352**. With the 19 highest contributions the mean remains **+0.3309049 percentage points**; with the 20 highest it becomes **-0.1380282 points**. In the deterministic optimal witness 189 matched sessions and 558 matched episodes lie in those repositories; 3,326 of all eligible DS1/DS2 episodes reside there. The operation is extreme and not an empirical diagnosis of label errors.
- **Whole-repository exclusion:** Drop *all* paired sessions from each selected source-qualified repository, preserving labels in the remaining cohort. The smallest number whose removal makes the remaining-session mean non-positive is **74 of 352**. With 73 selected it stays **+0.1757265 points**, with 74 it becomes **-0.0081119 points**. The selected repositories include 310 paired sessions and 927 paired episodes in one deterministic minimal-cardinality witness. This is an adversarial selection exercise, not evidence that these repositories should be excluded.

Both witness sets are chosen *after* examining the original-record contrasts. Their sizes should not be called measured misclassification, statistical confidence, probable corruption, or evidence of verified terminal repair. The two mechanisms change different things and their thresholds must not be directly compared as if equivalent error rates. The global sample includes 1,229 source-qualified repositories; **352** contain at least one matched session.

## Exact optimality proof

For each paired session s, define d_s = RS1_rate_DS2(s) - RS1_rate_DS1(s).
For source-qualified repository r, define T_r = sum of d_s across its paired sessions, and m_r = number of its paired sessions. The locked sum is S = sum_r T_r = 6669/56 and the observed mean is S/853 = 6669/47768.

A whole-repository severity inversion negates T_r for selected r, hence new mean = (S - 2 * sum_{r in A} T_r)/853. It reverses sign exactly when sum_A T_r >= S/2. Whole-repository exclusion changes the mean to (S - sum_A T_r)/(853 - sum_A m_r), so with nonempty remaining cohort it reverses sign when sum_A T_r >= S.

For **either sign** decision, among sets of exactly k repositories the largest possible sum_A T_r is the sum of the k largest source-qualified repository contributions (simple exchange argument). Exact Fraction arithmetic verifies that the largest k-1 sum is below the relevant threshold and the largest k meets it. Thus the cardinality numbers **20** and **74** are globally minimal for the *two explicitly specified finite-data operations*. This proof is straightforward and must not be promoted as a new general statistical theorem.

## Evidence and reproducibility

Original public data: Tang et al. *How Coding Agents Fail Their Users*, EMNLP 2026 (https://aclanthology.org/2026.emnlp-main.1011/), Git commit c887cc920129b2db0bdf218c8550e98f74f42f7c; source JSON SHA-256 7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57.

Execute `python novelty_candidate/exact_repository_coherent_certificates.py --annotations /path/to/annotated_misalignments.json --out /path/to/aggregate.json`. The independent GitHub Actions run 45179212927 checks the original SHA-256, verifies counts, runs synthetic mathematical tests, and publishes aggregate-only JSON; **no raw records or IDs are republished here**. To reproduce use exactly the pinned original-author source, not an updated version.

Related methodological precedents that must be cited before incorporating the result: Paul R. Rosenbaum (2004/2005), sensitivity of observational studies; Giordano, Meager & Broderick (2026), finite-sample robustness to data removal (https://doi.org/10.1098/rsta.2025.0001); Huang et al. (TMLR 2025), failures of data-dropping approximations (https://openreview.net/forum?id=m6EQ6YdPXV). These establish that sensitivity to removing subsets of observations is **not new in statistics**. Our contribution is bounded to a verified case-specific extension for the original coding-agent source.

## Research decision

**Scientifically admissible as an additional secondary-analysis diagnostic**, with its restriction and prior-art citations. Does not repair the original dataset's unknown outcomes or independently calibrate DS1/DS2. Do not make this candidate the central paper thesis. MR31R9-EP2 remains the scientific baseline; the BDCC PDF template version must undergo separate source-text editing before any new result is typeset.
