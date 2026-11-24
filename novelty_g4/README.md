# G4 — Objective-sensitive, repository-unit evidence rescue (24 Nov 2026)

**Research candidate only; original paper MR31R9-EP2 is NOT changed, and no real follow-up audit is claimed.**

G4 extends the previously source-verified G2 ideal-information frontier and G3 metadata-gated ceiling. The key question is: when the originally published **repository-level** license metadata exclude `NO_LICENSE` records under a *declared hypothetical policy*, how many exclusions must be relaxed to make each different scientific objective feasible, treating unknown eventual RV2 status as binary? The metadata value does **not** establish a legal prohibition or actual trace inaccessibility.

## Original-author source lock
Tang et al. (EMNLP 2026), original-author code commit `c887cc920129b2db0bdf218c8550e98f74f42f7c`. SHA256 for `data/core/annotated_misalignments.json`: `7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57`.

The held-constant cohort: 853 equal-weight DS1/DS2 matched sessions; 2,775 episodes; 352 matched source repositories; 2,352 RS2 unknown statuses. Only 1,005 unknown outcomes in 137 repositories are outside `NO_LICENSE`, with 1,602,087 exact weight units. The 1,347 excluded unknown outcomes in 215 repositories contribute 1,942,518 units. Total unidentifiable width 3,544,605 units, exact denominator 2,149,560.

## NEW G4 result (hypothetical perfect ascertainment)

After assuming **all 1,005 OTHER unknown outcomes** are perfectly known, minimum additional excluded `NO_LICENSE` outcomes for:
- possible positive sign: **28** episodes; or **1** complete repository if selecting whole repositories;
- at least halving original width: **68** episodes; or **3** complete repositories;
- possible negative sign: **108** episodes; or **5** complete repositories.

For the whole-repository counts, the baseline assumption is that **ALL 137 OTHER repositories** are already completely resolved, so the total numbers of repositories hypothetically inspected are **138, 140 and 142**, respectively. All 215 `NO_LICENSE` matched repositories belong to original SpecStory source, so this metadata grouping is source-confounded.

The first five repository weights have exact cumulative sums `83706,150066,204666,258342,300258`, respectively. An unrestricted ideal portfolio of **56** complete repositories would halve initial width (vs **704** individually chosen unknown episodes in the ideal episode-unit G2).

Sign thresholds describe **the ability to identify a sign under favorable, hypothetical labels, not guaranteed sign-certification or observed success**. Positive and negative extremal assignments differ. The width contraction is guaranteed by a selected unit *only if its entire unknown outcome set can actually be perfectly classified*. No costs, permissions, repair outcomes, probabilities, or external validation were observed.

## Executed verification
[Verified full-source GitHub Actions run](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45332933058) passed: pinned upstream SHA, previous G3 source-data check, full 352-repository grouping, exact integer endpoint thresholds, and export of **aggregate-only JSON**. The raw source is held ephemerally and deleted before artifact upload.

Run locally after separately obtaining the unchanged original author's JSON:
```bash
python novelty_g4/verify_repository_rescue.py --annotations /path/to/annotated_misalignments.json --out /tmp/g4_aggregate.json
```
The separate candidate package includes a 3-page peer-review English note and an exact-rational episode-unit script with synthetic exhaustive small-instance tests.

## Originality decision
Source-specific exact calculation at the intersection of a **fixed missing-outcome contrast**, a **declared source-metadata eligibility gate**, an **episode vs repository acquisition unit**, and **opposite sign/width objectives**. Classical missing-data partial identification, double-sampling/follow-up recovery, and greedy choice of independent weighted units are established; G4 does not claim a new general theorem or algorithm. No new research manuscript or causal effectiveness claim is warranted. Keep G4 **research candidate** and integrate at most one concise paragraph/table into the existing paper after exact native-source production parity is restored. The unsafe 28-page MDPI reflow is not submission-ready.
