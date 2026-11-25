#!/usr/bin/env python3
"""G15 forensic source recovery: read-only PDF inventory, no manuscript replacement."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"paper/99llm_MR31R9_EP2_GitHubSynced_AUTHOR_REVIEW.pdf"
BLOB="f65eb0485eee897f652795f2b684410d1af55bfc"
def sha(b):return hashlib.sha256(b).hexdigest()
def git_blob(b):return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
def overlap_fraction(a,b):
    if a.get_area()<=0:return 0
    return (a&b).get_area()/a.get_area()
def opaque_rects(page):
    # Strict admission: exact axis-aligned rectangle fill, fully opaque;
    # ignore any merely rectangular bounding box of a nonrectangular path.
    out=[]
    for d in page.get_drawings():
        if d.get("type") not in ("f","fs") or d.get("fill") is None or d.get("fill_opacity",1)<0.999999:continue
        if len(d.get("items",[]))!=1 or d["items"][0][0]!="re":continue
        r=fitz.Rect(d["items"][0][1])
        if r.is_empty or r.is_infinite:continue
        out.append((d["seqno"],r,tuple(d["fill"])))
    return out
def traces(page):
    rects=opaque_rects(page);visible=[];hidden=[];partial=[];invisible=[]
    for s in page.get_texttrace():
        seq=s["seqno"]
        for ch in s["chars"]:
            cp,gid,origin,bb=ch
            try:c=chr(cp)
            except ValueError:c="\ufffd"
            r=fitz.Rect(bb)
            info={"char":c,"origin":[round(x,4) for x in origin],"bbox":[round(x,4) for x in r],"seq":seq,
                  "font":s.get("font",""),"size":round(s.get("size",0),3),"dir":s.get("dir",(1,0))}
            if s.get("type")==3 or s.get("opacity",1)==0:
                invisible.append(info);continue
            hits=[(q,z,color) for q,z,color in rects if q>seq and z.intersects(r)]
            full=[(q,z,color) for q,z,color in hits if overlap_fraction(r,z)>=.999]
            if full:
                info["covered_by_seq"]=min(q for q,_,_ in full);hidden.append(info)
            else:
                if hits and any(overlap_fraction(r,z)>.05 for _,z,_ in hits):partial.append(info)
                visible.append(info)
    return visible,hidden,partial,invisible,rects
def grouped(chars):
    # Texttrace provides visible glyph origins and draw order. Reassemble
    # horizontal text by baseline, then x. Do not combine columns or equations
    # semantically; record line fragments with positions for editorial review.
    horizontal=[g for g in chars if abs(g["dir"][0]-1)<.001 and abs(g["dir"][1])<.001]
    rotated=len(chars)-len(horizontal)
    lines=[]
    for g in sorted(horizontal,key=lambda c:(c["origin"][1],c["origin"][0],c["seq"])):
        y=g["origin"][1]
        if lines and abs(lines[-1]["y"]-y)<0.7:lines[-1]["glyphs"].append(g)
        else:lines.append({"y":y,"glyphs":[g]})
    out=[]
    for line in lines:
        groups=[];prev=None
        for g in sorted(line["glyphs"],key=lambda q:(q["origin"][0],q["seq"])):
            # Large gaps split disjoint cells/columns rather than assert reading order.
            gap=g["origin"][0]-(prev["bbox"][2] if prev else g["origin"][0])
            if groups and gap>max(15,2*g["size"]):groups.append([])
            elif not groups:groups.append([])
            groups[-1].append(g);prev=g
        for grp in groups:
            pieces=[];last=None
            for g in grp:
                if last is not None and g["char"]!=" " and last["char"]!=" " and g["origin"][0]-last["bbox"][2]>max(1.4,.16*g["size"]):pieces.append(" ")
                pieces.append(g["char"]);last=g
            out.append({"y":round(line["y"],3),"x":grp[0]["origin"][0],"text":"".join(pieces),"n":len(grp)})
    return out,rotated
def synthetic():
    d=fitz.open();p=d.new_page()
    p.insert_text((70,100),"OLD CONTENT",fontsize=12)
    p.draw_rect(fitz.Rect(65,84,180,105),color=None,fill=(1,1,1),overlay=True)
    p.insert_text((70,100),"NEW CONTENT",fontsize=12,overlay=True)
    v,h,q,i,r=traces(p)
    assert "OLD CONTENT"=="".join(x["char"] for x in h)
    assert "NEW CONTENT"=="".join(x["char"] for x in v)
    print("G15 synthetic opaque-overlay glyph admission PASS")
def main(out):
    synthetic();out.mkdir(parents=True,exist_ok=True)
    b=P.read_bytes();assert git_blob(b)==BLOB
    d=fitz.open(P);assert len(d)==33
    records=[];pages=[]
    for j,p in enumerate(d,1):
        v,h,q,i,r=traces(p);lines,rot=grouped(v);hidden_lines,_=grouped(h)
        # A render hash binds the original page reference; no page is changed.
        pm=p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
        page_png=pm.tobytes("png")
        (out/"render").mkdir(exist_ok=True);(out/"render"/f"page_{j:02d}.png").write_bytes(page_png)
        raw=p.get_text("text",sort=True)
        rec={"page":j,"rect":[*p.rect],"render_sha256":sha(page_png),"raw_text_chars":len(raw),
             "visible_trace_glyphs":len(v),"fully_covered_glyphs":len(h),"partially_overlapping_glyphs":len(q),
             "invisible_glyphs":len(i),"rotated_visible_glyphs":rot,
             "opaque_rect_count":len(r),"visible_line_fragments":len(lines)}
        records.append(rec)
        pages.append({"page":j,"raw_text":raw,"visible_lines":lines,"covered_lines":hidden_lines,
                      "partially_overlapping_glyph_records":q,"invisible_glyph_records":i,
                      "qualification":"Coordinate fragments; reading order, math, columns, rotated labels, nonrectangular occlusions and ambiguous glyphs require review."})
        # Logs are bounded to diagnostic counts; full text and images retained in
        # the private run artifact, not posted as new public source rows.
        print("G15_PAGE",json.dumps(rec,sort_keys=True),flush=True)
    (out/"page_recovery_ledger.json").write_text(json.dumps(pages,indent=2,ensure_ascii=False)+"\n")
    (out/"visible_fragments.txt").write_text("\n\n".join("=== PAGE "+str(x["page"])+" ===\n"+"\n".join(v["text"] for v in x["visible_lines"]) for x in pages)+"\n")
    # source inventory pinned to original checkout; the editable manuscript is older.
    files=[p for p in (ROOT/"paper").rglob("*") if p.is_file()]
    manifest={str(p.relative_to(ROOT)):{"size":p.stat().st_size,"sha256":sha(p.read_bytes())} for p in files}
    summary={"status":"SOURCE_REFERENCE_RECOVERED_NOT_NATIVE_PARITY","combined_pdf_sha256":sha(b),"combined_pdf_git_blob_sha1":git_blob(b),"pages":len(d),"page_records":records,"total_fully_covered_glyphs":sum(x["fully_covered_glyphs"] for x in records),"pages_with_fully_covered_glyphs":[x["page"] for x in records if x["fully_covered_glyphs"]],"total_partial_overlap_glyphs":sum(x["partially_overlapping_glyphs"] for x in records),"paper_source_manifest":manifest,"qualification":"No editable parity claim. Glyph occlusion screen uses fully opaque later axis-aligned rectangular fill only; remaining partial overlap, rotated text, layout, mathematical structures and nonrectangular cover require editorial adjudication. Original PDF unchanged."}
    (out/"G15_recovery_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("G15_RECOVERY",json.dumps(summary,sort_keys=True),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--out",type=Path,required=True);o=a.parse_args();main(o.out)
