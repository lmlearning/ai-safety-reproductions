"""P120 original-method runner. No computations occur until main is explicitly invoked."""
from pathlib import Path
import os,sys,json,hashlib,datetime,math,itertools
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
import numpy as np
import pandas as pd
from scipy import stats
import psutil
BASE=Path(__file__).resolve().parents[1]
MODELS=['Claude','Gemini','GPT-4o','Llama']
ISSUES=['Unsafe','Includes Problematic Content','Missing Important Info','Missing History Taking','Poor Writing']
PAIRS=[('Claude','Gemini'),('Claude','Llama'),('Claude','GPT-4o'),('Gemini','Llama'),('Gemini','GPT-4o'),('Llama','GPT-4o')]
SOURCE=BASE/'sources/original_preprint_repo/SupplementaryDocuments/HealthAdviceDatasetWithEvaluations.xlsx'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2,allow_nan=False)+'\n',encoding='utf8')
def guard(stage):
    p=psutil.Process();m=p.memory_info()
    v={'stage':stage,'utc':now(),'RSS_bytes':m.rss,'peak_working_set_bytes':getattr(m,'peak_wset',None),'available_RAM_bytes':psutil.virtual_memory().available,'free_disk_bytes':psutil.disk_usage(str(BASE)).free}
    if m.rss>2**30 or v['available_RAM_bytes']<1.5*2**30 or v['free_disk_bytes']<35*2**30:raise RuntimeError('Resource guard: '+json.dumps(v))
    return v
def bonf(p):return min(1.,float(p)*6)
def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n
    center=(p+z*z/(2*n))/d
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [center-half,center+half]
def ztest(k1,n1,k2,n2):
    pooled=(k1+k2)/(n1+n2);variance=pooled*(1-pooled)*(1/n1+1/n2)
    if variance<=0:raise ValueError('Undefined original pooled z-test')
    z=(k1/n1-k2/n2)/math.sqrt(variance)
    return {'z':z,'p_raw':float(2*stats.norm.sf(abs(z))),'p_bonferroni':bonf(2*stats.norm.sf(abs(z))),'difference_percentage_points':100*(k1/n1-k2/n2)}
def check_target(t,metrics):
    value=metrics[t['metric']];kind=t['comparison'];want=t['target'];tol=t.get('absolute_tolerance')
    if kind=='absolute':passed=abs(value-want)<=tol*(1+1e-12)
    elif kind=='exact':passed=value==want
    elif kind=='exact_set':passed=sorted(value)==sorted(want)
    elif kind=='less_than':passed=value<want
    elif kind=='greater_than':passed=value>want
    elif kind=='at_least':passed=value>=want
    elif kind=='closed_interval':passed=want[0]<=value<=want[1]
    else:raise ValueError(kind)
    return dict(t,observed=value,passed=bool(passed))
def verify_inputs():
    doc=json.loads((BASE/'CODE_INPUT_RUNTIME_FREEZE004.json').read_text(encoding='utf8'))
    for f in doc['files']:
        p=Path(f['absolute_path'])
        if digest(p)!=f['sha256']:raise RuntimeError('Frozen input mismatch '+str(p))
    return doc
