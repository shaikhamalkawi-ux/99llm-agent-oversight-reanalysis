#!/usr/bin/env python3
"""Produce an exact-PDF, source-honest manuscript/appendix delivery.
No scientific or author metadata edits. This is a submission-PREPARATION
bundle, not journal submission and not an invented MR31 LaTeX archive.
"""
from __future__ import annotations
import hashlib, json, re, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
from pypdf import PdfReader, PdfWriter

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"paper"/"99llm_MR31R9_EP2_GitHubSynced_AUTHOR_REVIEW.pdf"
OUT=ROOT/"submission_preparation"/"out"
FINAL=OUT/"99llm_MR31R9_EP2_AuthorApproval_Closure"
MAIN=FINAL/"01_Journal_Review"/"Manuscript_Main.pdf"
SUPP=FINAL/"01_Journal_Review"/"Supplementary_Computational_Record.pdf"
COMBINED=FINAL/"02_Reader_Copy"/"Manuscript_and_Supplement_Combined.pdf"
REPORT=FINAL/"03_Production_and_Approval"/"PRE_SUBMISSION_QA.json"
MANIFEST=FINAL/"SHA256SUMS.txt"
CURRENT_REPO="https://github.com/shaikhamalkawi-ux/99llm-agent-oversight-reanalysis"

