#!/usr/bin/env python3
"""G10 pilot: controlled candidate/reference test-file version crossover.
Execute public benchmark code ONLY in isolated disposable Docker containers.
"""
import argparse,collections,hashlib,json,re,sys,tempfile,subprocess,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g9'))
from audit_test_identity import read_meta,load_source,command_kind,receipt,stable,PYID,parse_diff,safe,node_parts
from audit_test_identity import REV,VREV,VREPO,VRUNS
from audit_test_scope_transition import download
C=collections.Counter
def sha(b):return hashlib.sha256(b).hexdigest()
def select(root,setting,verdict,rank):
    import pyarrow.parquet as pq
    meta,mh=read_meta(root)
    gold=pq.read_table(root/'verified_task_metadata.parquet',columns=['instance_id','patch']).to_pylist()
    gold={r['instance_id']:r['patch'] for r in gold}
    T,th=load_source(root,setting,'trajectories');P,ph=load_source(root,setting,'patches')
    pm={(x['instance_id'],x['patch_id']):x for x in P}
    assert len(pm)==len(P) and {x['instance_id'] for x in T}==set(meta)
    elig=[]
    for r in T:
        if bool(r['resolved'])!=(verdict=='pass') or not r['trajectory_complete'] or not r['trajectory'] or not r['final_patch_id']:continue
        iid=r['instance_id'];fin=r['final_patch_id'];m=meta[iid]
        steps=json.loads(r['trajectory']);ids=r['step_patch_ids'] or []
        if len(steps)!=r['stop'] or [x.get('step') for x in steps]!=list(range(1,len(steps)+1)):continue
        full=False
        for st in steps:
            kind,obs=command_kind(st)
            if receipt(kind,obs)!='pass':continue
            ok,p=stable(ids,st['step'])
            if ok and p==fin and m['ftp']<={x[1].removeprefix('./') for x in PYID.finditer(obs)}:full=True
        if not full:continue
        a=pm[iid,fin]['patch'];g=m['test_patch'];prod=gold[iid]
        assert pm[iid,fin]['resolved']==r['resolved']
        # Select on the frozen G8 conditions alone. Technical preparation is
        # evaluated AFTER selection, never by substituting a different task.
        elig.append((iid,m,a,g,prod))
    expected={'qwen3coder_verified':{'nonpass':1,'pass':0},'laguna_verified':{'nonpass':4,'pass':6},'qwen3coder_verified_minisweagent':{'nonpass':1,'pass':1}}
    assert len(elig)==expected[setting][verdict],(len(elig),expected[setting][verdict])
    assert 0<=rank<len(elig)
    iid,m,a,g,prod=sorted(elig,key=lambda x:x[0])[rank]
    return iid,m,a,g,prod,{'eligible_stratum_runs':len(elig),'selection':'fixed G8 all-FTP-name receipt cohort; deterministic rank within setting and source verdict','source_verdict':verdict,'rank':rank,'source_hashes':{'meta':mh,'trajectories':th,'patches':ph}}

def command(args,timeout):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        return p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired:
        return 124,b'',b''
