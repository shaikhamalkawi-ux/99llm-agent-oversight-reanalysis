#!/usr/bin/env python3
"""Generate three MR31R6 result proposals from unchanged archived aggregates.

Run from any directory: python3 code/build_new_results.py
No source rows, new estimands, external data, or manuscript edits are introduced.
"""
from pathlib import Path
import hashlib
import json
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'proposed'
PREVIEW = ROOT / 'previews'
QA = ROOT / 'qa'
for d in (OUT, PREVIEW, QA):
    d.mkdir(parents=True, exist_ok=True)

DARK = '#17344B'
BLUE = '#2471A3'
TEAL = '#208574'
GRAY = '#C5CDD5'
MID = '#556878'
GRID = '#E4E9ED'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 12,
    'axes.labelsize': 11.5, 'xtick.labelsize': 10.5,
    'ytick.labelsize': 11.5, 'text.color': DARK,
    'axes.labelcolor': DARK, 'xtick.color': MID,
    'ytick.color': DARK, 'axes.edgecolor': GRAY,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.spines.left': False, 'pdf.fonttype': 42,
    'ps.fonttype': 42, 'svg.fonttype': 'none',
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
})

aggregate = json.loads((DATA / 'aggregate_results.json').read_text())
coverage = json.loads((DATA / 'matched_coverage_results.json').read_text())
assert aggregate['source_sha256'] == coverage['original_source_sha256']

audit = {
    'baseline': 'MR31R6',
    'review_proposals_only': True,
    'manuscript_changed': False,
    'source_hashes': {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest()
                      for name in ('aggregate_results.json', 'matched_coverage_results.json')},
    'figures': {},
    'layout_checks': {},
}


def text(fig, x, y, s, **kwargs):
    """All editorial and numeric annotations live outside plot areas."""
    a = fig.text(x, y, s, **kwargs)
    fig._external_texts.append(a)
    return a


def base(figsize, title, subtitle):
    fig = plt.figure(figsize=figsize)
    fig._external_texts = []
    text(fig, .06, .948, title, fontsize=18, fontweight='semibold', ha='left', va='top')
    text(fig, .06, .888, subtitle, fontsize=11.5, ha='left', va='top', color=MID)
    return fig


def decorate(ax):
    ax.set_axisbelow(True)
    ax.grid(axis='x', color=GRID, linewidth=.8)
    ax.set_yticks([])
    ax.tick_params(axis='x', length=3.2, pad=7)
    ax.tick_params(axis='y', length=0)


def save(fig, stem, axes):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    external_collisions = []
    for artist in fig._external_texts:
        bbox = artist.get_window_extent(renderer)
        for i, ax in enumerate(axes):
            if bbox.overlaps(ax.get_window_extent(renderer)):
                external_collisions.append({'text': artist.get_text(), 'plot_index': i})
    if external_collisions:
        raise AssertionError(f'{stem}: annotation intersects plot: {external_collisions}')
    # Separate labels, titles, numeric columns, and notes must not collide.
    text_collisions = []
    arts = fig._external_texts
    for i, a in enumerate(arts):
        for b in arts[i+1:]:
            if a.get_window_extent(renderer).overlaps(b.get_window_extent(renderer)):
                text_collisions.append([a.get_text(), b.get_text()])
    if text_collisions:
        raise AssertionError(f'{stem}: external labels overlap: {text_collisions}')
    audit['layout_checks'][stem] = {
        'numeric_and_editorial_labels_intersecting_plot': external_collisions,
        'external_text_overlaps': text_collisions,
        'figure_size_inches': list(fig.get_size_inches()),
        'font': 'DejaVu Sans', 'PDF_font_type': 42,
    }
    fig.savefig(OUT / f'{stem}.pdf', metadata={
        'Title': stem.replace('_', ' '),
        'Subject': 'MR31R6 figure review proposal; existing aggregate values unchanged',
        'Author': 'AI-assisted figure production',
    })
    fig.savefig(OUT / f'{stem}.svg')
    fig.savefig(PREVIEW / f'{stem}.png', dpi=230)
    plt.close(fig)


