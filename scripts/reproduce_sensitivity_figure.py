#!/usr/bin/env python3
"""Rebuild deterministic conceptual sensitivity frontier from published aggregate counts.

Figure is fully derived from published counts; no external trial outcomes imputed.
Use TrueType font embedding (PDF Type 0), never Type 3 bitmap fonts.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams
rcParams['pdf.fonttype'] = 42
rcParams['ps.fonttype'] = 42
r1,u1 = 1080/14587, 13413/14587
r2,u2 = 296/1361, 1031/1361
intercept=(r2-r1)/u1
slope=u2/u1
cross=intercept/(1-slope)
assert abs(cross-0.8856)<0.00015
x = np.linspace(0, 1, 300)
y = intercept+slope*x
fig,ax = plt.subplots(figsize=(8.2,4.8))
ax.plot(100*x,100*y,linewidth=2.3,label='Equal eventual RV2 shares (tie frontier)')
ax.plot(100*x,100*x,linestyle='--',linewidth=1.8,label='Assumed equal unknown-outcome rates')
ax.scatter([100*cross],[100*cross],s=55,zorder=6)
ax.annotate(f'Crossing: {100*cross:.2f}%', xy=(100*cross,100*cross), xytext=(48,91),arrowprops={'arrowstyle':'->','lw':0.85},fontsize=11)
ax.text(8,64,'DS1 eventual fraction higher',fontsize=11)
ax.text(40,24,'DS2 eventual fraction higher',fontsize=11)
ax.set(xlim=(0,100),ylim=(0,100),xlabel=r'DS2: RV2 among unknown cases, $q_2$ (%)',ylabel=r'DS1: RV2 among unknown cases, $q_1$ (%)')
ax.grid(True, alpha=0.19)
ax.legend(loc='lower right',fontsize=9.4,frameon=False)
fig.tight_layout()
output=Path(__file__).resolve().parent/'figures'
output.mkdir(exist_ok=True)
fig.savefig(output/'mr22_sensitivity_frontier.pdf')
fig.savefig(output/'mr22_sensitivity_frontier.png',dpi=190)
plt.close(fig)
print('PASS figure plot, crossing',cross)