def replay(setting,root,verdict,rank):
    iid,m,candidate,testpatch,gold,sel=select(root,setting,verdict,rank)
    # Only source-proven task names can construct an image reference.
    assert re.fullmatch(r'[a-zA-Z0-9_.-]+__[a-zA-Z0-9_.-]+',iid)
    img='swebench/sweb.eval.x86_64.'+iid.lower().replace('__','_1776_')+':latest'
    out={'setting':setting,'source_verdict':verdict,'rank':rank,'selection':sel,'task_id_sha256':sha(iid.encode()),'image_tag':img,'candidate_patch_sha256':sha(candidate.encode()),'reference_test_patch_sha256':sha(testpatch.encode()),'gold_patch_sha256':sha(gold.encode()),'ftp_count':len(m['ftp']),'cells':{}}
    gd=parse_diff(testpatch)
    if not gd or not all(safe(x) for x in gd) or not all(node_parts(x) is not None for x in m['ftp']) or not isinstance(candidate,str) or not candidate.strip() or not isinstance(gold,str) or not gold.strip():
        out['status']='HOLD_PREPARATION';return out
    # Non-test candidate/gold diffs are applied only inside the isolated container,
    # using git apply's default path safety and exact application checks.
    rc,so,se=command(['docker','pull',img],210)
    if rc!=0:
        out['status']='HOLD_IMAGE_PULL';out['pull_returncode']=rc
        out['pull_error_class']='timeout' if rc==124 else 'rate_limit' if b'toomanyrequests' in se.lower() or b'rate limit' in se.lower() else 'registry_or_image_error'
        return out
    rc,so,se=command(['docker','image','inspect','--format','{{json .}}',img],30)
    if rc!=0:out['status']='HOLD_IMAGE_INSPECT';return out
    image=json.loads(so);imageid=image['Id'];out['image_id']=imageid;out['repo_digests']=image.get('RepoDigests') or []
    with tempfile.TemporaryDirectory() as td:
        box=Path(td)
        (box/'candidate.diff').write_text(candidate)
        (box/'gold.diff').write_text(gold)
        (box/'reference_tests.diff').write_text(testpatch)
        (box/'meta.json').write_text(json.dumps({'base_commit':m['base_commit'],'test_paths':sorted(m['testpaths']),'nodes':sorted(m['ftp'])}))
        (box/'inside.py').write_bytes((Path(__file__).resolve().parent/'isolated_replay.py').read_bytes())
        box.chmod(0o755)
        for x in box.iterdir():x.chmod(0o444)
        for cell in ('base_local','base_reference','candidate_local','candidate_reference','gold_reference'):
            cname='g10-'+sha((setting+cell).encode())[:14]
            args=['docker','run','--rm','--name',cname,'--network','none','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','256','--memory','4g','--cpus','2','--mount','type=bind,source='+str(box)+',target=/audit,readonly','--entrypoint','/bin/bash',imageid,'-lc',
                  'set -e; if [ -f /opt/miniconda3/etc/profile.d/conda.sh ]; then source /opt/miniconda3/etc/profile.d/conda.sh; conda activate testbed; elif [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then source /root/miniconda3/etc/profile.d/conda.sh; conda activate testbed; elif command -v conda >/dev/null; then eval "$(conda shell.bash hook)"; conda activate testbed; fi; exec python /audit/inside.py "$1"','--',cell]
            rc,so,se=command(args,155)
            # No original test content or stdout is published.
            marker=[x for x in so.splitlines() if x.startswith(b'G10_CELL ')]
            try:res=json.loads(marker[-1][len(b'G10_CELL '):]) if rc==0 and len(marker)==1 else None
            except ValueError:res=None
            if res is None:res={'status':'HOLD_CONTAINER_OR_TIMEOUT','container_returncode':rc}
            out['cells'][cell]=res
            print('G10_CELL_AGGREGATE',setting,cell,json.dumps(res,sort_keys=True),flush=True)
            if rc==124:command(['docker','rm','-f',cname],20)
    c=out['cells']
    if all(v.get('status')=='EXECUTED' for v in c.values()):
        a,b=c['candidate_local'],c['candidate_reference']
        same=a['non_test_tree_digest']==b['non_test_tree_digest']
        base_same=c['base_local']['non_test_tree_digest']==c['base_reference']['non_test_tree_digest']
        out['non_test_tree_same_candidate']=same;out['non_test_tree_same_base']=base_same
        out['controlled_witness']=(same and base_same and a['pytest_verdict']=='PASS' and b['pytest_verdict']=='FAIL' and c['base_reference']['pytest_verdict']=='FAIL' and c['gold_reference']['pytest_verdict']=='PASS')
        out['status']='COMPLETED_PILOT'
    else:out['status']='PARTIAL_OR_HOLD'
    command(['docker','image','rm',imageid],45)
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--setting',required=True,choices=sorted(VRUNS));p.add_argument('--verdict',choices=['pass','nonpass'],required=True);p.add_argument('--rank',type=int,required=True);p.add_argument('--root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.root);root.mkdir(parents=True,exist_ok=True)
    z=replay(a.setting,root,a.verdict,a.rank)
    z['qualification']='Frozen G8 13-run cohort extension, no replacement, named FTP tests only. New controlled test-file intervention in official image, not a rerun of full benchmark or original historical environment. PASS/FAIL only with completed JUnit report; collection, infrastructure and timeout remain HOLD.'
    Path(a.out).write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
    print('G10_PILOT',json.dumps(z,sort_keys=True),flush=True)
