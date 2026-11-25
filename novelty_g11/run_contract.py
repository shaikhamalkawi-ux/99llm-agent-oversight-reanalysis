#!/usr/bin/env python3
"""G11: account for the two original nonpasses with reference FTP re-pass.
No replacement. Two further G10 exact patch HOLDs get check-only diagnostics.
"""
import argparse,hashlib,json,re,subprocess,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g10'))
from run_pilot import select,command,sha
from audit_test_identity import parse_diff,safe
CASES={'sphinx_a':('laguna_verified','nonpass',2),'sphinx_b':('laguna_verified','nonpass',3),
       'hold_a':('qwen3coder_verified','nonpass',0),'hold_b':('qwen3coder_verified_minisweagent','nonpass',0)}
def run(case,root):
    setting,verdict,rank=CASES[case];iid,m,candidate,testpatch,gold,sel=select(root,setting,verdict,rank)
    assert re.fullmatch(r'[a-zA-Z0-9_.-]+__[a-zA-Z0-9_.-]+',iid)
    img='swebench/sweb.eval.x86_64.'+iid.lower().replace('__','_1776_')+':latest'
    expected=json.loads((Path(__file__).resolve().parents[1]/'novelty_g10/G10_full_cohort_summary.json').read_text())
    prior=next(x for x in expected['rows'] if x['task_id_sha256']==sha(iid.encode()))
    assert sha(candidate.encode())==prior['candidate_patch_sha256']
    assert sha(testpatch.encode())==prior['reference_test_patch_sha256']
    assert sha(gold.encode())==prior['gold_patch_sha256']
    out={'case':case,'task_id_sha256':sha(iid.encode()),'selection':sel,'candidate_patch_sha256':sha(candidate.encode()),'reference_test_patch_sha256':sha(testpatch.encode()),'gold_patch_sha256':sha(gold.encode()),'ftp_count':len(m['ftp']),'ptp_count':len(m['ptp']),'cells':{}}
    gd=parse_diff(testpatch)
    if not gd or not all(safe(x) for x in gd):return dict(out,status='HOLD_TEST_PREPARATION')
    # Lock exact image digest already observed in G10. No latest substitution.
    digests=prior.get('repo_digests') or []
    if len(digests)!=1:return dict(out,status='HOLD_IMAGE_DIGEST')
    ref=digests[0]
    rc,so,se=command(['docker','pull',ref],210)
    if rc:return dict(out,status='HOLD_IMAGE_PULL',returncode=rc)
    rc,so,se=command(['docker','image','inspect','--format','{{.Id}}',ref],30)
    if rc or so.decode().strip()!=prior['image_id']:return dict(out,status='HOLD_IMAGE_ID')
    out['image_id']=prior['image_id'];out['image_digest']=ref
    with tempfile.TemporaryDirectory() as td:
        box=Path(td)
        for key,value in [('candidate.diff',candidate),('gold.diff',gold),('reference_tests.diff',testpatch)]:(box/key).write_text(value)
        (box/'meta.json').write_text(json.dumps({'base_commit':m['base_commit'],'test_paths':sorted(gd),'ftp':sorted(m['ftp']),'ptp':sorted(m['ptp'])}))
        (box/'inside.py').write_bytes((Path(__file__).resolve().parent/'reference_partition.py').read_bytes())
        box.chmod(0o755)
        for p in box.iterdir():p.chmod(0o444)
        for cell in (['candidate'] if case.startswith('hold_') else ['base','candidate','gold']):
            name='g11-'+sha((case+cell).encode())[:14]
            args=['docker','run','--rm','--name',name,'--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--memory','4g','--cpus','2','--mount','type=bind,source='+str(box)+',target=/audit,readonly','--entrypoint','/bin/bash',ref,'-lc',
                'set -e; if [ -f /opt/miniconda3/etc/profile.d/conda.sh ]; then source /opt/miniconda3/etc/profile.d/conda.sh; conda activate testbed; elif [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then source /root/miniconda3/etc/profile.d/conda.sh; conda activate testbed; elif command -v conda >/dev/null; then eval "$(conda shell.bash hook)"; conda activate testbed; fi; exec python /audit/inside.py "$1"','--',cell]
            rc,so,se=command(args,300)
            marker=[s for s in so.splitlines() if s.startswith(b'G11_CELL ')]
            try:z=json.loads(marker[0][len(b'G11_CELL '):]) if rc==0 and len(marker)==1 else None
            except ValueError:z=None
            if z is None:z={'status':'HOLD_CONTAINER_OR_TIMEOUT','returncode':rc}
            out['cells'][cell]=z
            print('G11_CELL_AGGREGATE',case,cell,json.dumps(z,sort_keys=True),flush=True)
            if rc==124:command(['docker','rm','-f',name],20)
    out['status']='CHECKED'
    c=out['cells']
    if set(c)=={'base','candidate','gold'} and all(x.get('fully_determinate') for x in c.values()):
        # Group-level control: base issue test fails, base preservation passes, gold all passes.
        control=c['base']['ftp']['fail']>0 and c['base']['ptp']['fail']==0 and c['gold']['ftp']['fail']==c['gold']['ptp']['fail']==0
        out['reference_controls_valid']=control
        out['candidate_ftp_pass']=c['candidate']['ftp']['fail']==0
        out['candidate_ptp_pass']=c['candidate']['ptp']['fail']==0
        out['ptp_only_nonpass_witness']=control and out['candidate_ftp_pass'] and not out['candidate_ptp_pass']
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=CASES,required=True);p.add_argument('--root',required=True);p.add_argument('--out',required=True);o=p.parse_args()
    root=Path(o.root);root.mkdir(parents=True,exist_ok=True);z=run(o.case,root)
    z['qualification']='Exact G10 task and image digest, named FTP and PTP union under pytest, not original harness rerun. Strict exact collection and setup/call/teardown receipts. No fuzzy application, no replacement. Historical nonpass cause remains unproven if not reproduced.'
    Path(o.out).write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print('G11_RESULT',json.dumps(z,sort_keys=True),flush=True)
