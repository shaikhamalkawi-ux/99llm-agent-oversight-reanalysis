#!/usr/bin/env python3
"""G12: released patch bytes, source hash convention, and grade-transport audit.
No source code or test execution. Aggregate output only.
"""
import argparse, collections, hashlib, json, re, sys, subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g10'))
from run_pilot import select
from audit_test_scope_transition import load_source, REV, RUNS
C=collections.Counter
def sha(b):return hashlib.sha256(b).hexdigest()
def legacy(p):return hashlib.sha1(p.encode('utf-8')).hexdigest()[:16]
def row_flags(row):
    p=row['patch'];pid=row['patch_id'];removed=row['dependency_files_removed']
    assert isinstance(p,str) and isinstance(pid,str) and isinstance(row['resolved'],bool)
    assert removed is None or isinstance(removed,int) and removed>=0
    v={'rows':1,'grade_pass':row['resolved'],'removed_positive':bool(removed),'removed_zero':removed==0,'removed_null':removed is None,
       'id_16_lower_hex':bool(re.fullmatch('[0-9a-f]{16}',pid)),'raw_id_match':legacy(p)==pid}
    variants={'append_newline':p+'\n','remove_one_newline':p[:-1] if p.endswith('\n') else p,
              'strip_final_newlines':p.rstrip('\n'),'one_final_newline':p.rstrip('\n')+'\n',
              'crlf':p.replace('\r\n','\n').replace('\n','\r\n'),'lf':p.replace('\r\n','\n')}
    if not v['raw_id_match']:
        v['raw_id_mismatch']=1
        for k,q in variants.items():v['mismatch_'+k+'_matches']=legacy(q)==pid
        v['mismatch_any_simple_newline_variant']=any(legacy(q)==pid for q in variants.values())
    return v
def flags_into(c,v):
    c.update(v)
    for k in ('removed_positive','removed_zero','removed_null'):
        if v[k]:
            c[k+'_match']+=v['raw_id_match'];c[k+'_mismatch']+=not v['raw_id_match']
def groups_summary(groups):
    out=C()
    for vals in groups.values():
        if len(vals)<2:continue
        out['multirow_groups']+=1
        out['multirow_group_rows']+=len(vals)
        grades={v[2] for v in vals}
        out['mixed_grade_groups']+=len(grades)>1
        out['mixed_grade_group_rows']+=len(vals) if len(grades)>1 else 0
        out['different_settings_groups']+=len({v[0] for v in vals})>1
        out['different_patch_ids_groups']+=len({v[1] for v in vals})>1
        out['mixed_grade_and_different_settings_groups']+=len(grades)>1 and len({v[0] for v in vals})>1
        out['mixed_grade_and_different_ids_groups']+=len(grades)>1 and len({v[1] for v in vals})>1
    return dict(out)
