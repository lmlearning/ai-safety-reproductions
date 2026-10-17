"""Render publication-only dashboards from audited, recorded metadata.

This script does not download inputs, run scientific experiments or change
classifications. Run from any directory: python tools/render_visuals.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
BG = '#f3f6fa'
WHITE = '#ffffff'
INK = '#182b42'
MUTED = '#53657a'
GRID = '#dfe6ee'
BLUE = '#3569a8'
TEAL = '#197c74'
AMBER = '#976518'
PALE = '#e0e6ed'
COLORS = {'strict': TEAL, 'near': BLUE, 'qualified': AMBER}
LABELS = {'strict': 'Strict central reproduction', 'near': 'Bounded / precision-supported near success',
          'qualified': 'Qualified near success · material exceptions'}


def configure():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 13,
        'text.color': INK, 'axes.labelcolor': MUTED, 'xtick.color': MUTED,
        'ytick.color': INK, 'axes.edgecolor': GRID, 'axes.facecolor': WHITE,
        'figure.facecolor': BG, 'savefig.facecolor': BG,
        'svg.fonttype': 'none', 'svg.hashsalt': 'ai-safety-reproductions-v1'})


def panel(fig, x, y, w, h, face=WHITE):
    box = FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.014',
                         transform=fig.transFigure,fc=face,ec=GRID,lw=0.8,zorder=-1)
    fig.add_artist(box)


def txt(fig,x,y,s,size=13,color=INK,weight='normal',va='top',**kw):
    return fig.text(x,y,s,fontsize=size,color=color,fontweight=weight,va=va,**kw)


def wrap(s,width):
    return '\n'.join(textwrap.wrap(s,width=width,break_long_words=False,break_on_hyphens=False))


def save(fig,stem):
    stem.parent.mkdir(parents=True,exist_ok=True)
    outputs=[]
    for ext in ['png','svg']:
        p=stem.with_suffix('.'+ext)
        metadata={'Software':'matplotlib; tools/render_visuals.py'} if ext=='png' else {'Date':None,'Creator':'tools/render_visuals.py'}
        fig.savefig(p,dpi=160,metadata=metadata)
        outputs.append(p)
    plt.close(fig)
    return outputs


def horizontal_counts(fig,rect,labels,values,colors,max_value):
    ax=fig.add_axes(rect)
    ys=list(range(len(values)))
    ax.barh(ys,values,color=colors,height=.44,zorder=3)
    ax.set_yticks(ys,labels,fontsize=12.8)
    ax.invert_yaxis()
    ax.set_xlim(0,max_value)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=4))
    ax.grid(axis='x',color=GRID,lw=.75,zorder=0)
    ax.tick_params(axis='both',length=0,pad=8)
    for spine in ax.spines.values():spine.set_visible(False)
    for y,v in zip(ys,values):ax.text(v+.35,y,str(v),va='center',weight='bold',fontsize=14,color=INK)
    # The dashboard already states that these are study counts. Leaving the
    # x-axis title empty gives the explanatory notes a separate baseline.
    ax.set_xlabel('')
    return ax


def programme(data):
    studies=data['studies'];n=len(studies)
    counts={k:sum(s['outcome_key']==k for s in studies) for k in COLORS}
    fig=plt.figure(figsize=(14,7.2))
    txt(fig,.045,.955,'A local reproduction programme',27,weight='bold')
    txt(fig,.047,.883,'Recorded outcomes, computational routes and selection windows',14,color=MUTED)
    tiles=[(str(n),'Central-result studies',INK),(str(counts['strict']),'Strict central',TEAL),
           (str(counts['near']),'Bounded / precision near',BLUE),
           (str(counts['qualified']),'Qualified near',AMBER),('0','Whole-paper reproductions',MUTED)]
    for i,(value,label,color) in enumerate(tiles):
        x=.045+i*.185
        panel(fig,x,.65,.17,.18)
        txt(fig,x+.014,.80,value,31,color,weight='bold')
        txt(fig,x+.014,.704,label,11.2,color=MUTED)
    panel(fig,.045,.16,.55,.43)
    panel(fig,.62,.16,.335,.43)
    txt(fig,.064,.565,'How the work was done',17,weight='bold')
    route_order=['Released-data / effect reanalysis','Fresh simulation','Original-checkpoint inference']
    vals=[sum(s['route_group']==r for s in studies) for r in route_order]
    horizontal_counts(fig,[.265,.25,.285,.245],['Released-data /\neffect reanalysis','Fresh simulation','Checkpoint inference'],vals,[BLUE,TEAL,AMBER],22)
    txt(fig,.064,.203,'P028 also fitted fresh probes to released activations.',10.8,color=MUTED)
    txt(fig,.641,.565,'Selection window',17,weight='bold')
    windows=['Main','Extended']
    vals=[sum(s['window']==r for s in studies) for r in windows]
    horizontal_counts(fig,[.755,.30,.155,.19],['Main','Extended'],vals,[BLUE,'#8595ab'],14)
    txt(fig,.641,.228,'Main: Oct 2025–Oct 2026\nExtension: Apr–Oct 2025',11,color=MUTED)
    txt(fig,.047,.10,'These are programme outcomes within declared central scopes, not grades of paper validity.',12,color=MUTED)
    txt(fig,.047,.055,'12 strict + 8 bounded / precision-supported near + 1 qualified near = 21 counted studies.',12,color=MUTED)
    return save(fig,ROOT/'visuals/programme_dashboard')


def citations(data):
    studies=sorted(data['studies'],key=lambda s:(-s['citations'],s['paper_id']))
    fig=plt.figure(figsize=(14,10.3))
    txt(fig,.045,.965,'Retained citation counts at selection',25,weight='bold')
    txt(fig,.047,.913,'Initial attention as recorded by the programme · counts have not been refreshed',13.5,color=MUTED)
    ax=fig.add_axes([.36,.16,.55,.68])
    provider_colors={'Semantic Scholar':BLUE,'OpenAlex':'#8566a5'}
    for i,s in enumerate(studies):
        color=provider_colors[s['citation_provider_group']]
        ax.hlines(i,0,s['citations'],color=color,lw=2,alpha=.45)
        ax.scatter(s['citations'],i,color=color,s=58,zorder=3)
        ax.text(s['citations']+4,i,str(s['citations']),va='center',fontsize=12,weight='bold')
    ax.set_yticks(range(len(studies)),[s['paper_id']+'  '+s['short_title'] for s in studies],fontsize=11.8)
    ax.invert_yaxis();ax.set_xlim(0,235);ax.set_ylim(len(studies)-.45,-.55)
    ax.set_xticks([0,50,100,150,200]);ax.set_xlabel('Retained citation count',fontsize=12.5,labelpad=12)
    ax.grid(axis='x',color=GRID,lw=.8);ax.tick_params(length=0,pad=8)
    for spine in ax.spines.values():spine.set_visible(False)
    for x,(provider,color) in zip([.36,.61],provider_colors.items()):
        n=sum(s['citation_provider_group']==provider for s in studies)
        fig.add_artist(plt.Line2D([x,x+.018],[.875,.875],transform=fig.transFigure,color=color,marker='o',lw=1.5))
        txt(fig,x+.026,.887,provider+' ('+str(n)+')',12,color=MUTED)
    txt(fig,.047,.082,'Providers are shown separately; their counts were not added together. Citations indicate attention, not scientific quality.',11.8,color=MUTED)
    txt(fig,.047,.043,'Exact capture times are supported for 8 studies and unknown for 13; source dates and qualifications remain in the reports.',11.8,color=MUTED)
    return save(fig,ROOT/'visuals/citation_selection')


def study_graph(s):
    fig=plt.figure(figsize=(14,6.5))
    key=s['outcome_key'];accent=COLORS[key];checks=s['original_central_checks']
    matched,total=checks['matched'],checks['total'];unmatched=total-matched
    txt(fig,.045,.95,s['paper_id']+'  /  '+s['short_title'],24,weight='bold')
    txt(fig,.047,.868,LABELS[key],15,color=accent,weight='bold')
    panel(fig,.045,.33,.57,.46)
    panel(fig,.64,.33,.315,.46)
    txt(fig,.065,.757,'Original central target checks',16,weight='bold')
    txt(fig,.065,.692,f'{matched:,} / {total:,}',27,color=BLUE,weight='bold')
    txt(fig,.065,.608,'matched within this study’s original criteria',12.5,color=MUTED)
    ax=fig.add_axes([.067,.477,.525,.065])
    ax.barh([0],[matched/total],color=BLUE,height=.8)
    if unmatched:
        ax.barh([0],[unmatched/total],left=[matched/total],color=PALE,
                edgecolor='#8996a6',hatch='////',height=.8,lw=.65)
    ax.set_xlim(0,1);ax.set_ylim(-.5,.5);ax.set_axis_off()
    txt(fig,.067,.445,f'Matched: {matched:,}',12.5,color=BLUE,weight='bold')
    txt(fig,.31,.445,f'Unmatched: {unmatched:,}',12.5,color=MUTED)
    txt(fig,.067,.392,checks['short_label'],11.6,color=MUTED)
    txt(fig,.66,.757,'Declared scope',16,weight='bold')
    for y,item in zip([.685,.535],s['scope_metrics']):
        txt(fig,.66,y,item['value'],25,color=INK,weight='bold')
        txt(fig,.66,y-.065,item['label'],12,color=MUTED)
    txt(fig,.047,.284,wrap(s['agreement_note'],144),12.8,color=INK)
    txt(fig,.047,.176,wrap(s['chart_scope_note'],152),11.6,color=MUTED)
    txt(fig,.047,.082,'Unmatched checks describe this attempt under its constraints; they do not establish that the paper is invalid.',11.8,color=MUTED)
    return save(fig,ROOT/Path(s['report']).parent/'visuals/summary')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',help='Render one paper ID, such as P041; default renders all dashboards and studies')
    args=parser.parse_args()
    configure()
    data=json.loads((ROOT/'visuals/metrics.json').read_text(encoding='utf-8'))
    assert len(data['studies'])==21
    outputs=[]
    if args.study:
        selected=[s for s in data['studies'] if s['paper_id']==args.study]
        if len(selected)!=1:parser.error('Unknown study ID')
    else:
        selected=data['studies'];outputs+=programme(data);outputs+=citations(data)
    for s in selected:
        c=s['original_central_checks']
        assert 0<=c['matched']<=c['total'] and c['total']>0
        outputs+=study_graph(s)
    receipt={'purpose':'Publication graphics from recorded outcomes; no scientific experiment executed.',
             'matplotlib_version':matplotlib.__version__,'study_graphs_rendered':len(selected),
             'files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
                       'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in outputs]}
    # Partial renders do not overwrite the complete publication graphics record.
    if not args.study:
        (ROOT/'visuals/BUILD.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'studies_rendered':len(selected),'image_files':len(outputs),'scientific_experiments_executed':False}))


if __name__=='__main__':main()
