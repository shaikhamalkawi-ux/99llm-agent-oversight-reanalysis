#!/usr/bin/env python3
"""99llm G5: public excerpt release + structurally linked late context.
Only aggregate results are emitted. No source rows, identifiers or excerpts
are printed, persisted as derivative data, or redistributed.
"""
from collections import defaultdict, Counter
from pathlib import Path
from hashlib import sha1, sha256
import argparse, json, re

PIN = {
 'annotations': ('78c4eee5220a09e024de0842421e1f4b02f71e6a',13625618),
 'excerpts': ('a09707338c3a9769dc376791e05da3a8e1142686',28000053),
 'mapping': ('17b5f7bc9d82e3557a9e0b294cbbb70b5f19d119',7025082),
}
ANNO_SHA='7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57'
SCALE=2520
M=853
DEN=M*SCALE
L,U,W=-1670550,1874055,3544605
TURN=re.compile(r'^TURN ([0-9]+) \| (USER|ASSISTANT|AGENT)$')
def read(path,name):
    b=Path(path).read_bytes()
    blob=sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
    assert (blob,len(b))==PIN[name], 'Pinned original blob or size mismatch'
    digest=sha256(b).hexdigest()
    if name=='annotations':assert digest==ANNO_SHA,'Annotation SHA-256 mismatch'
    return json.loads(b),{'git_blob_sha1':blob,'sha256':digest,'bytes':len(b)}
def sk(r):return (r['source'],str(r['repository_id']),r['session_id'])
def ek(r):return sk(r)+(r['misalignment_id'],)
def mk(r):return (r['source'],str(r['repository_id']),r['session_count_id'])
def unique(rows, key):
    d={key(r):r for r in rows}
    assert len(d)==len(rows),'Duplicate key'
    return d

def features(r, quality):
    turns=set(); quotes=set(); literal_quotes=set()
    total=r['user_turns']+r['agent_turns']
    for e in r['evidence']:
        m=TURN.fullmatch(e['turn'])
        assert m and 1<=int(m[1])<=total,'Invalid indexed anchor'
        quality['all_anchor_entries']+=1
        q=e.get('quote')
        if not isinstance(q,str) or not q.strip():
            quality['blank_quote_entries']+=1;continue
        t=int(m[1]);role='USER' if m[2]=='USER' else 'NONUSER'
        turns.add(t);quotes.add((t,role,q.strip()))
        literal_quotes.add((t,m[2],q))
    assert turns,'No nonempty anchored quote'
    return {'turns':turns,'quotes':quotes,'literal_quotes':literal_quotes,
            'last':max(turns),'total':total}

def linkflags(f,siblings):
    later=[(q,g) for q,g in siblings if g['last']>f['last']]
    anchor=[(q,g) for q,g in later if f['turns']&g['turns']]
    exact=[(q,g) for q,g in anchor if f['quotes']&g['quotes']]
    literal=[(q,g) for q,g in exact if f['literal_quotes']&g['literal_quotes']]
    return {'later_any':bool(later),'later_anchor_link':bool(anchor),
      'later_exact_quote_link':bool(exact),'later_literal_quote_link':bool(literal),
      'later_exact_RS1_packet':any(q['resolution_status']=='RS1' for q,g in exact),
      'any_exact_quote_link':any(f['quotes']&g['quotes'] for q,g in siblings)}