# N1: source-recorded visibility and unknown outcomes, exactly two source groups.
visibility = []
for severity in ('DS1', 'DS2'):
    source = aggregate['all_severity'][severity]
    n = source['episodes']
    visible = source['visibly_resolved']
    unknown = n - visible
    assert math.isclose(visible / n, source['visibility_fraction'], abs_tol=1e-14)
    assert math.isclose(unknown / n, source['unknown_fraction'], abs_tol=1e-14)
    visibility.append({'severity': severity, 'episodes': n, 'visible_RS1': visible,
                       'unknown_RS2': unknown, 'visible_percent': visible / n * 100,
                       'unknown_percent': unknown / n * 100,
                       'source': f'aggregate_results.json:all_severity.{severity}'})
assert [r['episodes'] for r in visibility] == [14587, 1361]
assert [r['visible_RS1'] for r in visibility] == [1174, 330]
assert [r['unknown_RS2'] for r in visibility] == [13413, 1031]
assert sum(r['episodes'] for r in visibility) == 15948

fig = base((10.4, 6.5), 'Recorded resolution and unknown final status',
           'Episode-level source labels | DS1 and DS2 together: 15,948 episodes')
fig.legend(handles=[Patch(facecolor=BLUE, label='Recorded visible resolution (RS1)'),
                    Patch(facecolor=GRAY, label='Unknown final status (RS2)')],
           loc='upper left', bbox_to_anchor=(.155, .823), ncol=2, frameon=False,
           fontsize=11.2, handlelength=1.4, columnspacing=2)
ax = fig.add_axes([.17, .477, .76, .235])
y = np.array([1., 0.])
visible = [r['visible_percent'] for r in visibility]
unknown = [r['unknown_percent'] for r in visibility]
ax.barh(y, visible, height=.42, color=BLUE)
ax.barh(y, unknown, height=.42, left=visible, color=GRAY)
ax.set(xlim=(0, 100), ylim=(-.45, 1.45), xticks=[0, 20, 40, 60, 80, 100],
       xlabel='Share of episodes within each severity group (%)')
decorate(ax)
for row, yy in zip(visibility, y):
    fy = .477 + .235 * ((yy + .45) / 1.9)
    text(fig, .06, fy + .011, row['severity'], fontsize=13.5, fontweight='semibold', va='center')
    text(fig, .06, fy - .027, f"n = {row['episodes']:,}", fontsize=10.7, color=MID, va='center')

text(fig, .06, .325, 'Original label', fontsize=11, color=MID)
text(fig, .25, .325, 'Visible RS1: count / total (%)', fontsize=11, color=MID)
text(fig, .62, .325, 'Unknown: count / total (%)', fontsize=11, color=MID)
for row, fy in zip(visibility, [.264, .203]):
    text(fig, .06, fy, row['severity'], fontsize=12.2, fontweight='semibold')
    text(fig, .25, fy, f"{row['visible_RS1']:,} / {row['episodes']:,}  ({row['visible_percent']:.2f}%)",
         fontsize=12.2, color=BLUE)
    text(fig, .62, fy, f"{row['unknown_RS2']:,} / {row['episodes']:,}  ({row['unknown_percent']:.2f}%)",
         fontsize=12.2)
text(fig, .06, .12, 'The 170 other-severity episodes in the 16,118-episode release are outside these bars.',
     fontsize=10.6, color=MID)
text(fig, .06, .077, 'Unknown status is not an observed failure. RS1 does not independently verify terminal repair.',
     fontsize=10.6, color=MID)
audit['figures']['N1_Visibility_And_Unknown'] = {
    'rows': visibility,
    'source_total': aggregate['source_episode_count'],
    'other_severity_excluded': aggregate['excluded_other_severity_episodes'],
    'caption': 'Recorded resolution visibility and unknown final status in the pinned release. Percentages use the stated episode denominators; DS1 and DS2 constitute 15,948 of the 16,118 original episodes. RS1 records a source-labelled visible resolution. Unknown final status is not an observed repair failure, and visible resolution does not independently verify terminal code correctness.'
}
save(fig, 'N1_Visibility_And_Unknown', [ax])


