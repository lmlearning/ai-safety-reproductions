"""Five conditional SVG views of frozen facts. Stdlib only; no estimator or imports.

All input observations and computed arrays remain in COMPLETE_FACTS.json. A panel
with an undefined value is labelled undefined, rather than dropping observations.
"""
import hashlib
import html
import json
import math
from pathlib import Path

RATERS=['AI','Human-Z','Human-S']
COLORS=['#1f77b4','#2ca02c','#d62728']

def render_complete_figures(result, output_root):
    bank={x['id']:x['values']for x in result['facts']}
    root=Path(output_root)
    title='Conditional reconstruction; original producer UNESTABLISHED'
    def text(x,y,s,size=13):return f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" fill="#111">{html.escape(str(s))}</text>'
    def line(x1,y1,x2,y2,color='#555',width=1,dash=''):
        return f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>'
    def circle(x,y,color):return f'<circle cx="{x:.3f}" cy="{y:.3f}" r="2.6" fill="{color}" opacity=".6"/>'
    def rect(x,y,w,h,color,opacity=.3):return f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" stroke="{color}" fill="{color}" fill-opacity="{opacity}"/>'
    def path(points,color):
        if not points:return ''
        d='M '+' L '.join(f'{x:.3f} {y:.3f}'for x,y in points)
        return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.7"/>'
    def finite(values):return all(v is not None and math.isfinite(v)for v in values)
    def axes(x,y,w,h,xmin,xmax,ymin,ymax,xlabel,ylabel):
        assert xmax>xmin and ymax>ymin
        out=line(x,y+h,x+w,y+h)+line(x,y,x,y+h)
        X=lambda v:x+w*(v-xmin)/(xmax-xmin)
        Y=lambda v:y+h-h*(v-ymin)/(ymax-ymin)
        for j in range(6):
            vx=xmin+(xmax-xmin)*j/5;vy=ymin+(ymax-ymin)*j/5
            out+=line(X(vx),y+h,X(vx),y+h+4)+text(X(vx)-12,y+h+20,f'{vx:.3g}',11)
            out+=line(x-4,Y(vy),x,Y(vy))+text(x-53,Y(vy)+4,f'{vy:.3g}',11)
        out+=text(x+w/2-45,y+h+43,xlabel)+text(x,y-12,ylabel)
        return out,X,Y
    results=[]
    def write(number,body,w=1000,h=600):
        raw=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif">'+
             text(24,25,f'P161 Figure {number}: {title}',15)+body+'</g></svg>\n').encode('utf-8')
        assert len(raw)<=1048576
        p=root/f'CONDITIONAL_RECONSTRUCTION_FIGURE{number}.svg'
        with p.open('xb')as f:f.write(raw)
        results.append({'figure':str(number),'ref':{'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
            'publication_graphic_reproduction':'UNESTABLISHED','conditional_metadata':'API002 prospective reconstruction policy; no target-selected plotting parameters'})
    body,X,Y=axes(85,85,820,420,0,4,0,100,'Rater index 1=AI, 2=Human-Z, 3=Human-S','Total score')
    for i,(r,c)in enumerate(zip(RATERS,COLORS),1):
        v=bank[f'FIGURE1.{r}'];fields=[v[k]for k in ['q1','median','q3','whisker_low','whisker_high']]
        if not finite(fields):body+=text(120,70+25*i,r+': undefined; see full facts');continue
        x=X(i);body+=rect(x-42,Y(v['q3']),84,Y(v['q1'])-Y(v['q3']),c)
        body+=line(x-42,Y(v['median']),x+42,Y(v['median']),c,2)
        body+=line(x,Y(v['q3']),x,Y(v['whisker_high']),c)+line(x,Y(v['q1']),x,Y(v['whisker_low']),c)
        for k in ['whisker_low','whisker_high']:body+=line(x-24,Y(v[k]),x+24,Y(v[k]),c)
        body+=''.join(circle(x,Y(y),c)for y in v['outliers'])+text(x-30,550,r)
    write(1,body)
    for number in [2,3]:
        V=[bank[f'FIGURE{number}.{r}']for r in RATERS]
        values=[y for v in V for key in ['density','kde_y']for y in v[key]]
        if not finite(values):write(number,text(70,110,'Undefined histogram/KDE panel: full values and reasons retained in facts.'));continue
        ymax=max(values)*1.10 if max(values)>0 else 1
        body,X,Y=axes(85,85,820,420,0,100,0,ymax,'Total score','Density')
        for r,c,v in zip(RATERS,COLORS,V):
            for lo,hi,d in zip(v['bin_edges'][:-1],v['bin_edges'][1:],v['density']):
                body+=rect(X(lo),Y(d),X(hi)-X(lo),Y(0)-Y(d),c,.12)
            body+=path([(X(x),Y(y))for x,y in zip(v['kde_x'],v['kde_y'])],c)
        body+=text(90,565,'All91 totals per rater; bins0..100 step5; Gaussian Scott bandwidth; grid401points. These settings are conditional.')
        for i,(r,c)in enumerate(zip(RATERS,COLORS)):body+=rect(100+240*i,40,15,15,c,1)+text(122+240*i,53,r)
        write(number,body)
    body=''
    for i,pair in enumerate(['AI_HumanZ','AI_HumanS']):
        v=bank[f'BA.{pair}'];values=v['x']+v['y']+v['fitted']+[v['mean_bias'],v['loa_low'],v['loa_high']]
        if not finite(values):body+=text(60+490*i,110,pair+': undefined full panel');continue
        xlo=min(v['x']);xhi=max(v['x']);ylo=min(v['y']+v['fitted']+[v['loa_low']]);yhi=max(v['y']+v['fitted']+[v['loa_high']])
        dx=max((xhi-xlo)*.05,1);dy=max((yhi-ylo)*.05,1)
        b,X,Y=axes(70+490*i,105,390,390,xlo-dx,xhi+dx,ylo-dy,yhi+dy,'Pair mean','AI minus human')
        b+=text(90+490*i,66,pair)
        b+=''.join(circle(X(x),Y(y),COLORS[0])for x,y in zip(v['x'],v['y']))
        for k in ['loa_low','loa_high']:b+=line(X(xlo-dx),Y(v[k]),X(xhi+dx),Y(v[k]),'#666',1,'4 4')
        b+=line(X(xlo-dx),Y(v['mean_bias']),X(xhi+dx),Y(v['mean_bias']),'#d62728',2)
        b+=path([(X(x),Y(y))for x,y in sorted(zip(v['x'],v['fitted']))],'#1f77b4')
        b+=text(75+490*i,565,f"Bias {v['mean_bias']:.6g}, slope {v['slope']:.6g}",11);body+=b
    write(4,body)
    body,X,Y=axes(85,85,820,420,1,9,0,100,'Principal component','Percent variance')
    for i,(r,c)in enumerate(zip(RATERS,COLORS)):
        v=bank[f'PCA.{r}.correlation_listwise']['percentages']
        if not finite(v):body+=text(110,70+25*i,r+': undefined correlation/listwise PCA');continue
        body+=path([(X(j+1),Y(y))for j,y in enumerate(v)],c)
        body+=''.join(circle(X(j+1),Y(y),c)for j,y in enumerate(v))
        body+=rect(100+240*i,40,15,15,c,1)+text(122+240*i,53,r)
    body+=text(90,565,'Conditional correlation/listwise display; all18 complete PCA variant matrices/spectra remain in facts.')
    write(5,body)
    p=root/'COMPLETE_FIVE_CONDITIONAL_FIGURE_RECONSTRUCTION_MANIFEST001.json'
    raw=(json.dumps({'schema':'P161_CONDITIONAL_FIVE_FIGURE_RECONSTRUCTIONS001','figures':results,'no_original_producer_recovery_claim':True},indent=2,allow_nan=False)+'\n').encode()
    with p.open('xb')as f:f.write(raw)
    return results
