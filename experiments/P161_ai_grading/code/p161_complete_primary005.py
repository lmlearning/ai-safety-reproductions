"""P161 primary. Definitions only until explicit caller admission; no import-time science.

Original XLSX is parsed here independently. NumPy supplies this route's reductions;
the secondary route is separately authored. Published targets never select math.
"""
import hashlib
import json
import math
import re
import runpy
import zipfile
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET

RATERS = ['AI', 'Human-Z', 'Human-S']
PAIRS = {'AI_HumanZ': ('AI', 'Human-Z'), 'AI_HumanS': ('AI', 'Human-S'),
         'HumanZ_HumanS': ('Human-Z', 'Human-S')}
COLS = {'AI': (['D','E','F','G','H','I','J','K','L'], 'M'),
        'Human-Z': (['N','O','P','Q','R','S','T','U','V'], 'W'),
        'Human-S': (['X','Y','Z','AA','AB','AC','AD','AE','AF'], 'AG')}
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def pin(path):
    p=Path(path); h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}

def checked(ref):
    assert pin(ref['path']) == ref, 'Changed frozen source/input'
    return Path(ref['path'])

def save(path, value):
    b=(json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode('ascii')
    assert len(b)<=16*1024*1024
    with Path(path).open('xb') as f:f.write(b)
    return pin(path)

def parse_original(path):
    """Only literal XML and narrowly verified same-row Excel totals, no arbitrary eval."""
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        ss=ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings=[''.join(t.itertext())for t in ss.findall('m:si',NS)]
        sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    cells={c.attrib['r']:c for c in sheet.findall('m:sheetData/m:row/m:c',NS)}
    def literal(coordinate):
        c=cells.get(coordinate)
        if c is None:return None
        v=c.find('m:v',NS)
        if v is None or v.text is None:return None
        typ=c.get('t','n')
        if typ=='s':return strings[int(v.text)]
        assert typ=='n', 'Unexpected data type'
        return v.text
    masters={}
    for coordinate,c in cells.items():
        f=c.find('m:f',NS)
        if f is not None and f.get('t')=='shared' and f.text:
            assert f.get('si') not in masters
            masters[f.get('si')]=(coordinate,f.text)
    provenance=[]; rows=[]
    for row in range(3,94):
        d={'row':row,'AA':str(literal('A'+str(row))),
           'AAUni':str(literal('B'+str(row))),'University':literal('C'+str(row)),
           'criteria':{},'totals':{},'formula_audits':{}}
        for rater,(cols,totalcol) in COLS.items():
            raw=[literal(c+str(row))for c in cols]
            vals=[Decimal(v)if v is not None else None for v in raw]
            assert all(v is None or (v.is_finite()and Decimal(1)<=v<=Decimal(10))for v in vals)
            d['criteria'][rater]=[float(v)if v is not None else None for v in vals]
            coord=totalcol+str(row);c=cells[coord];f=c.find('m:f',NS)
            assert f is not None
            expanded=f.text
            if not expanded:
                assert f.get('t')=='shared'and f.get('si')in masters
                mastercoord,mastertext=masters[f.get('si')]
                dr=row-int(re.search(r'\d+',mastercoord).group())
                expanded=re.sub(r'([A-Z]+)([0-9]+)',lambda m:m[1]+str(int(m[2])+dr),mastertext)
            sumtext=f'SUM({cols[0]}{row}:{cols[-1]}{row})'
            plustext='+'.join(c+str(row)for c in cols)
            assert expanded in (sumtext,plustext), 'Unapproved formula'
            derived=sum((v if v is not None else Decimal(0)for v in vals),Decimal(0))
            cache=Decimal(literal(coord));assert cache.is_finite()
            d['totals'][rater]=float(cache)
            d['formula_audits'][rater]={'coordinate':coord,'formula_text':f.text,
              'formula_attributes':dict(f.attrib),'expanded_formula':expanded,
              'cache':float(cache),'derived':float(derived),'cache_equal':cache==derived}
            provenance.append({'row':row,'rater':rater,'criterion_coordinates':[c+str(row)for c in cols],
              'criterion_literals':raw,'cached_total_literal':str(cache)})
        rows.append(d)
    assert len(rows)==91 and len({x['AA']for x in rows})==91
    assert [sum(x['University']==c for x in rows)for c in ['UoC','AuT']]==[48,43]
    missing=[(x['row'],r,i+1)for x in rows for r in RATERS
             for i,v in enumerate(x['criteria'][r])if v is None]
    assert missing==[(44,'Human-Z',6)]
    return {'rows':rows},provenance

def run_complete_primary(cfg,numpy_module,special_module,caller_guard):
    assert all(cfg.get(k)is True for k in ['execution_authorized','ROOT_full_P161_science_authorized','ROOT_P161_current_source_review_passed'])
    assert callable(caller_guard)
    np=numpy_module;sp=special_module
    caller_guard()
    workbook=checked(cfg['workbook_ref']);api=json.loads(checked(cfg['facts_schema_ref']).read_text())
    inp,provenance=parse_original(workbook)
    rows=inp['rows'];N=len(rows);rnums=[x['row']for x in rows]
    out=Path(cfg['output_root'])/'primary001';out.mkdir(exist_ok=False)
    save(out/'ORIGINAL_XML_LITERAL_PROVENANCE_PRIMARY001.json',provenance)
    save(out/'COMPLETE_RAW_INPUT_AND_FORMULA_AUDITS_PRIMARY001.json',inp)
    arrays={r:np.array([x['criteria'][r]for x in rows],dtype=np.float64)for r in RATERS}
    totals={r:np.array([x['totals'][r]for x in rows],dtype=np.float64)for r in RATERS}
    facts={}
    kappa_raw_lineage={}
    def emit(id,values,reason='Undefined for insufficient observations, zero variance or zero denominator'):
        undefined=[]
        def clean(x,path):
            if isinstance(x,np.ndarray):x=x.tolist()
            if isinstance(x,np.generic):x=x.item()
            if isinstance(x,dict):return {k:clean(v,path+[k])for k,v in x.items()}
            if isinstance(x,(list,tuple)):return [clean(v,path+[i])for i,v in enumerate(x)]
            if x is None or (isinstance(x,float)and not math.isfinite(x)):
                undefined.append({'path':path,'reason':reason});return None
            assert isinstance(x,(int,float,bool,str)),type(x)
            return x
        assert id not in facts
        facts[id]={'id':id,'values':clean(values,[]),'undefined':undefined}
    def t_p(t,df):
        return float(2*sp.stdtr(df,-abs(t)))if t is not None and df>0 else None
    def ratio(a,b):return float(a/b)if b!=0 else None
    def endpoint(r,ep):return totals[r]if ep=='Total'else arrays[r][:,int(ep)-1]
    def pair_vectors(pair,ep,common=False):
        a,b=PAIRS[pair];x=endpoint(a,ep);y=endpoint(b,ep)
        keep=np.isfinite(x)&np.isfinite(y)
        if common:
            for r in RATERS:keep &= np.isfinite(endpoint(r,ep))
        return x[keep],y[keep],[rnums[i]for i in np.flatnonzero(keep)]
    def correlation(x,y):
        xc=x-np.mean(x);yc=y-np.mean(y)
        r=ratio(np.dot(xc,yc),np.sqrt(np.dot(xc,xc)*np.dot(yc,yc)))
        if r is not None:r=max(-1.0,min(1.0,r))
        if r is None:p=None
        elif abs(r)==1:p=0.0
        else:p=t_p(r*np.sqrt((len(x)-2)/(1-r*r)),len(x)-2)
        return r,p
    def ranks(x):
        ix=np.argsort(x,kind='stable');out=np.empty(len(x),dtype=np.float64);i=0
        while i<len(ix):
            j=i+1
            while j<len(ix)and x[ix[j]]==x[ix[i]]:j+=1
            out[ix[i:j]]=(i+j+1)/2;i=j
        return out
    def desc(x):
        n=len(x);mu=np.mean(x);z=x-mu;m2=np.mean(z*z);m3=np.mean(z**3);m4=np.mean(z**4)
        g1=ratio(m3,m2**1.5);g2=ratio(m4,m2*m2)
        return {'n':n,'mean':float(mu),'sd':float(np.std(x,ddof=1)),
          'minimum':float(np.min(x)),'maximum':float(np.max(x)),
          'skewness':float(np.sqrt(n*(n-1))/(n-2)*g1)if g1 is not None and n>2 else None,
          'kurtosis':float((n-1)/((n-2)*(n-3))*((n+1)*(g2-3)+6))if g2 is not None and n>3 else None,
          'raw_skewness':g1,'raw_excess_kurtosis':g2-3 if g2 is not None else None}
    for scope in ['All','UoC','AuT']:
        keep=np.array([scope=='All'or x['University']==scope for x in rows])
        for r in RATERS:emit(f'DESC.{scope}.{r}',desc(totals[r][keep]))
    for ep in [str(i)for i in range(1,10)]+['Total']:
        for pair in PAIRS:
            caller_guard();x,y,case=pair_vectors(pair,ep);n=len(x)
            pr,pp=correlation(x,y);xr=ranks(x);yr=ranks(y);sr,spp=correlation(xr,yr)
            emit(f'CORR.{ep}.{pair}',{'n':n,'case_rows':case,'pearson_r':pr,'pearson_p':pp,
              'spearman_rho':sr,'spearman_p':spp,'x_ranks':xr,'y_ranks':yr})
            diff=x-y;md=float(np.mean(diff));sd=float(np.std(diff,ddof=1));tt=ratio(md,sd/np.sqrt(n))
            pv=t_p(tt,n-1)
            emit(f'PAIRED.{ep}.{pair}',{'n':n,'case_rows':case,'mean_difference':md,
              'sd_difference':sd,'t':tt,'df':n-1,'p':pv,'bonferroni_p':min(1,3*pv)if pv is not None else None,'d':ratio(md,sd)})
            for mask in ['common3','pairwise']:
                x,y,case=pair_vectors(pair,ep,mask=='common3');n=len(x);A=np.column_stack([x,y]);k=2
                grand=np.mean(A);rm=np.mean(A,axis=1);cm=np.mean(A,axis=0)
                msr=float(k*np.sum((rm-grand)**2)/(n-1));msc=float(n*np.sum((cm-grand)**2)/(k-1))
                mse=float(np.sum((A-rm[:,None]-cm[None,:]+grand)**2)/((n-1)*(k-1)))
                emit(f'ICC.{mask}.{ep}.{pair}',{'n':n,'case_rows':case,'MSR':msr,'MSC':msc,'MSE':mse,
                  'single':ratio(msr-mse,msr+(k-1)*mse+k*(msc-mse)/n),
                  'average':ratio(msr-mse,msr+(msc-mse)/n)})
    def covariance(A,mode):
        original=A;keep=np.all(np.isfinite(A),axis=1)
        if mode=='listwise':
            A=A[keep];case=[rnums[i]for i in np.flatnonzero(keep)]
        else:
            case=list(rnums)
            if mode=='mean_substitution':
                A=A.copy()
                for j in range(9):
                    ok=np.isfinite(A[:,j]);A[~ok,j]=np.mean(A[ok,j])if np.any(ok)else np.nan
        C=np.full((9,9),np.nan);counts=np.zeros((9,9),dtype=np.int64)
        for i in range(9):
            for j in range(9):
                ok=np.isfinite(A[:,i])&np.isfinite(A[:,j]);n=int(np.sum(ok));counts[i,j]=n
                if n>1:C[i,j]=np.dot(A[ok,i]-np.mean(A[ok,i]),A[ok,j]-np.mean(A[ok,j]))/(n-1)
        return C,counts,case
    for r in RATERS:
        for mode in ['listwise','pairwise','mean_substitution']:
            caller_guard();C,counts,case=covariance(arrays[r],mode);diag=np.diag(C)
            # Each pairwise correlation uses the same complete pair for
            # covariance AND both variances, not full-column marginal SDs.
            # Nonpairwise zero-variance entries remain explicitly undefined;
            # other matrix entries are retained, with no column pruning.
            denominator=np.sqrt(diag[:,None]*diag[None,:])
            R=np.full((9,9),np.nan)
            np.divide(C,denominator,out=R,where=np.isfinite(denominator)&(denominator>0))
            if mode=='pairwise':
                A=arrays[r]
                for i in range(9):
                    for j in range(9):
                        keep=np.isfinite(A[:,i])&np.isfinite(A[:,j])
                        if int(np.sum(keep))<2:continue
                        xi=A[keep,i]-np.mean(A[keep,i]);yj=A[keep,j]-np.mean(A[keep,j])
                        den=np.sqrt(np.dot(xi,xi)*np.dot(yj,yj))
                        R[i,j]=np.dot(xi,yj)/den if den>0 else np.nan
            if mode!='mean_substitution':
                for standardized in [False,True]:
                    M=R if standardized else C
                    alpha=ratio(9,8)*(1-ratio(np.trace(M),np.sum(M)))if np.all(np.isfinite(M))and np.sum(M)!=0 else None
                    v=('standardized_'if standardized else'raw_')+mode
                    emit(f'ALPHA.{r}.{v}',{'case_rows':case,'pair_counts':counts,'matrix':M,'alpha':alpha})
            for name,M in [('correlation',R),('covariance',C)]:
                if np.all(np.isfinite(M)):
                    eig=np.linalg.eigvalsh(M)[::-1];pc=100*eig/np.sum(eig)if np.sum(eig)!=0 else [None]*9
                else:eig=[None]*9;pc=[None]*9
                emit(f'PCA.{r}.{name}_{mode}',{'case_rows':case,'pair_counts':counts,'matrix':M,'eigenvalues':eig,'percentages':pc},
                     'Undefined covariance/correlation/eigenproblem; no constant column or case was silently removed')
    def category(x):return np.searchsorted(np.array([50.,70.,85.]),x,side='right').astype(np.int64)
    for pair in PAIRS:
        caller_guard();x0,y0,case=pair_vectors(pair,'Total');n=len(x0);x=(x0+y0)/2;y=x0-y0
        xm=np.mean(x);ym=np.mean(y);xx=np.sum((x-xm)**2)
        slope=ratio(np.dot(x-xm,y-ym),xx);intercept=float(ym-slope*xm)if slope is not None else None
        fitted=intercept+slope*x if slope is not None else np.full(n,np.nan);res=y-fitted
        sse=np.sum(res**2);syy=np.sum((y-ym)**2);se=np.sqrt(sse/(n-2)/xx)if xx>0 and n>2 else None
        tp=ratio(slope,se)if slope is not None and se is not None else None
        sd=float(np.std(y,ddof=1))
        emit(f'BA.{pair}',{'n':n,'case_rows':case,'x':x,'y':y,'mean_bias':float(ym),'sd_difference':sd,
             'loa_low':float(ym-1.96*sd),'loa_high':float(ym+1.96*sd),'intercept':intercept,'slope':slope,
             'slope_p':t_p(tp,n-2),'r_squared':1-ratio(sse,syy)if syy!=0 else None,'fitted':fitted,'residuals':res})
        a=category(x0);b=category(y0);table=np.zeros((4,4),dtype=np.int64)
        np.add.at(table,(a,b),1)
        emit(f'BANDS.{pair}',{'n':n,'case_rows':case,'x_categories':a,'y_categories':b,'table':table,
             'exact_percent':float(100*np.mean(a==b)),'one_category_percent':float(100*np.mean(np.abs(a-b)==1)),
             'two_plus_percent':float(100*np.mean(np.abs(a-b)>=2))})
        p=table/n;rr=np.sum(p,axis=1);cc=np.sum(p,axis=0);nullp=rr[:,None]*cc[None,:]
        dist=np.abs(np.arange(4)[:,None]-np.arange(4)[None,:])/3
        for style,W in [('linear',1-dist),('quadratic',1-dist**2),('unweighted',np.eye(4))]:
            po=float(np.sum(W*p));pe=float(np.sum(W*nullp));kap=ratio(po-pe,1-pe)
            variance=v0=None
            if kap is not None:
                de=(W@cc)[:,None]+(W.T@rr)[None,:]
                grad=(W*(1-pe)+(po-1)*de)/(1-pe)**2
                variance=float((np.sum(p*grad**2)-np.sum(p*grad)**2)/n)
                g0=(W-de)/(1-pe);v0=float((np.sum(nullp*g0**2)-np.sum(nullp*g0)**2)/n)
                se=math.sqrt(max(0,variance));se0=math.sqrt(max(0,v0));z=ratio(kap,se0)
                pv=float(2*sp.ndtr(-abs(z)))if z is not None else None
            else:se=se0=pv=None
            row_counts=np.sum(table,axis=1).tolist();column_counts=np.sum(table,axis=0).tolist()
            degenerate=sum(v>0 for v in row_counts)<=1 or sum(v>0 for v in column_counts)<=1
            kappa_raw_lineage[f'KAPPA.{pair}.{style}']={'row_integer_margins':row_counts,'column_integer_margins':column_counts,
              'raw_observed_variance':variance,'raw_null_independence_variance':v0,'exact_integer_margin_degenerate':degenerate,
              'regular_normal_diagnostics_applicable':not degenerate and kap is not None}
            if degenerate:se=se0=pv=None
            emit(f'KAPPA.{pair}.{style}',{'coefficient':kap,'observed_agreement':po,'expected_agreement':pe,
              'delta_SE_diagnostic':se,'null_SE_diagnostic':se0,'normal_p_diagnostic':pv},
              'Kappa coefficient or regular normal diagnostics undefined: zero denominator or exact integer margin occupying<=1category. Raw variances retained; no forced coefficient zero. Exact source SPSS test remains unestablished')
    for group in ['AI_HumanZ','AI_HumanS','All3']:
        rs=list(PAIRS[group])if group!='All3'else RATERS
        G=[totals[r]for r in rs];ng=[len(x)for x in G];K=len(G);nt=sum(ng)
        for center in ['mean','median']:
            centers=[float(np.mean(g)if center=='mean'else np.median(g))for g in G]
            Z=[np.abs(g-c)for g,c in zip(G,centers)];zs=[np.mean(z)for z in Z]
            mu=sum(n*z for n,z in zip(ng,zs))/nt
            between=sum(n*(z-mu)**2 for n,z in zip(ng,zs));within=sum(float(np.sum((z-zm)**2))for z,zm in zip(Z,zs))
            F=ratio(between/(K-1),within/(nt-K));pv=float(sp.fdtrc(K-1,nt-K,F))if F is not None else None
            emit(f'LEVENE.{group}.{center}',{'group_sizes':ng,'centers':centers,'absolute_deviations':Z,
              'F':F,'df1':K-1,'df2':nt-K,'p':pv})
    for r in RATERS:
        caller_guard();v=totals[r];q1,med,q3=np.quantile(v,[.25,.5,.75],method='linear');iqr=q3-q1
        inside=v[(v>=q1-1.5*iqr)&(v<=q3+1.5*iqr)]
        outlier_values=v[(v<q1-1.5*iqr)|(v>q3+1.5*iqr)]
        emit(f'FIGURE1.{r}',{'values':v,'q1':float(q1),'median':float(med),'q3':float(q3),
            'whisker_low':float(np.min(inside)),'whisker_high':float(np.max(inside)),'outliers':outlier_values})
        edges=np.arange(0.,100.1,5.);counts,_=np.histogram(v,bins=edges)
        assert int(np.sum(counts))==N, 'Declared bins must preserve every input observation'
        density=counts/(N*np.diff(edges));grid=np.linspace(0.,100.,401);h=float(np.std(v,ddof=1)*N**(-1/5))
        kde=np.mean(np.exp(-.5*((grid[:,None]-v[None,:])/h)**2),axis=1)/(h*math.sqrt(2*math.pi))if h>0 else [None]*401
        for fig in ['FIGURE2','FIGURE3']:
            emit(f'{fig}.{r}',{'values':v,'bin_edges':edges,'counts':counts,'density':density,'kde_x':grid,'kde_y':kde},
                 'KDE undefined for zero sample variance; producer unknown, reconstruction only')
    expected=api['ordered_fact_queries'];ordered=[]
    assert set(facts)=={q['id']for q in expected}
    for query in expected:
        f=facts[query['id']];assert list(f['values'])==query['fields'];ordered.append(f)
    result={'schema':'P161_COMPLETE_FACTS001','route':'PRIMARY','input':inp,'facts':ordered,
            'not_run':api['declared_not_run_variants']}
    caller_guard()
    save(out/'COMPLETE_KAPPA_RAW_VARIANCE_AND_EXACT_DEGENERACY_LINEAGE_PRIMARY004.json',kappa_raw_lineage)
    ref=save(out/'COMPLETE_FACTS.json',result)
    renderer=runpy.run_path(str(checked(cfg['renderer_ref'])))
    figure_refs=renderer['render_complete_figures'](result,out)
    assert len(figure_refs)==5
    caller_guard()
    return {'result_ref':ref,'fact_count':len(ordered),'figure_refs':figure_refs,'no_whole_family_or_paper_credit_claimed':True}
