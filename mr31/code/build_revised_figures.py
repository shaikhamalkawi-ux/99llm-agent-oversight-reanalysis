#!/usr/bin/env python3
"""Regenerate three MR31R6 review figures from frozen aggregates.

No source record, manuscript, estimand or result is changed.
Run from any directory: python code/build_revised_figures.py
"""
from pathlib import Path
from fractions import Fraction
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'proposed'
PRE = ROOT / 'previews'
OUT.mkdir(exist_ok=True)
PRE.mkdir(exist_ok=True)
A = json.loads((DATA / 'aggregate_results.json').read_text())
M = json.loads((DATA / 'matched_RV2_eligibility.json').read_text())
R = json.loads((DATA / 'exact_label_sensitivity.json').read_text())
DARK, BLUE, TEAL, GRAY = '#17344B', '#2471A3', '#208574', '#C5CDD5'
MUTED, GRID = '#536674', '#E7ECF0'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11.5,
    'axes.titlesize':12,'axes.labelsize':11.5,'xtick.labelsize':10.5,
    'ytick.labelsize':11,'text.color':DARK,'axes.labelcolor':DARK,
    'xtick.color':MUTED,'ytick.color':DARK,'axes.edgecolor':MUTED,
    'axes.spines.top':False,'axes.spines.right':False,
    'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
    'savefig.facecolor':'white'})

def title(fig, heading, subtitle):
    fig.text(.065,.957,heading,fontsize=16,weight='semibold',ha='left',va='top')
    fig.text(.065,.895,subtitle,fontsize=11.1,color=MUTED,ha='left',va='top')

def clean(ax, axis='both'):
    ax.grid(axis=axis,color=GRID,lw=.75)
    ax.set_axisbelow(True)
    ax.tick_params(length=3.5,pad=6)

def line(fig,x1,y1,x2,y2,color=GRID,lw=.9,ls='-'):
    fig.add_artist(Line2D([x1,x2],[y1,y2],transform=fig.transFigure,color=color,lw=lw,ls=ls))

def save(fig,name):
    for ext in ['pdf','svg']:
        fig.savefig(OUT / f'{name}.{ext}')
    fig.savefig(PRE / f'{name}.png',dpi=240)
    plt.close(fig)

audit = {'scope':'Review proposals only; manuscript unchanged', 'figures':{}}

# Figure 1: retain original pooled frontier; all explanatory labels are outside axes.
q2=np.linspace(0,100,501)
s1,s2=A['all_severity']['DS1'],A['all_severity']['DS2']
r1,r2=Fraction(s1['after_pushback_visible'],s1['episodes']),Fraction(s2['after_pushback_visible'],s2['episodes'])
u1,u2=Fraction(s1['episodes']-s1['visibly_resolved'],s1['episodes']),Fraction(s2['episodes']-s2['visibly_resolved'],s2['episodes'])
intercept,slope=(r2-r1)/u1,u2/u1
cross=(r2-r1)/(u1-u2)
assert abs(float(cross)-A['missing_outcome_sensitivity']['equal_unknown_rate_zero_difference'])<1e-14
tie=100*float(intercept)+float(slope)*q2
fig=plt.figure(figsize=(9.8,6.3))
title(fig,'Hypothetical completion of unknown outcomes',
      'Pooled DS1/DS2 episodes (n = 15,948); q1 and q2 are scenario assumptions.')
ax=fig.add_axes([.105,.215,.49,.58])
ax.plot(q2,tie,color=BLUE,lw=2.6)
ax.plot(q2,q2,color=MUTED,lw=1.8,ls=(0,(5,3)))
ax.plot([100*float(cross)],[100*float(cross)],marker='o',ms=8,color=TEAL,mec='white',mew=1,zorder=6)
ax.set(xlim=(0,100),ylim=(0,100),xlabel='Unknown DS2 outcomes assigned RV2: q2 (%)',
       ylabel='Unknown DS1 outcomes assigned RV2: q1 (%)')
ax.set_xticks(range(0,101,20));ax.set_yticks(range(0,101,20));ax.set_aspect('equal',adjustable='box');clean(ax)
line(fig,.65,.78,.71,.78,BLUE,2.6)
fig.text(.73,.78,'Tie frontier',fontsize=12,weight='semibold',va='center')
fig.text(.65,.725,'Equal eventual RV2 shares',fontsize=10.8,color=MUTED)
line(fig,.65,.65,.71,.65,MUTED,1.8,'--')
fig.text(.73,.65,'q1 = q2 scenario',fontsize=12,weight='semibold',va='center')
fig.text(.65,.595,'Common completion share',fontsize=10.8,color=MUTED)
line(fig,.65,.55,.94,.55)
fig.text(.65,.485,f'{100*float(cross):.2f}%',fontsize=25,weight='semibold',color=TEAL)
fig.text(.65,.435,'Intersection under q1 = q2',fontsize=11)
fig.text(.65,.347,'Above: DS1 eventual RV2 share larger\nBelow: DS2 eventual RV2 share larger',
         fontsize=10.4,linespacing=1.75,color=MUTED)