# N2: all session signs and conditional tie decomposition, separate denominators.
signs = coverage['matched_session_sign_counts']
ties = coverage['matched_session_tie_components']
n_sessions = coverage['matched_session_count']
n_ties = signs['tie']
assert n_sessions == 853 and sum(signs.values()) == n_sessions
assert n_ties == 553 and sum(ties.values()) == n_ties
panels = [
    {'title': '(a) All matched-session contrasts', 'denominator': n_sessions,
     'title_y': .837, 'plot_y': .567, 'head_y': .788,
     'rows': [('DS2 RS1 rate higher', signs['positive'], BLUE, 'positive'),
              ('DS1 RS1 rate higher', signs['negative'], TEAL, 'negative'),
              ('Equal recorded RS1 rates', signs['tie'], GRAY, 'tie')]},
    {'title': '(b) Composition of the tied sessions', 'denominator': n_ties,
     'title_y': .487, 'plot_y': .217, 'head_y': .438,
     'rows': [('No visible RS1\nin either class', ties['both_rates_zero'], BLUE, 'both_rates_zero'),
              ('All episodes visibly resolved\nin both classes', ties['both_rates_one'], TEAL, 'both_rates_one'),
              ('Equal intermediate\nRS1 rates', ties['equal_interior_rates'], GRAY, 'equal_interior_rates')]},
]
fig = base((10.4, 8.5), 'What the 853 matched-session contrasts contain',
           'Within-session DS2-minus-DS1 differences in source-recorded RS1 visibility')
axes = []
panel_audit = []
for panel in panels:
    text(fig, .06, panel['title_y'], panel['title'], fontsize=13, fontweight='semibold')
    text(fig, .79, panel['head_y'], f"Count / {panel['denominator']:,} (%)", fontsize=10.8, color=MID)
    a = fig.add_axes([.325, panel['plot_y'], .415, .205])
    a.barh(np.arange(3), [r[1] / panel['denominator'] * 100 for r in panel['rows']],
           color=[r[2] for r in panel['rows']], height=.50)
    a.set(xlim=(0, 100), ylim=(2.5, -.5), xticks=[0, 25, 50, 75, 100],
          xlabel=f"Share of {panel['denominator']:,} {'matched sessions' if panel['denominator']==853 else 'ties'} (%)")
    decorate(a)
    pa = []
    for i, (label, count, color, key) in enumerate(panel['rows']):
        fy = panel['plot_y'] + .205 * (1 - (i + .5) / 3)
        text(fig, .06, fy, label, fontsize=11.3, va='center', linespacing=1.25)
        text(fig, .79, fy, f"{count:,} / {panel['denominator']:,}  ({100*count/panel['denominator']:.2f}%)",
             fontsize=11.2, va='center')
        pa.append({'category': key, 'count': count, 'denominator': panel['denominator'],
                   'percent': 100 * count / panel['denominator']})
    panel_audit.append({'title': panel['title'], 'rows': pa})
    axes.append(a)
text(fig, .06, .112, 'Panel (b) uses the 553 ties as its denominator; 528/553 (95.48%) have no visible RS1 in either class.',
     fontsize=10.5, color=MID)
text(fig, .06, .073, 'Equal recorded visibility does not establish equal eventual recovery or verified terminal repair.',
     fontsize=10.5, color=MID)
audit['figures']['N2_Matched_Session_Ties'] = {
    'source': 'matched_coverage_results.json:matched_session_sign_counts and matched_session_tie_components',
    'panels': panel_audit,
    'caption': 'Distribution of recorded RS1 contrasts in the 853 original matched sessions. Panel (a) reports the sign of the within-session DS2-minus-DS1 visibility difference. Panel (b) decomposes the 553 ties, of which 528 have no recorded resolution in either class. The denominators differ between panels. A zero visibility contrast does not establish equal eventual recovery.'
}
save(fig, 'N2_Matched_Session_Ties', axes)


# N3: the four existing manuscript Table 4 checks, preferred cluster resampling.
key_primary = 'mr22_nested_repository_resampling_of_matched_sessions'
key_hc = 'mr22_high_confidence_session_matched_exploratory'
key_one = 'mr22_exactly_one_episode_per_severity_session_matched_exploratory'
specs = [
    ('Primary, equal-session weights', key_primary, 'equal_session_mean_difference',
     'repo_level_cluster_resample_equal_session_mean_2p5_97p5', False),
    ('Equal-repository weights', key_primary, 'equal_repository_mean_of_session_differences',
     'repo_level_cluster_resample_equal_repository_mean_2p5_97p5', False),
    ('Extraction confidence = high', key_hc, 'equal_session_mean_difference',
     'repo_level_cluster_resample_equal_session_mean_2p5_97p5', True),
    ('One DS1 and one DS2 per session', key_one, 'equal_session_mean_difference',
     'repo_level_cluster_resample_equal_session_mean_2p5_97p5', True),
]
checks = []
for label, key, mean_key, band_key, exploratory in specs:
    s = aggregate[key]
    checks.append({'label': label, 'sessions': s['matched_sessions'],
                   'repositories': s['matched_repositories'],
                   'mean_pp': 100*s[mean_key], 'band_pp': [100*v for v in s[band_key]],
                   'post_hoc_restricted_cohort': exploratory,
                   'source': f'aggregate_results.json:{key}',
                   'mean_key': mean_key, 'band_key': band_key,
                   'resample_replicates': s['bootstrap_replicates'],
                   'resample_seed': s['bootstrap_seed']})
