#!/usr/bin/env python3
"""G4: hypothetical complete-repository evidence access; aggregate-only results.

Distinct from observed audit cost or licensed access. Does not verify patches.
"""
from collections import defaultdict
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import argparse, json

PIN='7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57'
SCALE=2520
W,LOWER,UPPER=3544605,-1670550,1874055

def crossing(ws, threshold, strict=False):
    total=0
    for k,w in enumerate(sorted(ws,reverse=True),1):
        total+=w
        if (total>threshold if strict else total>=threshold):
            return k,total
    return None,total

def run(path):
    b=Path(path).read_bytes()
    if sha256(b).hexdigest()!=PIN:raise ValueError('Source hash mismatch')
    rows=json.loads(b)
    if len(rows)!=16118:raise ValueError('Original source size mismatch')
    sess=defaultdict(lambda:{'DS1':[0,0],'DS2':[0,0],'lic':set()})
    for r in rows:
        g=r.get('damage_severity')
        if g not in ('DS1','DS2'):continue
        key=(str(r['source']),str(r['repository_id']),str(r['session_id']))
        z=sess[key];z['lic'].add(str(r.get('license_type')))
        z[g][0]+=1;z[g][1]+=int(r.get('resolution_status')=='RS2')
    repos=defaultdict(lambda:{'weight':0,'lic':set(),'src':set(),'nunknown':0})
    matched=episodes=n1_no=nu=0
    for key,z in sess.items():
        a,b=z['DS1'],z['DS2']
        if not (a[0] and b[0]):continue
        assert len(z['lic'])==1
        matched+=1;episodes+=a[0]+b[0]
        x=repos[key[:2]];x['lic']|=z['lic'];x['src'].add(key[0])
        for n,u in (a,b):
            assert SCALE%n==0
            x['weight']+=u*(SCALE//n)
            x['nunknown']+=u;nu+=u
            if 'NO_LICENSE' in z['lic'] and n==1:n1_no+=u
    assert (len(sess),matched,episodes,len(repos),nu,n1_no)==(8590,853,2775,352,2352,441)
    no=[];other=[];un=no_un=0;nos=set()
    for z in repos.values():
        assert len(z['lic'])==1 and len(z['src'])==1
        if 'NO_LICENSE' in z['lic']:
            no.append(z['weight']);no_un+=z['nunknown'];nos|=z['src']
        else:
            other.append(z['weight']);un+=z['nunknown']
    assert nos=={'specstory'}
    assert (len(no),len(other),no_un,un,sum(no),sum(other))==(215,137,1347,1005,1942518,1602087)
    A=sum(other)
    objectives={'positive_sign_possible':(Fraction(-LOWER-A),True),
                'half_width':(Fraction(W,2)-A,False),
                'negative_sign_possible':(Fraction(UPPER-A),True)}
    answer={}
    for name,(deficit,strict) in objectives.items():
        k,att=crossing(no,deficit,strict)
        assert k is not None
        prev=sum(sorted(no,reverse=True)[:k-1])
        assert (prev<=deficit<att) if strict else (prev<deficit<=att)
        answer[name]={'minimum_no_license_repositories':k,
            'prior_weight_units':prev,'attained_weight_units':att,
            'deficit_units':str(deficit)}
    allw=other+no
    k_half,v_half=crossing(allw,Fraction(W,2))
    k_pos,_=crossing(allw,-LOWER,True)
    k_neg,_=crossing(allw,UPPER,True)
    assert (k_pos,k_neg)==(49,63)
    return {
      'version':'99llm_G4_repository_unit_originality_candidate',
      'source_sha256':PIN,'raw_rows_and_identifiers_exported':False,
      'matched_sessions':matched,'matched_repositories':352,'unknown_statuses':nu,
      'NO_LICENSE_repositories':len(no),'other_repositories':len(other),
      'unknown_no_license':no_un,'unknown_other':un,
      'unknown_width_no_license_units':sum(no),'unknown_width_other_units':A,
      'all_NO_LICENSE_repositories_from_specstory':True,
      'whole_repository_objective_rescue_after_all_137_other_repositories':answer,
      'unrestricted_min_complete_repositories_to_halve_width':k_half,
      'unrestricted_min_complete_repositories_for_possible_positive_sign':k_pos,
      'unrestricted_min_complete_repositories_for_possible_negative_sign':k_neg,
      'half_width_attained_units':v_half,
      'qualification':'Counterfactual perfect ascertainment within selected repositories; not observed retrieval, human audit, legal entitlement, verified repair, or a new general theorem.'
    }
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--annotations',required=True)
    p.add_argument('--out')
    a=p.parse_args()
    r=run(a.annotations);s=json.dumps(r,indent=2,sort_keys=True)+'\n'
    if a.out:Path(a.out).write_text(s)
    else:print(s)
    print('G4 PINNED SOURCE REPOSITORY UNIT PASS')