def check_syntax(p):
    # --numstat parses a diff but does not apply or execute it. --recount is
    # diagnostic only; no rewriting or evaluation of an altered source patch.
    def run(*args):
        r=subprocess.run(['git','apply',*args,'--numstat','-'],input=p.encode('utf-8'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        return r.returncode==0
    return {'git_numstat_parse':run(),'git_recount_numstat_parse_diagnostic':run('--recount')}
def selftest():
    p='diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x\n+y\n'
    assert row_flags({'patch':p,'patch_id':legacy(p),'resolved':True,'dependency_files_removed':0})['raw_id_match']
    assert row_flags({'patch':p,'patch_id':legacy(p.rstrip('\n')),'resolved':False,'dependency_files_removed':0})['mismatch_any_simple_newline_variant']
    assert check_syntax(p)['git_numstat_parse']
    assert groups_summary({'x':[('a','p',True),('b','p',False)]})['mixed_grade_groups']==1
    print('G12 synthetic hash and syntax checks PASS')
def main(root):
    import pyarrow.parquet as pq
    frozen=json.loads((Path(__file__).resolve().parents[1]/'novelty_g10/G10_full_cohort_summary.json').read_text())['rows']
    target={(x['setting'],x['task_id_sha256']):x for x in frozen}
    assert len(target)==13
    allgroups=collections.defaultdict(list);idgroups=collections.defaultdict(list);finalgroups=collections.defaultdict(list)
    totals=C();finals=C();settings={};frozen_summary=C();frozen_by_stratum=collections.defaultdict(C);frozen_diagnostics=[];hashes={}
    for setting,n in RUNS.items():
        T,th=load_source(root,setting,'trajectories');P,ph=load_source(root,setting,'patches')
        D=pq.read_table(root/f'{setting}_patches.parquet',columns=['instance_id','patch_id','dependency_files_removed']).to_pylist()
        removed={(x['instance_id'],x['patch_id']):x['dependency_files_removed'] for x in D}
        assert len(P)==len(removed)==len(D)
        pm={(x['instance_id'],x['patch_id']):x for x in P}
        assert len(pm)==len(P) and len(T)==n and len({r['instance_id'] for r in T})==n
        assert set(x[0] for x in pm)<=set(r['instance_id'] for r in T)
        rcount=C();fcount=C();empty=0
        for x in P:
            key=(x['instance_id'],x['patch_id']);x['dependency_files_removed']=removed[key]
            v=row_flags(x);flags_into(rcount,v)
            h=sha(x['patch'].encode('utf-8'))
            # Same task and exact released bytes, and separately same task and
            # original reported patch ID. Cross-setting counts are descriptive.
            allgroups[(x['instance_id'],h)].append((setting,x['patch_id'],x['resolved']))
            idgroups[key].append((setting,h,x['resolved']))
        for row in T:
            iid=row['instance_id'];pid=row['final_patch_id']
            assert all((iid,p) in pm for p in row['step_patch_ids'] if p)
            if not pid:
                empty+=1;assert not row['resolved'];continue
            x=pm[(iid,pid)];assert x['resolved']==row['resolved']
            v=row_flags(x);flags_into(fcount,v)
            h=sha(x['patch'].encode('utf-8'));finalgroups[(iid,h)].append((setting,pid,x['resolved']))
            k=(setting,sha(iid.encode()))
            if k in target:
                g=target[k];assert h==g['candidate_patch_sha256']
                assert (g['source_verdict']=='pass')==row['resolved']
                z={**v,**check_syntax(x['patch'])}
                frozen_summary.update(z);frozen_by_stratum[g['source_verdict']].update(z)
                # Retain only the previously frozen rank and setting, not task identity.
                frozen_diagnostics.append({'setting':setting,'source_verdict':g['source_verdict'],'rank':g['rank'],**z})
        rcount['settings']=1;fcount['all_runs']=n;fcount['empty_final_patch_id']=empty
        totals.update(rcount);finals.update(fcount)
        settings[setting]={'patch_rows':dict(rcount),'final_runs':dict(fcount)}
        hashes[setting]={'trajectories':th,'patches':ph}
        print('G12_SETTING',setting,json.dumps(settings[setting],sort_keys=True),flush=True)
        del T,P,pm,D,removed
    assert finals['all_runs']==2400 and frozen_summary['rows']==13
    assert len(frozen_diagnostics)==13
    # Same reported ID with distinct released bytes: count it explicitly.
    id_digest_collisions=sum(len({v[1] for v in z})>1 for z in idgroups.values())
    id_mixed_grade_same_bytes=sum(len({v[2] for v in z})>1 and len({v[1] for v in z})==1 for z in idgroups.values())
    out={'source_revision':REV,'upstream_grading_code_commit':'40a5b65aabf02063cd7a940a82bdee10fdbc91e6','settings':settings,'source_hashes':hashes,
         'patch_rows':dict(totals),'final_runs':dict(finals),'same_task_same_released_bytes_patch_groups':groups_summary(allgroups),
         'same_task_same_released_bytes_final_groups':groups_summary(finalgroups),'same_task_same_reported_id_groups':groups_summary(idgroups),
         'same_task_reported_id_different_released_bytes_groups':id_digest_collisions,
         'same_task_same_id_same_released_bytes_mixed_grade_groups':id_mixed_grade_same_bytes,
         'frozen_13':dict(frozen_summary),'frozen_13_by_source_verdict':{k:dict(v) for k,v in frozen_by_stratum.items()},
         'frozen_13_diagnostics':sorted(frozen_diagnostics,key=lambda r:(r['setting'],r['source_verdict'],r['rank'])),
         'qualification':'The upstream grading script generates a 16-hex SHA1 prefix from full input patch text; dataset card does not explicitly promise this convention for every release identifier. Digest match is consistency with that convention, not proof of historical execution or full environment identity. Digest mismatch is not evidence of corrupt grading. Public release documents removing dependency files while retaining full-patch grades. Same released bytes can share a projection or differ in environment. Syntax check is nonapplying; --recount is diagnostic only. No source code or tests executed, no original rows or patch content exported.'}
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--selftest',action='store_true');p.add_argument('--root');p.add_argument('--out');o=p.parse_args()
    if o.selftest:selftest()
    if o.root:
        root=Path(o.root);root.mkdir(parents=True,exist_ok=True);z=main(root)
        Path(o.out).write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
        print('G12_AGGREGATE',json.dumps(z,sort_keys=True),flush=True)
        print('G12 SOURCE AUDIT PASS',flush=True)
