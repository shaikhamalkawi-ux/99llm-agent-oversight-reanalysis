#!/usr/bin/env python3
"""MR22 hierarchical robustness: original frozen author annotations; aggregate-only.

Adds a repository-level bootstrap over the session-matched contrast, explicitly
preserving between-session dependence within repositories. Also reports alternative
cluster weights and two transparent sensitivity subsets.  All resampling
intervals describe the observed, purposively assembled corpus; no population
sampling, causal treatment, label validation, or human coding is implied.
"""
import argparse, collections, hashlib, json, random
from pathlib import Path
from reproduce_visibility_robustness import run as mr21_run, PIN

NBOOT=3000
SEED_NEST=993720
SEED_HIGH=993721
SEED_ONEEACH=993722

def percentile_nearest(seq,p):
    z=sorted(seq)
    return z[round((len(z)-1)*p)]

def analyze_sessions(rows,seed):
    sess=collections.defaultdict(lambda: {'DS1':[0,0], 'DS2':[0,0]})
    for r in rows:
        if r['damage_severity'] not in ('DS1','DS2'):
            continue
        key=(r['source'],str(r['repository_id']),str(r['session_id']))
        stat=sess[key][r['damage_severity']]
        stat[0]+=1
        stat[1]+=int(r['resolution_status']=='RS1')
    paired={k:v for k,v in sess.items() if v['DS1'][0]>0 and v['DS2'][0]>0}
    byrepo=collections.defaultdict(list)
    for key,pair in paired.items():
        d=pair['DS2'][1]/pair['DS2'][0] - pair['DS1'][1]/pair['DS1'][0]
        byrepo[key[:2]].append(d)
    keys=sorted(byrepo)
    total_sessions=sum(map(len,byrepo.values()))
    mean_sessions=sum(map(sum,byrepo.values()))/total_sessions
    mean_repos=sum(sum(v)/len(v) for v in byrepo.values())/len(byrepo)
    rng=random.Random(seed)
    bs_sessions=[]
    bs_repos=[]
    for _ in range(NBOOT):
        sampled=[byrepo[keys[rng.randrange(len(keys))]] for __ in keys]
        bs_sessions.append(sum(map(sum,sampled))/sum(map(len,sampled)))
        bs_repos.append(sum(sum(x)/len(x) for x in sampled)/len(sampled))
    t=sum(map(sum,byrepo.values())); n=sum(map(len,byrepo.values()))
    loomeans=[(t-sum(v))/(n-len(v)) for v in byrepo.values() if n>len(v)]
    return {
       'matched_sessions':len(paired),
       'matched_repositories':len(byrepo),
       'matched_episodes':sum(v[g][0] for v in paired.values() for g in ('DS1','DS2')),
       'equal_session_mean_difference':mean_sessions,
       'repo_level_cluster_resample_equal_session_mean_2p5_97p5':[percentile_nearest(bs_sessions,.025),percentile_nearest(bs_sessions,.975)],
       'equal_repository_mean_of_session_differences':mean_repos,
       'repo_level_cluster_resample_equal_repository_mean_2p5_97p5':[percentile_nearest(bs_repos,.025),percentile_nearest(bs_repos,.975)],
       'leave_one_repository_out_equal_session_mean_range':[min(loomeans),max(loomeans)],
       'bootstrap_seed':seed,'bootstrap_replicates':NBOOT,
       'resampling_unit':'source + repository; all matched sessions in each selected repository retained',
       'estimand_definition':'Per-session DS2 minus DS1 observed RS1 rate. Equal-session mean weights each included session equally; equal-repository mean weights each included repository equally.'
    }

def relabeling_certificate(ds1_success, ds1_total, ds2_success, ds2_total):
    """Sharp observed-RS1 sign reversal under adversarial DS1<->DS2 reclassification.

    Only the original severity labels may move; RS1/RS2 remains fixed; no other
    classes are admitted. A beneficial relabeling either moves a DS2/RS1
    episode into DS1 (x) or a DS1/RS2 episode into DS2 (y). The other two
    directions always increase the positive visibility contrast until crossing.
    Exhaustively search all x+y=k for k=0,1,... with integer comparisons.
    This is an algebraic worst-case certificate, NOT estimated labeling error.
    """
    assert 0 < ds1_success < ds1_total and 0 < ds2_success < ds2_total
    assert ds2_success*ds1_total > ds1_success*ds2_total
    for k in range(ds1_total + ds2_total + 1):
        for x in range(min(k, ds2_success) + 1):
            y=k-x
            if y>ds1_total-ds1_success:
                continue
            n1=ds1_total+x-y
            n2=ds2_total-x+y
            c1=ds1_success+x
            c2=ds2_success-x
            if min(n1,n2)<=0:
                continue
            if c2*n1 <= c1*n2:  # exact integer check
                return {
                    'minimum_reclassifications':k,
                    'optimal_DS2_RS1_to_DS1_RS1':x,
                    'optimal_DS1_RS2_to_DS2_RS2':y,
                    'eligible_episode_denominator':ds1_total+ds2_total,
                    'fraction_of_eligible_episodes':k/(ds1_total+ds2_total),
                    'original_fraction_ds1':ds1_success/ds1_total,
                    'original_fraction_ds2':ds2_success/ds2_total,
                    'relabelled_fraction_ds1':c1/n1,
                    'relabelled_fraction_ds2':c2/n2,
                    'strictly_smaller_k_certified_impossible_by_exhaustive_integer_search':True,
                    'model':'Allowed DS1/DS2 severity switches only, fixed RS1/RS2; two outcome-concordant directions enumerated exhaustively. Not an empirical misclassification estimate.'
                }
    raise AssertionError('No feasible relabeling found')