def main(args):
    a,ah=read(args.annotations,'annotations')
    r,rh=read(args.excerpts,'excerpts')
    m,mh=read(args.mapping,'mapping')
    assert (len(a),len(r),len(m))==(16118,7760,20574)
    A,R,Mp=unique(a,ek),unique(r,ek),unique(m,mk)
    assert R.keys()<=A.keys(),'Excerpt key not found in complete annotation file'
    for k,row in R.items():
        assert all(k2 in row and row[k2]==v for k2,v in A[k].items()),'Shared field mismatch'
    for row in a:
        x=Mp[mk(row)]
        assert all(row[k]==x[k] for k in ['user_turns','agent_turns','session_sha']),'Session mapping mismatch'
    all_sessions=defaultdict(list); public_sessions=defaultdict(list); groups=defaultdict(lambda:{'DS1':[],'DS2':[]})
    for row in a:
        all_sessions[sk(row)].append(row)
        if row['damage_severity'] in ('DS1','DS2'):
            groups[sk(row)][row['damage_severity']].append(row)
    for row in r:public_sessions[sk(row)].append(row)
    release_all=Counter()
    for s,rows in all_sessions.items():
        p=sum(ek(row) in R for row in rows)
        release_all['none' if p==0 else 'all' if p==len(rows) else 'partial']+=1
    assert (release_all['all'],release_all['none'],release_all['partial'])==(4418,4212,0)
    quality=Counter(); F={ek(row):features(row,quality) for row in r}
    role_conflict=set()
    for s,rows in public_sessions.items():
        roles=defaultdict(set)
        for row in rows:
            for turn,role,_ in F[ek(row)]['quotes']:roles[turn].add(role)
        if any(len(v)>1 for v in roles.values()):role_conflict.add(s)
    results=defaultdict(Counter);strata=defaultdict(Counter)
    repositories=defaultdict(set);context=defaultdict(Counter);pairs=Counter();ses_pairs=Counter()
    status_counts=Counter();unknown_w=Counter();repo_weight=defaultdict(Counter)
    for s,z in groups.items():
        if not(z['DS1'] and z['DS2']):continue
        rows=z['DS1']+z['DS2']
        n=sum(ek(q) in R for q in rows)
        assert n in (0,len(rows)),'Partial release within matched session'
        rel='released' if n else 'absent';src=s[0]
        S=strata[(src,rel)];S['sessions']+=1;S['episodes']+=len(rows)
        repositories[(src,rel)].add(s[:2])
        status_counts['matched_sessions']+=1
        status_counts['matched_episodes']+=len(rows)
        if n:
            packets=[(q,F[ek(q)]) for q in public_sessions[s]]
            turns=set().union(*(g['turns'] for q,g in packets))
            total=F[ek(rows[0])]['total']
            assert all(g['total']==total for q,g in packets)
            ses_pairs['sessions']+=1
            any_t=any_q=False
            for x in z['DS1']:
                for y in z['DS2']:
                    f,g=F[ek(x)],F[ek(y)]
                    t=bool(f['turns']&g['turns']);q=bool(f['quotes']&g['quotes'])
                    pairs['pairs']+=1;pairs['shared_turn']+=t;pairs['shared_exact_quote']+=q
                    pairs['identical_nonempty_quote_set']+=f['quotes']==g['quotes']
                    op=x['resolution_status']!=y['resolution_status']
                    pairs['opposite_status']+=op;pairs['opposite_status_shared_exact_quote']+=op and q
                    any_t|=t;any_q|=q
            ses_pairs['shared_turn']+=any_t;ses_pairs['shared_exact_quote']+=any_q
        for sev in ('DS1','DS2'):
            ncell=len(z[sev]);assert SCALE%ncell==0
            w=SCALE//ncell
            for row in z[sev]:
                status=row['resolution_status'];assert status in ('RS1','RS2')
                key=(src,sev,status,rel);results[key]['episodes']+=1;results[key]['weight_units']+=w
                if status=='RS1':
                    S['rs1_units']+=(-w if sev=='DS1' else w)
                    if row['resolver']=='RV2':S['rv2_units']+=(-w if sev=='DS1' else w)
                else:
                    status_counts['unknown_episodes']+=1
                    S['unknown_DS1_units' if sev=='DS1' else 'unknown_DS2_units']+=w
                    unknown_w[rel]+=w;repo_weight[rel][s[:2]]+=w
                if not n:continue
                focal=F[ek(row)]
                C=context[(src,sev,status)]
                C['episodes']+=1;C['weight_units']+=w
                siblings=[(q,g) for q,g in packets if ek(q)!=ek(row)]
                flags=linkflags(focal,siblings)
                flags.update({'own_metadata_final_anchor':focal['last']==total,
                    'union_metadata_final_anchor':max(turns)==total,
                    'own_all_metadata_indices':focal['turns']==set(range(1,total+1)),
                    'union_all_metadata_indices':turns==set(range(1,total+1)),
                    'role_conflict_session':s in role_conflict})
                for name,v in flags.items():
                    C[name]+=int(v);C[name+'_weight_units']+=int(v)*w
                assert not(flags['later_exact_quote_link'] and not flags['later_anchor_link'])
                assert not(flags['later_anchor_link'] and not flags['later_any'])
    assert dict(status_counts)=={'matched_sessions':853,'matched_episodes':2775,'unknown_episodes':2352}
    assert sum(unknown_w.values())==W and unknown_w['released']==1474407
    assert sum(x['rs1_units'] for x in strata.values())==300105
    assert sum(x['rv2_units'] for x in strata.values())==251805
    assert sum(x['unknown_DS1_units'] for x in strata.values())==1922355
    assert sum(x['unknown_DS2_units'] for x in strata.values())==1622250
    c=Counter()
    for k,v in context.items():
        if k[2]=='RS2':c.update(v)
    assert (c['episodes'],c['later_any'],c['later_anchor_link'],c['later_exact_quote_link'],c['later_exact_RS1_packet'])==(936,644,144,55,18)
    assert (c['own_metadata_final_anchor'],c['union_metadata_final_anchor'],c['union_all_metadata_indices'])==(23,63,9)
    assert (pairs['pairs'],pairs['shared_turn'],pairs['shared_exact_quote'],pairs['opposite_status_shared_exact_quote'])==(871,141,46,16)
    assert c['role_conflict_session']==0
    released=unknown_w['released']
    assert L+released<0<U-released
    for k,v in strata.items():v['repositories']=len(repositories[k])
    return {'version':'99llm_G5_observed_release_and_linked_context','original_source_hashes':{'annotations':ah,'excerpts':rh,'mapping':mh},
      'source_lock':{'annotation_rows':len(a),'excerpt_rows':len(r),'session_mapping_rows':len(m),
        'shared_field_matches':len(r),'annotation_and_excerpt_keys_unique':True,
        'all_annotation_session_mappings_match':True},
      'release_session_counts':dict(release_all),'quality':dict(quality),
      'role_conflict_public_sessions':len(role_conflict),
      'fixed_matched_frame':dict(status_counts),'strata':{'/'.join(k):dict(v) for k,v in strata.items()},
      'episode_strata':{'/'.join(k):dict(v) for k,v in results.items()},
      'context_strata':{'/'.join(k):dict(v) for k,v in context.items()},
      'RS2_released_context_total':dict(c),'cross_severity_pairs':dict(pairs),
      'cross_severity_pair_sessions':dict(ses_pairs),
      'counterfactual_ceiling':{'initial_width_units':W,'released_unknown_weight_units':released,
       'absent_unknown_weight_units':W-released,'exact_denominator':DEN,
       'released_fraction_of_width_pct':100*released/W,'residual_width_pp':100*(W-released)/DEN,
       'max_possible_lower_pp':100*(L+released)/DEN,'min_possible_upper_pp':100*(U-released)/DEN,
       'all_outcome_assignments_still_span_zero':True},
      'qualification':'File membership is observed. Perfect ascertainment of released IDs is hypothetical. A quoted turn, later sibling packet, exact shared quote, or all indexed turns is not an independent verification of repair. Source labels remain unchanged.',
      'raw_records_identifiers_or_quotes_exported':False}