def digest(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for block in iter(lambda:f.read(2**20),b""):h.update(block)
    return h.hexdigest()

def save_pages(reader,span,target):
    w=PdfWriter()
    for i in span:w.add_page(reader.pages[i])
    w.add_metadata({"/Title":"Resolution Visibility Is Not Recovery: Evidence Limits in Coding-Agent Evaluation After Developer Pushback",
                    "/Subject":"Author-review copy; not submitted"})
    target.parent.mkdir(parents=True,exist_ok=True)
    with open(target,"wb") as f:w.write(f)

def zip_files(target,root,paths):
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in paths:z.write(p,str(p.relative_to(root)))
    with zipfile.ZipFile(target) as z:
        bad=z.testzip()
        if bad:raise RuntimeError("Zip CRC failure: "+bad)

def main():
    if not SOURCE.exists():raise FileNotFoundError(SOURCE)
    if FINAL.exists():shutil.rmtree(FINAL)
    FINAL.mkdir(parents=True)
    reader=PdfReader(str(SOURCE),strict=False)
    if reader.is_encrypted:raise RuntimeError("Source PDF encrypted")
    alltexts=[p.extract_text() or "" for p in reader.pages]
    n=len(reader.pages)
    candidates=[i for i,t in enumerate(alltexts)
       if i>=n//2 and ("Supplementary Computational Record" in t[:500]
                       and "Matched-session endpoint" in t[:1200])]
    if len(candidates)!=1:raise RuntimeError("Cannot verify supplement boundary: "+str(candidates))
    split=candidates[0]
    if not(20<=split<n and 1<=n-split<=12):
        raise RuntimeError("Implausible split boundary")
    save_pages(reader,range(split),MAIN)
    save_pages(reader,range(split,n),SUPP)
    COMBINED.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(SOURCE,COMBINED)
    combined_text="\n".join(alltexts)
    main_text="\n".join(alltexts[:split])
    notes={
      "title":"Resolution Visibility Is Not Recovery: Evidence Limits in Coding-Agent Evaluation After Developer Pushback",
      "source_pdf":str(SOURCE.relative_to(ROOT)),
      "source_sha256":digest(SOURCE),"main_pages":split,
      "supplement_pages":n-split,"combined_pages":n,
      "main_pdf_sha256":digest(MAIN),"supplement_pdf_sha256":digest(SUPP),
      "combined_pdf_sha256":digest(COMBINED),
      "linked_github_in_main":("99llm-agent-oversight-reanalysis" in main_text),
      "abstract_present":bool(re.search(r"Abstract",main_text,re.I)),
      "conclusion_present":bool(re.search(r"Conclusion",main_text,re.I)),
      "references_present":bool(re.search(r"References",main_text,re.I)),
      "submission_status":"AUTHOR APPROVAL REQUIRED -- NOT SUBMITTED",
      "scientific_content_modified":False,
      "MR32P1_in_main_pdf":False,
      "MR32P2_in_main_pdf":False,
      "author_metadata_pending":bool(re.search(r"author information pending|author.*confirmation|affiliations pending",main_text,re.I)),
      "requires_current_authoritative_source":True,
      "field_notes":"The published MR31R9-EP2 PDF is the only verified current manuscript artifact; historical MR26/MR30 TeX cannot be silently substituted.",
      "sensitive_raw_episode_rows_included":False
    }
    # Guard against missing scientific sections and source/version confusion.
    if not all(notes[k] for k in ["linked_github_in_main","abstract_present","conclusion_present","references_present"]):
       raise RuntimeError("Unexpected current PDF content: "+str(notes))
    assert len(PdfReader(str(MAIN)).pages)==split
    assert len(PdfReader(str(SUPP)).pages)==n-split
    assert len(PdfReader(str(COMBINED)).pages)==n
    assert digest(COMBINED)==digest(SOURCE)
    # Check PDF page-content stream parity (content is not typeset anew).
    for i in range(n):
        original=reader.pages[i].get_contents().get_data() if reader.pages[i].get_contents() else b""
        target=MAIN if i<split else SUPP
        offset=i if i<split else i-split
        page=PdfReader(str(target)).pages[offset]
        derived=page.get_contents().get_data() if page.get_contents() else b""
        if hashlib.sha256(original).digest()!=hashlib.sha256(derived).digest():
            raise AssertionError("Page content stream mismatch at "+str(i+1))
    notes["pdf_page_content_stream_parity"]=f"{n}/{n} PASS"
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (REPORT.parent/"README_FIRST.md").write_text(
        "# 99llm | MR31R9-EP2 submission-preparation handoff\n\n"
        "This contains a faithful split of the EXISTING 33-page author-review PDF. "
        "No scientific text, source data, figure, citation, or numeric result was edited.\n\n"
        "The current 33-page combined reading copy is byte-identical to the GitHub PDF. "
        "The Main and Supplement are split at the original heading and page-content-stream verified.\n\n"
        "STATUS: NOT SUBMITTED and NOT YET FORMALLY READY. The author list/affiliations, "
        "CRediT, funding, competing interests, ethics and AI-use disclosure require "
        "human-author approval. Current version-matched editable source (MR31R9) "
        "is not in the verified GitHub repository; do not upload historical MR26 TeX "
        "as if it compiled the present article. Complete current source prior to journal upload.\n\n"
        "MR32P1 and MR32P2 are repository-side exploratory research records, not "
        "scientific results in this MR31R9-EP2 paper. They must not be described as included here.\n\n"
        "Reanalysis repository: "+CURRENT_REPO+"\n",encoding="utf8")
    (REPORT.parent/"Author_Approval_Form.md").write_text(
        "# Required author approvals (complete before submission)\n\n"
        "- [ ] Confirm each author's full legal publication name and order.\n"
        "- [ ] Confirm institutional affiliations and corresponding-author email.\n"
        "- [ ] Confirm ORCID IDs as applicable.\n"
        "- [ ] Obtain consent from all authors for this version and submitted venue.\n"
        "- [ ] Complete CRediT contribution roles without attributing work not performed.\n"
        "- [ ] Confirm exact funding/grant record or approve 'no external funding' if true.\n"
        "- [ ] Confirm conflicts-of-interest declaration.\n"
        "- [ ] Approve disclosure of actual AI-assisted literature inspection, code, mathematical checking and drafting.\n"
        "- [ ] Confirm institution's ethics requirements for secondary public data analysis.\n"
        "- [ ] Confirm original-source redistribution rights; only derived aggregates shared.\n"
        "- [ ] Restore version-matched editable MR31R9 source and build exact manuscript.\n"
        "- [ ] Confirm repository availability statement, any permanent DOI and no simultaneous submission.\n"
        "- [ ] Perform journal portal preflight and final author reading.\n",encoding="utf8")
    (REPORT.parent/"Cover_Letter_DRAFT.md").write_text(
       "# Cover letter DRAFT — require author sign-off\n\n"
       "Dear Editor-in-Chief,\n\n"
       "Please consider our manuscript, *Resolution Visibility Is Not Recovery: Evidence Limits "
       "in Coding-Agent Evaluation After Developer Pushback*, for consideration as an Article in "
       "*Big Data and Cognitive Computing*.\n\n"
       "The article asks what can legitimately be inferred from conversation-derived resolution "
       "labels when terminal software-repair outcomes remain unobserved. It reanalyzes a fixed "
       "public release of 16,118 annotated episodes from Tang et al. and quantifies how recorded "
       "visibility contrasts depend on session eligibility, unknown outcomes, and source-assigned "
       "severity labels. Among 853 matched sessions the recorded visibility contrast is +13.96 "
       "percentage points, yet logical bounds for eventual post-pushback outcome differences "
       "cross zero. An exact, adversarial source-label sensitivity calculation illustrates "
       "that stable observed associations and valid outcome inferences are distinct questions.\n\n"
       "The contribution is a documented secondary reanalysis and evidence-accounting example, "
       "not a new agent benchmark, independent annotation, verified task-repair study, or "
       "causal evaluation of human oversight. The original third-party episode rows are not "
       "redistributed. The public derivation materials and limits are described in the "
       "manuscript and its linked repository.\n\n"
       "We believe this fits the journal's interest in robust data interpretation and "
       "evaluation of cognitive computing systems.\n\n"
       "[The submitting author must confirm originality, exclusive submission, all author approvals, "
       "any prior submissions and relevant disclosures before using this letter.]\n\n"
       "Sincerely,\n[Approved corresponding author and affiliation]\n",encoding="utf8")
    (REPORT.parent/"Science_Freeze.md").write_text(
       "# Science freeze\n\nMR31R9-EP2 remains authoritative for the current manuscript. "
       "No numerical, analytical, statistical, figure, or citation result has been added by "
       "this PDF-only split. MR32P1/P2 are NOT merged into the submission manuscript.\n\n"
       "The temporal MR32P2 test counted 28 benchmark-unresolved among 98 with an explicit "
       "source-edit acknowledgement preceding a local passing-test receipt; it cannot guarantee "
       "that the test followed the final actual code edit or establishes task correctness. "
       "The pattern is not claimed as a novel theory or merged with the original cohort.\n",encoding="utf8")
    paths=sorted(p for p in FINAL.rglob("*") if p.is_file())
    MANIFEST.write_text("".join(f"{digest(p)}  {p.relative_to(FINAL)}\n" for p in paths),encoding="utf8")
    rootzip=OUT/"99llm_MR31R9_EP2_AuthorApproval_SubmissionPreparation.zip"
    paperszip=OUT/"99llm_MR31R9_EP2_Paper_and_Supplement_Only.zip"
    zip_files(rootzip,FINAL,[*paths,MANIFEST])
    zip_files(paperszip,FINAL,[MAIN,SUPP])
    print(json.dumps({"qa":notes,"full_zip":str(rootzip),"full_zip_sha256":digest(rootzip),
      "paper_supp_zip":str(paperszip),"paper_supp_zip_sha256":digest(paperszip)},indent=2))
if __name__=="__main__":
    main()
