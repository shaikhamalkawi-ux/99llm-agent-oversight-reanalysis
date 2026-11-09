#!/usr/bin/env python3
"""Reproduce additional finite-corpus coverage and tie-composition counts.

Reads the exact frozen original-author annotation release; never exports rows,
repository IDs, session IDs, or original text. These are descriptive counts of
released source labels, not independent human validation or population inference.
"""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

PIN = '7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57'

def run(path):
    raw = Path(path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    assert actual == PIN, 'SOURCE SHA-256 MISMATCH; refused to compute'
    rows = json.loads(raw)
    assert len(rows) == 16118
    sessions = collections.defaultdict(lambda: {'DS1': [0, 0], 'DS2': [0, 0]})
    repositories = set()
    n_eligible = 0
    for row in rows:
        sev = row['damage_severity']
        if sev not in ('DS1', 'DS2'):
            continue
        n_eligible += 1
        key = (row['source'], str(row['repository_id']), str(row['session_id']))
        rk = key[:2]
        repositories.add(rk)
        count = sessions[key][sev]
        count[0] += 1
        count[1] += int(row['resolution_status'] == 'RS1')

    paired = {k: v for k, v in sessions.items() if v['DS1'][0] and v['DS2'][0]}
    n_episodes = sum(v[sev][0] for v in paired.values() for sev in ('DS1', 'DS2'))
    matched_repos = {k[:2] for k in paired}
    signs = collections.Counter()
    ties = collections.Counter()
    for group in paired.values():
        p1 = group['DS1'][1] / group['DS1'][0]
        p2 = group['DS2'][1] / group['DS2'][0]
        if p2 > p1:
            signs['positive'] += 1
        elif p2 < p1:
            signs['negative'] += 1
        else:
            signs['tie'] += 1
            if p1 == 0:
                ties['both_rates_zero'] += 1
            elif p1 == 1:
                ties['both_rates_one'] += 1
            else:
                ties['equal_interior_rates'] += 1

    assert n_eligible == 15948
    assert len(sessions) == 8590
    assert len(repositories) == 1229
    assert len(paired) == 853
    assert len(matched_repos) == 352
    assert n_episodes == 2775
    assert (signs['positive'], signs['negative'], signs['tie']) == (201, 99, 553)
    assert (ties['both_rates_zero'], ties['both_rates_one'], ties['equal_interior_rates']) == (528,22,3)
    return {
        'original_source_sha256': PIN,
        'original_episode_count': len(rows),
        'two_class_episode_count': n_eligible,
        'two_class_distinct_source_sessions': len(sessions),
        'two_class_distinct_source_repositories': len(repositories),
        'matched_session_count': len(paired),
        'matched_session_fraction_of_two_class_sessions': len(paired)/len(sessions),
        'matched_session_episode_count': n_episodes,
        'matched_episode_fraction_of_two_class_episodes': n_episodes/n_eligible,
        'repositories_containing_at_least_one_matched_session': len(matched_repos),
        'matched_repo_fraction_of_two_class_repositories': len(matched_repos)/len(repositories),
        'matched_session_sign_counts': {'positive':signs['positive'],'negative':signs['negative'],'tie':signs['tie']},
        'matched_session_sign_fractions': {k:signs[k]/len(paired) for k in ('positive','negative','tie')},
        'matched_session_tie_components': {k:ties[k] for k in ('both_rates_zero','both_rates_one','equal_interior_rates')},
        'fraction_of_ties_with_no_visible_resolution_in_either_class':ties['both_rates_zero']/signs['tie'],
        'adversarial_reclassification_certificate_fraction_of_visible_DS2':223/330,
        'adversarial_reclassification_certificate_fraction_of_all_two_class_records':223/n_eligible,
        'original_rows_republished':0,
        'scope': 'Descriptive, released-label selection audit. The matched subset is not assumed representative; tie and label-error analyses do not identify eventual recovery or a causal intervention effect.'
    }

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--annotations', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    result=run(args.annotations)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
    print('PASS MR26 source-locked coverage/tie audit; matched sessions:',result['matched_session_count'],
          'tie-zero:',result['matched_session_tie_components']['both_rates_zero'])
