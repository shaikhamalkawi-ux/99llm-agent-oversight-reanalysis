# G12 — verified released-patch provenance and grade transport

**Status:** source-locked audit completed. MR31R9-EP2, G10 and G11 source grades unchanged.

All six Termination Lag settings: 2,400 runs, 26,666 patch rows. Compare the 16-hex IDs with the SHA1-prefix convention in the original grading script (build_ml_preds.py at 40a5b65aabf02063cd7a940a82bdee10fdbc91e6). The data card documents dependency-file projection and full-patch grading.

- 26,448/26,666 raw patch texts match the reported identifier by this convention; 218 do not.
- All 211 records with positive declared dependency-files-removed counts mismatch. Seven further mismatches have zero declared removals (all in the Laguna multilingual setting); six simple newline variants recover none. These are unexplained digest inconsistencies, NOT proof of invalid original grades.
- 2,371 nonempty final patch IDs, of which 2,350 match; 20 mismatches have declared removals and one does not. The other 29 runs have no final patch ID and are reported separately.
- 149 same-task same-released-byte multirow groups (362 patch rows), 22 with different reported IDs, 127 across settings; zero mixed source grades in these groups. Nine duplicate exact final-patch groups (18 runs) likewise agree. No same-task reported ID maps to multiple released byte strings. This is limited consistency evidence, not independently repeated evaluation.
- All 13 frozen G10 patches match the source hash convention and have zero declared removals. Twelve are parseable using non-applying git apply --numstat, one (mini-SWE-agent nonpass) is not, even in diagnostic --recount mode. Thus the observed syntax HOLD is not explained by declared dependency projection or a simple newline variant. G11's context-mismatch case remains an application HOLD. The prefix convention is not a formal dataset ID guarantee; a digest match alone cannot establish historical execution.

The main contribution is a provenance boundary: byte-identity consistency, patch applicability, test-identity and outcome validity are separate verification objects. The G12 result is a secondary source audit, not a new mathematical theorem or a new independent benchmark grade. No original patch text, identifiers, or source rows exported.

[Verified run](https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis/actions/runs/45620862263). [Aggregate](G12_verified_summary.json). [Upstream dataset card](https://huggingface.co/datasets/musacim/termination-lag-trajectories); [upstream grading hash convention](https://github.com/musacim/termination-lag/blob/40a5b65aabf02063cd7a940a82bdee10fdbc91e6/code/grading/build_ml_preds.py).