def selftest():
    f={'turns':{1,2},'quotes':{(1,'USER','a'),(2,'NONUSER','b')},'literal_quotes':{(1,'USER','a'),(2,'ASSISTANT','b')},'last':2}
    u={'turns':{3},'quotes':{(3,'USER','c')},'literal_quotes':{(3,'USER','c')},'last':3}
    t={'turns':{1,4},'quotes':{(1,'USER','different'),(4,'USER','d')},'literal_quotes':{(1,'USER','different'),(4,'USER','d')},'last':4}
    q={'turns':{1,5},'quotes':{(1,'USER','a'),(5,'USER','e')},'literal_quotes':{(1,'USER','a'),(5,'USER','e')},'last':5}
    x={'resolution_status':'RS1'}
    for g,want in [(u,(1,0,0)),(t,(1,1,0)),(q,(1,1,1)),(f,(0,0,0))]:
        z=linkflags(f,[(x,g)])
        assert tuple(int(z[k]) for k in ('later_any','later_anchor_link','later_exact_quote_link'))==want
    assert linkflags(f,[(x,q)])['later_exact_RS1_packet']
    assert not linkflags(f,[])['later_any']
    print('Synthetic context ladder tests PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--annotations');p.add_argument('--excerpts');p.add_argument('--mapping');p.add_argument('--out')
    p.add_argument('--selftest',action='store_true');a=p.parse_args()
    if a.selftest:selftest()
    if a.annotations:
        assert a.excerpts and a.mapping and a.out
        result=main(a)
        Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print('G5: pinned source byte checks, full-key joins, independent aggregate locks PASS')
