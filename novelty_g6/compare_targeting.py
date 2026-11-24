#!/usr/bin/env python3
"""G6 exact targeting comparator. No new endpoint labels; aggregates only."""
import argparse,json,sys
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_validation_scope import read_validation,STRICT
from verify_release_context import read,sk,ek,unique,SCALE,DEN,L,U,W

def sufficient(weight,target,strict):
    return weight>target if strict else weight>=target
def crossing(weights,target,strict):
    total=0
    for i,w in enumerate(sorted(weights,reverse=True),1):
        prev=total;total+=w
        if sufficient(total,target,strict):
            assert not sufficient(prev,target,strict)
            return {'count':i,'previous_units':prev,'achieved_units':total}
    return None
def guaranteed_loss_tolerance(weights,target,strict):
    remaining=sum(weights)
    assert sufficient(remaining,target,strict)
    for i,w in enumerate(sorted(weights,reverse=True),1):
        remaining-=w
        if not sufficient(remaining,target,strict):return i-1
    return len(weights)
def run(a,r,v):
    R=unique(r,ek)
    strict={sk(q) for q in v if q['label']=='INVALID' and q['invalid_category'] in STRICT}
    by=defaultdict(list)
    for q in a:
        if q['damage_severity'] in ('DS1','DS2'):by[sk(q)].append(q)
    absent=[];target=[];abs_rows=[];target_rows=[];released=0;released_n=0;matched=0
    for s,qs in by.items():
        ns=Counter(q['damage_severity'] for q in qs)
        if len(ns)!=2:continue
        matched+=1
        assert all(SCALE%n==0 for n in ns.values())
        weights=[SCALE//ns[q['damage_severity']] for q in qs if q['resolution_status']=='RS2']
        visible=[ek(q) in R for q in qs]
        assert all(visible) or not any(visible)
        if all(visible):released+=sum(weights);released_n+=len(weights)
        else:
            absent.append(sum(weights));abs_rows.extend(weights)
            if s in strict:target.append(sum(weights));target_rows.extend(weights)
    assert (matched,released,released_n,len(absent),sum(absent),len(abs_rows),len(target),sum(target),len(target_rows))==(853,1474407,936,479,2070198,1416,97,437472,271)
    k=len(target)
    random_expected=Fraction(k*sum(absent),len(absent))
    top=sum(sorted(absent,reverse=True)[:k])
    attainable=released+sum(target)
    objectives={'positive_sign_possible':(Fraction(-L-released),True),
                'half_width':(Fraction(W,2)-released,False),
                'negative_sign_possible':(Fraction(U-released),True)}
    result={}
    for name,(t,strict_) in objectives.items():
        result[name]={'additional_threshold_units':str(t),'strict':strict_,
                      'restricted_min_sessions':crossing(target,t,strict_),
                      'unrestricted_min_sessions':crossing(absent,t,strict_),
                      'restricted_min_episodes':crossing(target_rows,t,strict_),
                      'unrestricted_min_episodes':crossing(abs_rows,t,strict_),
                      'guaranteed_tolerance_to_any_wholly_unresolved_target_sessions':guaranteed_loss_tolerance(target,t,strict_),
                      'required_fraction_of_target_weight_pct':100*float(t)/sum(target)}
    return {'matched_sessions':matched,'released_unknowns':released_n,
            'released_unknown_weight_units':released,'absent_sessions':len(absent),
            'strict_target_sessions':k,'strict_target_unknowns':len(target_rows),
            'strict_target_weight_units':sum(target),'strict_target_session_share_pct':100*k/len(absent),
            'strict_target_absent_weight_share_pct':100*sum(target)/sum(absent),
            'uniform_random_same_k_expected_weight_units_exact':str(random_expected),
            'uniform_random_same_k_expected_weight_units':float(random_expected),
            'strict_over_uniform_expected_weight_ratio':float(Fraction(sum(target),1)/random_expected),
            'optimal_same_k_sessions_weight_units':top,'strict_over_optimal_same_k_weight_ratio':sum(target)/top,
            'union_weight_units':attainable,'union_unknowns':released_n+len(target_rows),
            'union_width_reduction_pct':100*attainable/W,
            'union_residual_width_pp':100*(W-attainable)/DEN,
            'union_greatest_possible_lower_pp':100*(L+attainable)/DEN,
            'union_smallest_possible_upper_pp':100*(U-attainable)/DEN,
            'objectives':result,
            'qualification':'Perfect ascertainment assumed for all published unknowns plus selected additional unknowns. Different favorable completions for positive/negative. Session count not audit cost. Rejection flag is not a failure label or proof of access. Uniform comparator is exact finite-frame expectation, not a test or observed retrieval.'}
def selftest():
    assert crossing([3,2,1],5,False)['count']==2
    assert crossing([3,2,1],5,True)['count']==3
    assert crossing([3,2,1],6,True) is None
    assert guaranteed_loss_tolerance([4,3,2,1],3,True)==1
    assert guaranteed_loss_tolerance([4,3,2,1],3,False)==2
    print('G6 exact targeting synthetic PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('annotations','excerpts','validation','out'):p.add_argument('--'+n)
    p.add_argument('--selftest',action='store_true');args=p.parse_args()
    if args.selftest:selftest()
    if args.annotations:
        a,_=read(args.annotations,'annotations');r,_=read(args.excerpts,'excerpts');v,_=read_validation(args.validation)
        out=run(a,r,v)
        Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print('G6_TARGETING',json.dumps(out,sort_keys=True))
        print('G6 TARGETING SOURCE-LOCKED PASS')
