# Reproduce the source-locked numbers

Public code: https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis

1. Obtain `annotated_misalignments.json` **yourself** from the original authors at their exact [pinned GitHub commit](https://github.com/ND-SaNDwichLAB/coding-agent-misalignment/blob/c887cc920129b2db0bdf218c8550e98f74f42f7c/data/core/annotated_misalignments.json), using the GitHub **Raw** download or your own checkout. Do not commit or redistribute the third-party file here.
2. Independently calculate its SHA-256 and verify this exact value:
   ```text
   7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57
   ```
3. From the root of this repository run:
   ```bash
   python scripts/reproduce_visibility_robustness.py --annotations /path/to/annotated_misalignments.json --output /tmp/visibility.json
   python scripts/reproduce_nested_robustness.py --annotations /path/to/annotated_misalignments.json --output /tmp/aggregate_results.json
   python scripts/verify_replay.py /tmp/aggregate_results.json results/aggregate_results.json
   ```
4. The expected exact SHA-256 of the **deterministic aggregate JSON** is `2020eafd809b3a6888fefa35c48ad036322f3c4faaab0056303168791b60f7e1`. The verifier compares file bytes and expected digest. Environment is Python 3.10+; no third-party libraries are needed for numerical results. Optional figure regeneration:
   ```bash
   python -m pip install matplotlib numpy
   python scripts/reproduce_sensitivity_figure.py
   ```
   Figure script saves to `scripts/figures/` by default. The canonical published figure is `paper/figures/mr22_sensitivity_frontier.pdf` and is generated from stated aggregate counts; the plot is conceptual, not a data fit.
5. Recompile the **integrated manuscript and Appendix A** with TeX Live (pdfLaTeX) from `paper/`:
   ```bash
   cd paper
   pdflatex -interaction=nonstopmode preprint.tex
   pdflatex -interaction=nonstopmode preprint.tex
   ```

**What this procedure cannot reproduce:** extraction of initial episodes from raw conversations, original LLM annotation decisions, original source authors' human agreement/accuracy audit, eventual unknown recoveries, real deployment causal outcomes, other works' full published trial pipelines, or a peer-review verdict. Repository-nested bootstrap intervals describe the observed finite release and its cluster heterogeneity; they are not representative-sample confidence intervals.

The standalone supplement was consolidated into `paper/appendix_a.tex` in MR25 and is automatically included by `paper/preprint.tex`; do not compile `appendix_a.tex` by itself. The publicly hosted `paper/author_review_preprint.pdf` is the integrated 22-page working paper.