line(fig,.065,.13,.95,.13)
fig.text(.065,.077,'Missing final outcomes are unobserved. This is a sensitivity scenario, not an estimated recovery rate.',fontsize=10.7)
save(fig,'F1_Completion_Frontier_Clear')
audit['figures']['F1']={'pooled_equal_completion_intersection_pct':float(cross)*100,
    'frontier_intercept':str(intercept),'frontier_slope':str(slope),
    'source':'aggregate_results.json: all_severity and missing_outcome_sensitivity',
    'annotation_policy':'All explanatory text lies outside the data axes.'}

# Figure 2: labels and counts in columns outside the bars and interval lines.
S=M['matched_session_eligibility'];V=M['RV2_partial_identification']
rows=[('Matched sessions',853,8590),('All DS1/DS2 episodes',2775,15948),
      ('DS1 episodes',1772,14587),('DS2 episodes',1003,1361)]
assert abs(853/8590-S['selected_session_fraction_decimal'])<1e-14
assert Fraction(S['DS1_fraction_in_matched_episodes'])==Fraction(1772,14587)
assert Fraction(S['DS2_fraction_in_matched_episodes'])==Fraction(1003,1361)
fig=plt.figure(figsize=(10.4,8.1))
title(fig,'Eligible support and limits on eventual outcomes',
      'The selected cohort is fixed; recorded RS1 and hypothetical eventual RV2 are distinct endpoints.')
fig.text(.065,.825,'(a) Inclusion in the 853 matched sessions',fontsize=12.4,weight='semibold')
ax=fig.add_axes([.28,.535,.35,.245])
vals=[100*n/d for _,n,d in rows];yy=np.arange(4)
ax.barh(yy,vals,color=BLUE,height=.49)
ax.set_yticks(yy,[x[0] for x in rows]);ax.invert_yaxis();ax.set_ylim(3.6,-.6)
ax.set_xlim(0,100);ax.set_xticks(range(0,101,25));ax.set_xlabel('Share of source group (%)',labelpad=8);clean(ax,'x')
fig.text(.68,.788,'Included / total',fontsize=10.7,weight='semibold')
fig.text(.94,.788,'Share',fontsize=10.7,weight='semibold',ha='right')
for y,(_,n,d),val in zip(yy,rows,vals):
    fy=fig.transFigure.inverted().transform(ax.transData.transform((0,y)))[1]
    fig.text(.68,fy,f'{n:,} / {d:,}',fontsize=11,va='center')
    fig.text(.94,fy,f'{val:.2f}%',fontsize=11,va='center',ha='right')
line(fig,.065,.44,.95,.44)
fig.text(.065,.405,'(b) Sharp logical bounds for hypothetical eventual RV2',fontsize=12.4,weight='semibold')
bounds=[A['logical_eventual_after_pushback_diff_ds2_minus_ds1_bounds'],
        [z['value'] for z in V['hypothetical_eventual_RV2_difference_sharp_bounds']]]
bx=fig.add_axes([.28,.195,.35,.15])
for i,(lo,hi) in enumerate(bounds):
    bx.plot([lo*100,hi*100],[i,i],color=BLUE,lw=4.8,solid_capstyle='butt')
    bx.plot([lo*100,hi*100],[i,i],color=BLUE,marker='|',ms=12,mew=1.7,ls='None')
bx.axvline(0,color=MUTED,lw=1,ls='--')
bx.set_yticks([0,1],['All DS1/DS2 episodes','853 matched sessions'])
bx.set_ylim(1.6,-.6);bx.set_xlim(-100,100);bx.set_xticks([-100,-50,0,50,100])
bx.set_xlabel('DS2 minus DS1 (percentage points)',labelpad=8);clean(bx,'x')
fig.text(.68,.358,'Lower bound',fontsize=10.7,weight='semibold')
fig.text(.94,.358,'Upper bound',fontsize=10.7,weight='semibold',ha='right')
for i,(lo,hi) in enumerate(bounds):
    fy=fig.transFigure.inverted().transform(bx.transData.transform((0,i)))[1]
    fig.text(.68,fy,f'{lo*100:+.2f} pp',va='center',fontsize=11)
    fig.text(.94,fy,f'{hi*100:+.2f} pp',va='center',ha='right',fontsize=11)