def run(raw_path):
    raw=Path(raw_path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PIN, 'Source SHA-256 mismatch'
    rows=json.loads(raw)
    base=mr21_run(raw_path)
    nested=analyze_sessions(rows,SEED_NEST)
    assert nested['matched_sessions']==853
    assert nested['matched_repositories']==352
    assert nested['matched_episodes']==2775
    assert abs(nested['equal_session_mean_difference']-base['session_matched']['equal_cluster_mean_visible_risk_difference'])<1e-13
    high=analyze_sessions([x for x in rows if x['confidence']=='high'],SEED_HIGH)
    assert high['matched_sessions']==801
    # One-to-one comparison limited to sessions containing exactly one DS1 and one DS2 episode.
    all_sessions=collections.defaultdict(list)
    for r in rows:
        if r['damage_severity'] not in ('DS1','DS2'):continue
        k=(r['source'],str(r['repository_id']),str(r['session_id']))
        all_sessions[k].append(r)
    one=[]
    for arr in all_sessions.values():
        if len(arr)==2 and {z['damage_severity'] for z in arr}=={'DS1','DS2'}:
            one+=arr
    one_to_one=analyze_sessions(one,SEED_ONEEACH)
    assert one_to_one['matched_sessions']==307
    assert abs(one_to_one['equal_session_mean_difference']-0.16938110749185667)<1e-13
    # Adversarial label-error stress is separate from the uncertainty over missing terminal outcomes.
    certs = {
        'all': relabeling_certificate(1174,14587,330,1361),
        'specstory': relabeling_certificate(833,10861,255,1107),
        'swe': relabeling_certificate(341,3726,75,254),
    }
    assert [certs[g]['minimum_reclassifications'] for g in ('all','specstory','swe')]==[223,170,55]
    base['mr22_adversarial_severity_relabeling_certificates']=certs
    base['mr22_nested_repository_resampling_of_matched_sessions']=nested
    base['mr22_high_confidence_session_matched_exploratory']=high
    base['mr22_exactly_one_episode_per_severity_session_matched_exploratory']=one_to_one
    base['mr22_scope_and_cautions']={
       'original_annotations_unchanged':True,
       'author_validation_source_version':'Tang et al. arXiv:2605.29442v1 Appendix A.2 Table 5: expert 100-record axis checks; severity judge accuracy 0.64 and inter-human agreement 0.71; original-author QC, not our reannotation.',
       'label_reclassification_threshold_is_adversarial_not_calibrated':True,
       'source_sha256_verified':True,
       'third_party_episode_rows_exported':0,
       'high_confidence_and_one_to_one_subsets_are_post_hoc_robustness_checks':True,
       'multiple_exploratory_checks_not_for_confirmatory_hypothesis_tests':True,
       'nonrandom_corpus_does_not_support_population_CI':True,
       'repo_level_cluster_resampling_is_preferred_over_naive_session_resampling_for_nested_dependence':True,
       'interpretation':'Robustness of visibility association within labeled records only. No causal severity effect, external label validity, or eventual recovery estimate.'
    }
    return base

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--annotations',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    result=run(a.annotations)
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    for k in ('mr22_nested_repository_resampling_of_matched_sessions','mr22_high_confidence_session_matched_exploratory','mr22_exactly_one_episode_per_severity_session_matched_exploratory'):
        v=result[k]
        print(k, 'N_sessions=',v['matched_sessions'],'mean_pp=',round(100*v['equal_session_mean_difference'],4), 'nested_interval_pp=', [round(100*z,4) for z in v['repo_level_cluster_resample_equal_session_mean_2p5_97p5']])
    print('PASS source lock + MR21 anchors + repository-nested sensitivity + exact adversarial relabeling + aggregate-only')
