#!/usr/bin/env python3
"""Recompute source-, repository-, and session-matched visibility analyses.

This script reads the pinned public annotation file but exports only aggregate
statistics. Original labels are not reannotated or independently validated.
All resampling intervals are descriptive for the observed nonrandom corpus and
must not be read as population or causal confidence intervals.
"""
import argparse, collections, hashlib, json, random
from pathlib import Path

PIN='7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57'
REPO_SEED=993718
SESSION_SEED=993719
BOOT=3000

def point(v):
    return v['DS2'][1]/v['DS2'][0] - v['DS1'][1]/v['DS1'][0]

def quantile(z,q):
    return sorted(z)[round((len(z)-1)*q)]

def cluster_bootstrap(matched, seed):
    rng=random.Random(seed)
    reps=[]
    for _ in range(BOOT):
        sample=[matched[rng.randrange(len(matched))] for __ in range(len(matched))]
        reps.append(sum(point(v) for v in sample)/len(sample))
    return [quantile(reps,.025),quantile(reps,.975)]

def run(path):
    p=Path(path); raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PIN, 'Wrong source content: no result admitted'
    x=json.loads(raw); assert len(x)==16118

    ident=set()
    group=collections.defaultdict(lambda:[0,0,0])
    repo=collections.defaultdict(lambda:{'DS1':[0,0],'DS2':[0,0]})
    session=collections.defaultdict(lambda:{'DS1':[0,0],'DS2':[0,0],'source':None,'session_type':None})

    for r in x:
        k=(r['source'],str(r['repository_id']),str(r['session_id']),str(r['misalignment_id']))
        assert k not in ident, 'Duplicate key'; ident.add(k)
        assert r['resolution_status'] in ('RS1','RS2')
        assert (r['resolver'] in ('RV1','RV2','RV3')) == (r['resolution_status']=='RS1')
        severity=r['damage_severity']; source=r['source']
        if severity not in ('DS1','DS2'): continue
        for label in ('ALL',source):
            v=group[(label,severity)]
            v[0]+=1; v[1]+=(r['resolution_status']=='RS1'); v[2]+=(r['resolver']=='RV2')
        rv=repo[(source,str(r['repository_id']))][severity]
        rv[0]+=1; rv[1]+=(r['resolution_status']=='RS1')
        sk=(source,str(r['repository_id']),str(r['session_id']))
        sv=session[sk]
        sv['source']=source; sv['session_type']=r['session_type']
        a=sv[severity]; a[0]+=1; a[1]+=(r['resolution_status']=='RS1')

    expected={
      ('specstory','DS1'):[10861,833,751],('specstory','DS2'):[1107,255,225],
      ('swe','DS1'):[3726,341,329],('swe','DS2'):[254,75,71],
      ('ALL','DS1'):[14587,1174,1080],('ALL','DS2'):[1361,330,296]}
    assert all(group[k]==v for k,v in expected.items())

    matched_repo=[v for v in repo.values() if v['DS1'][0]>0 and v['DS2'][0]>0]
    assert len(repo)==1229 and len(matched_repo)==414
    assert sum(v['DS1'][0]+v['DS2'][0] for v in matched_repo)==12643
    repo_delta=[point(v) for v in matched_repo]
    repo_signs={'positive':sum(z>0 for z in repo_delta),'negative':sum(z<0 for z in repo_delta),'tie':sum(z==0 for z in repo_delta)}
    assert repo_signs=={'positive':163,'negative':94,'tie':157}
    repo_mean=sum(repo_delta)/len(repo_delta)
    repo_ci=cluster_bootstrap(matched_repo,REPO_SEED)
    assert abs(repo_mean-0.15867834119348542)<1e-12
    assert abs(repo_ci[0]-.12602601017277018)<1e-12 and abs(repo_ci[1]-.19285368579866724)<1e-12

    matched_session=[v for v in session.values() if v['DS1'][0]>0 and v['DS2'][0]>0]
    assert len(session)==8590 and len(matched_session)==853
    assert sum(v['DS1'][0]+v['DS2'][0] for v in matched_session)==2775
    sess_delta=[point(v) for v in matched_session]
    sess_signs={'positive':sum(z>0 for z in sess_delta),'negative':sum(z<0 for z in sess_delta),'tie':sum(z==0 for z in sess_delta)}
    assert sess_signs=={'positive':201,'negative':99,'tie':553}
    sess_mean=sum(sess_delta)/len(sess_delta)
    sess_ci=cluster_bootstrap(matched_session,SESSION_SEED)
    assert abs(sess_mean-0.13961229274828338)<1e-12
    assert abs(sess_ci[0]-0.10903394182995589)<1e-12 and abs(sess_ci[1]-0.17023949087255066)<1e-12

    session_strata={}
    for field,values in [('source',['specstory','swe']),('session_type',['IDE','CLI'])]:
        for value in values:
            ds=[point(v) for v in matched_session if v[field]==value]
            session_strata[f'{field}={value}']={'matched_sessions':len(ds),'equal_session_mean_difference':sum(ds)/len(ds)}

    matched_episode={}
    for sev in ('DS1','DS2'):
        n=sum(v[sev][0] for v in matched_session); seen=sum(v[sev][1] for v in matched_session)
        matched_episode[sev]={'episodes':n,'visibly_resolved':seen,'visibility_fraction':seen/n}

    totals={}
    for g in ('DS1','DS2'):
        n,seen,push=group[('ALL',g)]
        totals[g]={'episodes':n,'visibly_resolved':seen,'after_pushback_visible':push,
          'visibility_fraction':seen/n,'eventual_after_pushback_lower':push/n,
          'eventual_after_pushback_upper':(push+n-seen)/n,
          'after_pushback_among_visible':push/seen,'unknown_fraction':(n-seen)/n}

    lo=totals['DS2']['eventual_after_pushback_lower']-totals['DS1']['eventual_after_pushback_upper']
    hi=totals['DS2']['eventual_after_pushback_upper']-totals['DS1']['eventual_after_pushback_lower']
    r1=totals['DS1']['eventual_after_pushback_lower']; r2=totals['DS2']['eventual_after_pushback_lower']
    u1=totals['DS1']['unknown_fraction']; u2=totals['DS2']['unknown_fraction']
    frontier=[]
    for q2 in (0.0,0.25,0.50,0.75,1.0):
        q1=(r2-r1+u2*q2)/u1
        frontier.append({'ds2_unknown_eventual_rv2_rate':q2,'ds1_rate_at_zero_difference':q1})
    equal_unknown_crossing=(r2-r1)/(u1-u2)

    return {
      'source_sha256':PIN,'source_episode_count':len(x),
      'original_severity_values_used':['DS1','DS2'],'excluded_other_severity_episodes':170,
      'by_source_and_severity':{f'{a}/{b}':{'episodes':v[0],'visibly_resolved':v[1],'pushback_visible':v[2]} for (a,b),v in sorted(group.items())},
      'all_severity':totals,
      'visible_risk_difference_ds2_minus_ds1':totals['DS2']['visibility_fraction']-totals['DS1']['visibility_fraction'],
      'repository_matched':{
        'all_source_repositories':len(repo),'repositories_with_both_labels':len(matched_repo),
        'episodes_in_matched_repositories':12643,'signs':repo_signs,
        'equal_cluster_mean_visible_risk_difference':repo_mean,'resample_2p5_97p5':repo_ci,
        'bootstrap_seed':REPO_SEED,'bootstrap_replicates':BOOT},
      'session_matched':{
        'all_source_sessions_in_ds1_ds2':len(session),'sessions_with_both_labels':len(matched_session),
        'episodes_in_matched_sessions':2775,'episode_rates':matched_episode,'signs':sess_signs,
        'equal_cluster_mean_visible_risk_difference':sess_mean,'resample_2p5_97p5':sess_ci,
        'bootstrap_seed':SESSION_SEED,'bootstrap_replicates':BOOT,'strata':session_strata},
      'logical_eventual_after_pushback_diff_ds2_minus_ds1_bounds':[lo,hi],
      'missing_outcome_sensitivity':{
        'definition':'q_g is the fraction of RS2/unknown cases in severity group g that would eventually receive resolver RV2.',
        'zero_difference_frontier':frontier,
        'equal_unknown_rate_zero_difference':equal_unknown_crossing,
        'interpretation':'Under q1=q2=q only, DS2 remains higher until q exceeds the crossing. Without this assumption, the sign remains unidentified.'},
      'interpretation':'Visible resolution is observed. The DS2-DS1 visibility contrast persists within source streams, matched repositories, and matched sessions. Eventual after-pushback recovery remains unidentified without assumptions about RS2 outcomes. Original labels are not independently validated; the corpus is nonrandom; resampling intervals are descriptive only.',
      'third_party_rows_exported':0}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--annotations',required=True); ap.add_argument('--output',required=True)
    a=ap.parse_args(); result=run(a.annotations)
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('PASS: pinned source; source-stratified, repository-matched, session-matched, and missing-outcome sensitivity analyses reproduced')