line(fig,.065,.105,.95,.105)
fig.text(.065,.067,'Both logical intervals cross zero: the sign of the eventual RV2 contrast remains unknown. These are not CIs.',fontsize=10.5)
fig.text(.065,.027,'Recorded RS1 contrasts are a separate result: +16.20 pp pooled and +13.96 pp with equal-session weights.',fontsize=10.5,color=MUTED)
save(fig,'F2_Eligibility_And_Bounds_Clear')
audit['figures']['F2']={'selection':[{'label':label,'numerator':n,'denominator':d,'pct':100*n/d} for label,n,d in rows],
    'bounds_pp':[[lo*100,hi*100] for lo,hi in bounds],
    'source':'matched_RV2_eligibility.json and aggregate_results.json',
    'annotation_policy':'Counts and interval endpoints are in external aligned columns.'}

# Figure S1: equal emphasis to full frontier and zoom; no in-axes text at all.
front=R['complete_exact_budget_frontier_to_first_nonpositive']
xx=[z['budget_k'] for z in front]
exact=[Fraction(z['minimum_attainable_equal_session_difference']['exact']) for z in front]
assert xx==list(range(121))
assert exact[0]==Fraction(6669,47768)
assert exact[119]==Fraction(5,47768) and exact[120]==Fraction(-51,47768)
assert all(v==Fraction(6669-56*k,47768) for k,v in enumerate(exact))
assert all(z['attains_analytic_bound'] for z in front)
yy=np.array([float(v)*100 for v in exact])
fig=plt.figure(figsize=(10.4,6.3))
title(fig,'Exact sensitivity to severity-label switches',
      'DS2 minus DS1 in 853 matched sessions; observed outcomes and session membership remain fixed.')
fig.text(.095,.812,'(a) Complete budget frontier',fontsize=12.1,weight='semibold')
fig.text(.61,.812,'(b) Enlargement near zero',fontsize=12.1,weight='semibold')
ax=fig.add_axes([.095,.365,.37,.385]);bx=fig.add_axes([.61,.365,.34,.385])
ax.plot(xx,yy,color=BLUE,lw=2.5)
ax.axhline(0,color=MUTED,lw=1.1,ls=(0,(4,3)))
ax.plot([120],[yy[120]],marker='s',ms=7,color=DARK,mec='white',mew=.8,zorder=5)
ax.set(xlim=(0,122),ylim=(-.7,14.65),ylabel='Minimum RS1 contrast (pp)',xlabel='Maximum allowed switches')
ax.set_xticks([0,20,40,60,80,100,120]);ax.set_yticks([0,3,6,9,12,15]);ax.set_ylim(-.7,14.9);clean(ax)
bx.plot(xx[115:],yy[115:],color=BLUE,lw=2.4,marker='o',ms=4)
bx.axhline(0,color=MUTED,lw=1.1,ls=(0,(4,3)))
bx.plot([119],[yy[119]],marker='o',ms=9,color=TEAL,mec='white',mew=.8,zorder=6)
bx.plot([120],[yy[120]],marker='s',ms=8.5,color=DARK,mec='white',mew=.8,zorder=6)
bx.set(xlim=(114.8,120.35),ylim=(-.16,.52),xlabel='Maximum allowed switches')
bx.set_xticks([115,116,117,118,119,120]);bx.set_yticks([-.1,0,.1,.2,.3,.4,.5]);clean(bx)
fig.text(.095,.252,'Exact minimum computed at every integer budget from 0 through 120.',fontsize=10.9,color=MUTED)
line(fig,.095,.225,.95,.225)
fig.add_artist(Line2D([.12],[.164],transform=fig.transFigure,marker='o',ms=9,color=TEAL,ls='None'))
fig.text(.145,.175,'119 switches',fontsize=12.3,weight='semibold',va='center')
fig.text(.145,.124,f'{yy[119]:+.5f} pp  |  still positive',fontsize=11.5,va='center')
fig.add_artist(Line2D([.60],[.164],transform=fig.transFigure,marker='s',ms=8.5,color=DARK,ls='None'))
fig.text(.625,.175,'120 switches',fontsize=12.3,weight='semibold',va='center')
fig.text(.625,.124,f'{yy[120]:+.5f} pp  |  first non-positive',fontsize=11.5,va='center')
fig.text(.095,.043,'Hypothetical targeted relabelling; this is not an estimated frequency of source-label errors.',fontsize=10.8,color=MUTED)
save(fig,'S1_Exact_Budget_Clear_119_120')
audit['figures']['S1']={'budgets':xx,'minimum_difference_pp':yy.tolist(),
    'all_121_match_exact_archived_rationals':True,'all_121_attain_analytic_bound':True,
    '119_exact':str(exact[119]),'120_exact':str(exact[120]),
    'source':'exact_label_sensitivity.json: complete_exact_budget_frontier_to_first_nonpositive',
    'annotation_policy':'Zero annotation text inside either plot; threshold labels in an external band.'}

(ROOT/'qa/revised_figure_values.json').write_text(json.dumps(audit,indent=2)+'\n')
print('Built F1, F2 and S1 from frozen source values; all 121 frontier points verified exactly.')