def original_comment_cells():
    # Raw metadata only: the original pandas dataframe is never modified.
    import zipfile,xml.etree.ElementTree as ET
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(SOURCE) as z:
        shared=[''.join(t.text or '' for t in si.findall('.//x:t',ns)) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        def scalar(cell):
            if cell is None:return None
            typ=cell.get('t');v=cell.find('x:v',ns)
            if typ=='s':return shared[int(v.text)]
            if typ=='inlineStr':return ''.join(t.text or '' for t in cell.findall('x:is//x:t',ns))
            if v is None:return None
            if typ in (None,'n'):
                value=float(v.text)
                assert math.isfinite(value)
                return value
            if typ=='b':
                assert v.text in ('0','1')
                return v.text=='1'
            if typ=='str':return v.text
            raise ValueError('Unexpected original XML comment scalar type '+str(typ))
        rows=sheet.findall('x:sheetData/x:row',ns)
        header=next(r for r in rows if r.get('r')=='1')
        columns=[ ''.join(c for c in cell.get('r') if c.isalpha()) for cell in header.findall('x:c',ns) if scalar(cell)=='Optional Comments']
        assert len(columns)==1
        values={}
        for row in rows:
            nr=int(row.get('r'))
            if not 2<=nr<=889:continue
            cell=next((c for c in row.findall('x:c',ns) if c.get('r')==columns[0]+str(nr)),None)
            values[nr]=scalar(cell)
            assert values[nr] is None or isinstance(values[nr],(str,int,float,bool))
        assert set(values)==set(range(2,890))
        return values
def main():
    assert len(sys.argv)==3 and sys.argv[1]=='--run'
    out=Path(sys.argv[2]).resolve();assert out.parent==BASE/'runs'
    assert not out.exists();out.mkdir(parents=True)
    start=now();resources=[guard('after imports')];freeze=verify_inputs()
    assert digest(SOURCE)=='c1c8e47d1e9fe73cd78f63e3a09c37879891955101d7ce357ad324113575c959'
    df=pd.read_excel(SOURCE,sheet_name='Sheet1',engine='openpyxl')
    required=['UUID','Chatbot','PatientQuestion','ChatbotResponse','AcceptableVersusProblematic','Range1to5']+ISSUES
    assert all(k in df for k in required) and len(df)==888
    for k in required[:6]:assert df[k].notna().all()
    assert set(df.Chatbot)==set(MODELS) and df.UUID.is_unique
    assert len(df.PatientQuestion.unique())==222
    assert all(len(g)==222 for _,g in df.groupby('Chatbot'))
    assert not df.duplicated(['PatientQuestion','Chatbot']).any()
    assert all(set(g.Chatbot)==set(MODELS) and len(g)==4 for _,g in df.groupby('PatientQuestion'))
    assert set(df.AcceptableVersusProblematic.astype(str).str.strip().str.lower())=={'acceptable','problematic'}
    assert np.isfinite(df.Range1to5.to_numpy(dtype=float)).all()
    assert df.Range1to5.between(1,5).all()
    raw=[]
    for i,row in df.iterrows():
        rec={'source_excel_row':int(i)+2}
        for k,v in row.items():
            if pd.isna(v):v=None
            elif isinstance(v,np.generic):v=v.item()
            rec[k]=v
        raw.append(rec)
    comments=original_comment_cells()
    for rec in raw:rec['Optional Comments']=comments[rec['source_excel_row']]
    save(out/'original_per_response_records.json',raw)
    resources.append(guard('raw workbook parsed'))
    normal=df.AcceptableVersusProblematic.astype(str).str.lower().str.strip().str.contains('problematic',na=False)
    literal=df.AcceptableVersusProblematic.astype(str).eq('Acceptable').astype(int)
    issue_stat={k:df[k].notna() for k in ISSUES}
    issue_plot={k:df[k].replace(r'^\s*$',pd.NA,regex=True).notna() for k in ISSUES}
    assert all(issue_stat[k].equals(issue_plot[k]) for k in ISSUES)
    metrics={};detail={'primary':{},'ratings':{},'issues':{},'correlations':{},'agreement':{}}
    counts={m:int(normal[df.Chatbot.eq(m)].sum()) for m in MODELS}
    for m in MODELS:
        metrics['problematic count '+m]=counts[m]
        metrics['problematic percent '+m]=100*counts[m]/222
        metrics['acceptable percent '+m]=100*(222-counts[m])/222
    metrics['problematic rate order']=sorted(MODELS,key=lambda m:counts[m])
    table=np.array([[counts[m],222-counts[m]] for m in MODELS])
    h,p,dfree,expected=stats.chi2_contingency(table)
    assert dfree==3 and expected.min()>=5
    metrics['primary chi-square']=float(h);metrics['primary omnibus p']=float(p)
    detail['primary']['omnibus']={'chi_square':float(h),'p':float(p),'df':int(dfree),'observed_table':table.tolist(),'expected_table':expected.tolist()}
    detail['primary']['pairwise']={}
    for a,b in PAIRS:
        d=ztest(counts[a],222,counts[b],222);k=a+'__'+b
        metrics['primary corrected p '+k]=d['p_bonferroni'];metrics['primary corrected p<0.05 '+k]=d['p_bonferroni']<.05
        detail['primary']['pairwise'][k]=dict(d,original_posthoc_dispatched=bool(p<.05))
    resources.append(guard('primary proportions'))
    arrays={m:df.loc[df.Chatbot.eq(m),'Range1to5'].to_numpy(dtype=float) for m in MODELS}
    for m,vals in arrays.items():
        metrics['rating mean '+m]=float(np.mean(vals));metrics['rating sample SD '+m]=float(np.std(vals,ddof=1))
        detail['ratings'][m]={'n':len(vals),'mean':metrics['rating mean '+m],'sample_SD':metrics['rating sample SD '+m]}
    metrics['descending mean rating order']=sorted(MODELS,key=lambda m:metrics['rating mean '+m],reverse=True)
    h,p=stats.kruskal(*[arrays[m] for m in MODELS])
    metrics['Kruskal-Wallis H']=float(h);metrics['Kruskal-Wallis p']=float(p)
    ranks=df.Range1to5.rank(method='average')
    N=len(df);ties=df.Range1to5.value_counts().to_numpy(dtype=float)
    tie_sum=float(np.sum(ties**3-ties));tie_term=tie_sum/(12*(N-1))
    avg={m:float(ranks[df.Chatbot.eq(m)].mean()) for m in MODELS}
    detail['ratings']['pooled_rank_details']={'N':N,'tie_sum':tie_sum,'tie_term':tie_term,'mean_ranks':avg,'Kruskal_H':float(h),'Kruskal_p':float(p)}
    detail['ratings']['dunn']={}
    for a,b in PAIRS:
        z=abs(avg[a]-avg[b])/math.sqrt((N*(N+1)/12-tie_term)*(1/len(arrays[a])+1/len(arrays[b])))
        p_raw=float(2*stats.norm.sf(z));adjusted=bonf(p_raw);k=a+'__'+b
        metrics['Dunn Bonferroni p '+k]=adjusted;metrics['Dunn Bonferroni p<0.05 '+k]=adjusted<.05
        detail['ratings']['dunn'][k]={'z':z,'p_raw':p_raw,'p_bonferroni':adjusted,'original_posthoc_dispatched':bool(metrics['Kruskal-Wallis p']<.05)}
    resources.append(guard('ratings'))
    for issue in ISSUES:
        c={m:int(issue_stat[issue][df.Chatbot.eq(m)].sum()) for m in MODELS}
        ct=np.array([[c[m],222-c[m]] for m in MODELS])
        h,p,dof,expected=stats.chi2_contingency(ct);assert dof==3 and expected.min()>=5
        metrics['issue chi-square '+issue]=float(h);metrics['issue omnibus p '+issue]=float(p)
        d={'counts':c,'chi_square':float(h),'p':float(p),'df':int(dof),'expected_table':expected.tolist(),'pairwise':{}}
        for m in MODELS:metrics['issue percent '+issue+'__'+m]=100*c[m]/222
        for a,b in PAIRS:
            z=ztest(c[a],222,c[b],222);k=a+'__'+b
            metrics['issue corrected p '+issue+'__'+k]=z['p_bonferroni'];metrics['issue corrected p<0.05 '+issue+'__'+k]=z['p_bonferroni']<.05
            d['pairwise'][k]=dict(z,original_posthoc_dispatched=bool(p<.05),status='original dispatched' if p<.05 else 'supporting unreported posthoc')
        detail['issues'][issue]=d
        resources.append(guard('issue '+issue))
    pivot=df.pivot(index='PatientQuestion',columns='Chatbot',values='AcceptableVersusProblematic').sort_index()
    assert pivot.shape==(222,4) and pivot.notna().all().all()
    all_a=pivot.eq('Acceptable').all(axis=1);all_p=pivot.eq('Problematic').all(axis=1)
    metrics['exact-literal agreement total_questions']=len(pivot)
    metrics['exact-literal agreement unanimous_acceptable']=int(all_a.sum())
    metrics['exact-literal agreement unanimous_problematic']=int(all_p.sum())
    metrics['exact-literal unanimous problematic question set']=pivot.index[all_p].tolist()
    detail['agreement']={'unanimous_acceptable_questions':pivot.index[all_a].tolist(),'unanimous_problematic_questions':pivot.index[all_p].tolist()}
    numeric=df.pivot(index='PatientQuestion',columns='Chatbot',values='Range1to5').sort_index()
    binary=pivot.eq('Acceptable').astype(float)
    for label,frame in [('exact_literal_binary',binary),('numeric_rating',numeric)]:
        corr=frame.corr(method='pearson')
        detail['correlations'][label]={'question_order':frame.index.tolist(),'matrix':corr.to_dict()}
        for a,b in PAIRS:metrics['Pearson '+label+'__'+a+'__'+b]=float(corr.loc[a,b])
        # Additional canonical pair orientations used by published upper triangle.
        for a,b in itertools.combinations(MODELS,2):metrics['Pearson '+label+'__'+a+'__'+b]=float(corr.loc[a,b])
    diagnostics={'normalized_labels':{},'paired_design':{},'Wilson95percent_intervals':{},'literal_parser_affected_records':[]}
    norm_pivot=df.assign(IsProblematic=normal).pivot(index='PatientQuestion',columns='Chatbot',values='IsProblematic').sort_index()
    norm_corr=(~norm_pivot).astype(float).corr()
    diagnostics['normalized_labels']={'Pearson_matrix':norm_corr.to_dict(),'unanimous_problematic_count':int(norm_pivot.all(axis=1).sum()),'unanimous_acceptable_count':int((~norm_pivot).all(axis=1).sum()),'unanimous_problematic_questions':norm_pivot.index[norm_pivot.all(axis=1)].tolist()}
    for i in df.index:
        if int(literal.loc[i])!=int(not normal.loc[i]):diagnostics['literal_parser_affected_records'].append({'source_excel_row':int(i)+2,'UUID':df.loc[i,'UUID'],'raw_label':df.loc[i,'AcceptableVersusProblematic']})
    for label,vec in [('primary',normal)]+[(k,issue_stat[k]) for k in ISSUES]:
        frame=df.assign(Value=vec).pivot(index='PatientQuestion',columns='Chatbot',values='Value').sort_index()
        pairs={}
        for a,b in PAIRS:
            d1=int((frame[a]&~frame[b]).sum());d2=int((~frame[a]&frame[b]).sum());n=d1+d2
            p=1. if n==0 else float(stats.binomtest(min(d1,d2),n,.5,alternative='two-sided').pvalue)
            pairs[a+'__'+b]={'discordant_a_only':d1,'discordant_b_only':d2,'p_raw':p,'p_bonferroni':bonf(p),'status':'supporting paired diagnostic; no credit'}
        diagnostics['paired_design'][label]=pairs
        for m in MODELS:
            k=int(frame[m].sum());diagnostics['Wilson95percent_intervals'][label+'__'+m]=wilson(k,222)
    fh,fp=stats.friedmanchisquare(*[numeric[m].to_numpy(dtype=float) for m in MODELS])
    diagnostics['paired_design']['numeric_Friedman']={'statistic':float(fh),'p':float(fp),'status':'supporting paired diagnostic; no credit'}
    resources.append(guard('all diagnostics'))
    for k,v in metrics.items():
        if isinstance(v,(float,int)) and not isinstance(v,bool):assert math.isfinite(v),k
    targetdoc=json.loads((BASE/'PROSPECTIVE_COMPLETE_QUANTITATIVE_TARGETS001.json').read_text(encoding='utf8'))
    assert len(targetdoc['all_targets'])==141
    checks=[check_target(t,metrics) for t in targetdoc['all_targets']]
    passed=sum(c['passed'] for c in checks)
    save(out/'all_original_method_metrics.json',metrics);save(out/'all_original_method_details.json',detail)
    save(out/'all_fixed_supporting_diagnostics.json',diagnostics);save(out/'mandatory_target_checks.json',checks)
    # Serialization-only repair must reproduce every original scientific output byte.
    baseline=BASE/'runs/run001'
    identical=[]
    for filename in ['all_original_method_metrics.json','all_original_method_details.json','all_fixed_supporting_diagnostics.json','mandatory_target_checks.json']:
        identical.append({'path':filename,'original_run001_sha256':digest(baseline/filename),'repair_sha256':digest(out/filename),'byte_identical':(out/filename).read_bytes()==(baseline/filename).read_bytes()})
    before=json.loads((baseline/'original_per_response_records.json').read_text(encoding='utf8'))
    assert len(before)==len(raw)
    changes=[]
    for i,(a,b) in enumerate(zip(before,raw)):
        assert set(a)==set(b)
        for field in a:
            if a[field]!=b[field]:changes.append({'record_index':i,'source_excel_row':b['source_excel_row'],'field':field,'original':a[field],'repaired':b[field]})
    expected=[{'record_index':561,'source_excel_row':563,'field':'Optional Comments','original':None,'repaired':''}]
    serialization_equal=all(x['byte_identical'] for x in identical) and changes==expected
    save(out/'RAW_SERIALIZATION_REPAIR_VALIDATION.json',{'original_run001_scientific_files':identical,'raw_metadata_changes':changes,'expected_only_metadata_change':expected,'repair_validated':serialization_equal,'original_dataframe_and_all_numerical_branches_unchanged':True})
    save(out/'RUN_SUMMARY.json',{'paper_id':'P120','utc_start':start,'utc_end':now(),'n_responses':888,'n_questions':222,'all_targets':141,'passed_targets':passed,'failed_targets':141-passed,'successful_central_result':passed==141 and serialization_equal,'serialization_repair_equivalence_passed':serialization_equal,'original_methods_retained':True,'resource_observations':resources,'source_hash':digest(SOURCE),'input_freeze_hash':digest(BASE/'CODE_INPUT_RUNTIME_FREEZE004.json'),'exit_status':(0 if passed==141 else 2) if serialization_equal else 3})
    files=[{'path':f.name,'bytes':f.stat().st_size,'sha256':digest(f)} for f in sorted(out.iterdir()) if f.is_file()]
    save(out/'RUN_MANIFEST.json',files)
    print(json.dumps({'all_targets':141,'passed_targets':passed,'failed_targets':141-passed,'result_directory':str(out)}))
    return (0 if passed==141 else 2) if serialization_equal else 3
if __name__=='__main__':sys.exit(main())
