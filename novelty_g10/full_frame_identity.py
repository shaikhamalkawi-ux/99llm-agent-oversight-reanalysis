#!/usr/bin/env python3
"""G10 context: whole Verified-frame static name-identity opportunities.
No benchmark execution or source redistribution.
"""
import argparse,ast,collections,concurrent.futures,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g9'))
from audit_test_identity import read_meta,node_parts,parse_diff,base_file,apply_block,get_ast
C=collections.Counter
def classify(r):
    iid,m=r
    counts=C();unique=C();cache={};hashes=C()
    gold=parse_diff(m['test_patch'])
    per={}
    for node in sorted(m['ftp']):
        counts['identifiers']+=1
        pair=node_parts(node)
        if pair is None:
            counts['unsupported_node_syntax']+=1;continue
        path,names=pair
        k=(path,names)
        if k not in per:
            if gold is None:state='unparseable_reference_diff'
            else:
                status,raw=base_file(m,path,cache,hashes)
                if status not in ('present','absent'):state='base_fetch_unavailable'
                else:
                    st,ref=apply_block(raw,gold.get(path),path)
                    if st not in ('unchanged','applied'):state='reference_application_unavailable'
                    else:
                        ga,gb=get_ast(ref,names);ba,bb=get_ast(raw,names)
                        if ga!='found':state='reference_definition_not_found'
                        elif ba in ('file_missing','function_missing_or_ambiguous'):
                            # The helper does not distinguish a missing function from ambiguity.
                            state='base_definition_absent_or_ambiguous'
                        elif ba!='found':state='base_definition_parse_unavailable'
                        elif bb==gb:state='same_function_AST'
                        else:state='changed_function_AST'
            per[k]=state;unique[state]+=1
        counts[per[k]]+=1
        counts['parseable_identifiers']+=1
    assert sum(counts[k] for k in ('unsupported_node_syntax','unparseable_reference_diff','base_fetch_unavailable','reference_application_unavailable','reference_definition_not_found','base_definition_absent_or_ambiguous','base_definition_parse_unavailable','same_function_AST','changed_function_AST'))==counts['identifiers']
    good={'same_function_AST','changed_function_AST'}
    known=set(per.values())
    flags=C({'tasks':1})
    flags['all_identifiers_supported']+=counts['unsupported_node_syntax']==0
    flags['any_same_AST']+=bool(counts['same_function_AST'])
    flags['any_changed_AST']+=bool(counts['changed_function_AST'])
    flags['any_absent_or_ambiguous_base']+=bool(counts['base_definition_absent_or_ambiguous'])
    flags['all_identifiers_have_both_found_definitions']+=counts['same_function_AST']+counts['changed_function_AST']==counts['identifiers']
    flags['all_found_and_any_changed']+=counts['same_function_AST']+counts['changed_function_AST']==counts['identifiers'] and bool(counts['changed_function_AST'])
    flags['all_found_and_all_same']+=counts['same_function_AST']==counts['identifiers']
    flags['all_found_and_all_changed']+=counts['changed_function_AST']==counts['identifiers']
    flags['all_reference_found_and_at_least_one_base_missing_or_ambiguous']+=counts['same_function_AST']+counts['changed_function_AST']+counts['base_definition_absent_or_ambiguous']==counts['identifiers'] and bool(counts['base_definition_absent_or_ambiguous'])
    return counts,unique,flags,len(cache),len(hashes)
def main(root):
    meta,mh=read_meta(root);c=C();u=C();f=C();fetches=0;hashes=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for a,b,d,n,h in pool.map(classify,sorted(meta.items())):
            c.update(a);u.update(b);f.update(d);fetches+=n;hashes+=h
    assert f['tasks']==500
    assert f['all_found_and_any_changed']+f['all_found_and_all_same']==f['all_identifiers_have_both_found_definitions']
    out={'metadata':mh,'identifier_counts':dict(c),'distinct_task_function_counts':dict(u),'task_counts':dict(f),'base_file_fetches_within_task_cache':fetches,'present_base_file_hashes_within_task_cache':hashes,'qualification':'Static benchmark design audit over the full 500-task metadata frame. Unsupported identifiers and failed reconstruction remain unknown. Pytest parameterized IDs map to named function definitions, not necessarily the exact parameter instance; AST difference is not semantic inequivalence. Base definition absent or ambiguous is not proof of a new test. No outcomes, agent success or prevalence outside Verified are inferred.'}
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);o=p.parse_args()
    root=Path(o.root);root.mkdir(parents=True,exist_ok=True);z=main(root)
    Path(o.out).write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
    print('G10_BASELINE_IDENTITY',json.dumps(z,sort_keys=True),flush=True)