assert checks[0]['sessions'] == checks[1]['sessions'] == 853
assert math.isclose(checks[0]['mean_pp'], 13.961229274828338, abs_tol=1e-12)
fig = base((10.4, 7.6), 'Recorded RS1 visibility across analysis choices',
           'Existing repository-nested checks | DS2-minus-DS1 difference in percentage points')
ax = fig.add_axes([.43, .274, .285, .485])
ys = [4.5, 3.5, 1.5, .5]
ax.axvline(0, color=MID, linewidth=1.0, linestyle='--')
for row, yy in zip(checks, ys):
    color = TEAL if row['post_hoc_restricted_cohort'] else BLUE
    ax.plot(row['band_pp'], [yy, yy], color=color, linewidth=2.2, solid_capstyle='round')
    ax.scatter([row['mean_pp']], [yy], color=color, s=52, zorder=4,
               marker='s' if row['post_hoc_restricted_cohort'] else 'o')
    ax.plot(row['band_pp'], [yy, yy], linestyle='None', marker='|', markersize=9, color=color)
ax.set(xlim=(0, 25), ylim=(0, 5), xticks=[0, 5, 10, 15, 20, 25], xlabel='Recorded RS1 difference (pp)')
decorate(ax)
text(fig, .06, .807, 'Original matched cohort', fontsize=12.5, fontweight='semibold')
text(fig, .77, .807, 'Mean [descriptive band]', fontsize=11, color=MID)
text(fig, .06, .532, 'Post-hoc restricted cohorts', fontsize=12.5, fontweight='semibold')
for row, yy in zip(checks, ys):
    fy = .274 + .485 * yy/5
    text(fig, .06, fy + .013, row['label'], fontsize=11.3,
         fontweight='semibold' if row is checks[0] else 'normal', va='center')
    text(fig, .06, fy - .023, f"{row['sessions']:,} sessions; {row['repositories']:,} repositories",
         fontsize=10.5, color=MID, va='center')
    text(fig, .77, fy + .011, f"{row['mean_pp']:+.2f} pp", fontsize=12.5, va='center',
         color=TEAL if row['post_hoc_restricted_cohort'] else BLUE)
    text(fig, .77, fy - .023, f"[{row['band_pp'][0]:+.2f}, {row['band_pp'][1]:+.2f}]",
         fontsize=11.1, va='center', color=MID)
text(fig, .06, .163, 'Bands: 2.5th-97.5th percentiles from 3,000 repository-level resamples of observed clusters.',
     fontsize=10.5, color=MID)
text(fig, .06, .122, 'These are descriptive resampling bands, not population confidence intervals.',
     fontsize=10.5, color=MID)
text(fig, .06, .081, 'Restricted cohorts do not independently validate severity labels or terminal repair.',
     fontsize=10.5, color=MID)
audit['figures']['N3_Repository_Resampling'] = {
    'rows': checks,
    'band_definition': 'Repository-cluster resampling; descriptive 2.5th-97.5th percentiles, not population confidence intervals',
    'caption': 'Recorded RS1 visibility contrast under alternative weights and restricted matched cohorts. Points are DS2-minus-DS1 differences; horizontal bands show the 2.5th-97.5th percentiles from repository-level resampling of the observed clusters. These are descriptive resampling bands, not population confidence intervals. The two restricted cohorts are post-hoc checks and do not independently validate severity labels or eventual repair.'
}
save(fig, 'N3_Repository_Resampling', [ax])

(QA / 'new_result_values.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'generated': list(audit['figures']), 'layout_checks': audit['layout_checks']}, indent=2))
