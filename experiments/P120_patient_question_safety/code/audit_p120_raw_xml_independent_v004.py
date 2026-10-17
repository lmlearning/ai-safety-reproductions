"""Independent P120 raw XLSX/XML audit; never imports runner or borrows its aggregates."""
from pathlib import Path
import os,sys,json,hashlib,datetime,math,itertools,collections,zipfile,xml.etree.ElementTree as ET
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
from scipy.special import gammaincc
import psutil
BASE=Path(__file__).resolve().parents[1]
NAMES=['Claude','Gemini','GPT-4o','Llama']
TAGS=['Unsafe','Includes Problematic Content','Missing Important Info','Missing History Taking','Poor Writing']
PAIR_ORDER=[('Claude','Gemini'),('Claude','Llama'),('Claude','GPT-4o'),('Gemini','Llama'),('Gemini','GPT-4o'),('Llama','GPT-4o')]
SOURCE=BASE/'sources/original_preprint_repo/SupplementaryDocuments/HealthAdviceDatasetWithEvaluations.xlsx'
X={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2,allow_nan=False)+'\n',encoding='utf8')
def resources(stage):
    p=psutil.Process();m=p.memory_info();a=psutil.virtual_memory().available;d=psutil.disk_usage(str(BASE)).free
    if m.rss>2**30 or a<1.5*2**30 or d<35*2**30:raise RuntimeError('Independent audit resource floor/cap breach')
    return {'stage':stage,'utc':utc(),'RSS_bytes':m.rss,'available_RAM_bytes':a,'free_disk_bytes':d,'peak_working_set_bytes':getattr(m,'peak_wset',None)}
def raw_rows():
    with zipfile.ZipFile(SOURCE) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')):
                shared.append(''.join(t.text or '' for t in si.findall('.//x:t',X)))
        sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'));records=[];header={}
        for row in sheet.findall('x:sheetData/x:row',X):
            nr=int(row.get('r'));cells={}
            for cell in row.findall('x:c',X):
                address=cell.get('r');col=''.join(c for c in address if c.isalpha())
                if cell.find('x:f',X) is not None:raise ValueError('Unexpected source formula '+address)
                v=cell.find('x:v',X);value=v.text if v is not None else None
                typ=cell.get('t')
                if typ=='s':value=shared[int(value)] if value is not None else None
                elif typ=='inlineStr':value=''.join(t.text or '' for t in cell.findall('x:is//x:t',X))
                elif value is not None and typ in (None,'n'):value=float(value)
                elif typ not in (None,'n','s','inlineStr'):raise ValueError('Unspecified cell type '+str(typ))
                cells[col]=value
            if nr==1:header=cells
            else:
                if not any(v is not None for v in cells.values()):continue
                records.append(dict([('source_excel_row',nr)]+[(name,cells.get(col)) for col,name in header.items()]))
        assert len(header)==17 and len(records)==888
        assert [r['source_excel_row'] for r in records]==list(range(2,890))
        return records
def is_problematic(record):return 'problematic' in str(record['AcceptableVersusProblematic']).lower().strip()
def adjusted(p):return min(1.,p*6)
def pooled_z(a,b,n=222):
    pooled=(a+b)/(2*n);v=pooled*(1-pooled)*(2/n)
    if v<=0:raise ValueError('Undefined original z statistic')
    z=((a-b)/n)/math.sqrt(v);p=math.erfc(abs(z)/math.sqrt(2))
    return {'z':z,'p_raw':p,'p_bonferroni':adjusted(p),'difference_percentage_points':100*(a-b)/n}
def chi(counts):
    n=222;total=sum(counts);expected_positive=total/4;expected_negative=n-expected_positive
    assert expected_positive>=5 and expected_negative>=5
    statistic=math.fsum((c-expected_positive)**2/expected_positive+((n-c)-expected_negative)**2/expected_negative for c in counts)
    return statistic,float(gammaincc(1.5,statistic/2))
def corr(a,b):
    n=len(a);assert len(b)==n==222
    ma=math.fsum(a)/n;mb=math.fsum(b)/n
    top=math.fsum((x-ma)*(y-mb) for x,y in zip(a,b))
    left=math.fsum((x-ma)**2 for x in a);right=math.fsum((x-mb)**2 for x in b)
    if left<=0 or right<=0:raise ValueError('Undefined original Pearson')
    return top/math.sqrt(left*right)
def rank_values(values):
    freq=collections.Counter(values);before=0;mapping={}
    for value,count in sorted(freq.items()):
        mapping[value]=before+(count+1)/2;before+=count
    return mapping,freq
def paired_p(b,c):
    n=b+c
    if n==0:return 1.
    # Exact symmetric binomial probability tail: integer coefficients, no shared test routine.
    tail=sum(math.comb(n,i) for i in range(min(b,c)+1))
    return min(1.,(2*tail)/(2**n))
def wilson_count(c):
    n=222;z=1.959963984540054;v=c/n;den=1+z*z/n
    center=(v+z*z/(2*n))/den;span=z*math.sqrt((v*(1-v)+z*z/(4*n))/n)/den
    return [center-span,center+span]
def decide(t,m):
    value=m[t['metric']];target=t['target'];kind=t['comparison']
    if kind=='absolute':ok=abs(value-target)<=t['absolute_tolerance']*(1+1e-12)
    elif kind=='exact':ok=value==target
    elif kind=='exact_set':ok=set(value)==set(target) and len(value)==len(target)
    elif kind=='less_than':ok=value<target
    elif kind=='greater_than':ok=value>target
    elif kind=='at_least':ok=value>=target
    elif kind=='closed_interval':ok=target[0]<=value<=target[1]
    else:raise ValueError('Unknown comparison '+kind)
    return dict(t,observed=value,passed=bool(ok))
def main():
    assert len(sys.argv)==4 and sys.argv[1]=='--audit'
    run=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]).resolve()
    assert run.parent==BASE/'runs' and out.parent==BASE/'audits'
    assert not out.exists();out.mkdir(parents=True)
    start=utc();samples=[resources('after independent audit imports')];checks=[]
    def record(label,ok,**extra):checks.append(dict({'check':label,'passed':bool(ok)},**extra))
    def compare(label,a,b):
        if isinstance(a,dict) and isinstance(b,dict):
            record(label+' keys',set(a)==set(b))
            for k in sorted(set(a)&set(b)):compare(label+'/'+str(k),a[k],b[k])
        elif isinstance(a,list) and isinstance(b,list):
            record(label+' length',len(a)==len(b))
            for i,(x,y) in enumerate(zip(a,b)):compare(label+'/'+str(i),x,y)
        elif isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
            ok=math.isfinite(a) and math.isfinite(b) and abs(a-b)<=max(1e-13,1e-10*abs(a))
            record(label,ok,independent=a,runner=b)
        else:record(label,a==b,independent=a,runner=b)
    def compare_raw_records(label,a,b):
        # Original raw cells use exact scalar equality, never statistical tolerance.
        record(label+' length',len(a)==len(b))
        for i,(left,right) in enumerate(zip(a,b)):
            record(label+'/'+str(i)+' keys',set(left)==set(right))
            for k in sorted(set(left)&set(right)):
                x,y=left[k],right[k]
                numeric=lambda v:isinstance(v,(int,float)) and not isinstance(v,bool)
                if numeric(x) and numeric(y):
                    ok=math.isfinite(x) and math.isfinite(y) and x==y
                else:
                    ok=type(x) is type(y) and x==y
                record(label+'/'+str(i)+'/'+str(k),ok,independent=x,runner=y)
    freeze=json.loads((BASE/'CODE_INPUT_RUNTIME_FREEZE004.json').read_text(encoding='utf8'))
    for item in freeze['files']:record('frozen input '+item['absolute_path'],sha(Path(item['absolute_path']))==item['sha256'])
    record('original workbook hash',sha(SOURCE)=='c1c8e47d1e9fe73cd78f63e3a09c37879891955101d7ce357ad324113575c959')
    manifest=json.loads((run/'RUN_MANIFEST.json').read_text(encoding='utf8'))
    record('run manifest filename set',{f.name for f in run.iterdir() if f.is_file()}=={x['path'] for x in manifest}|{'RUN_MANIFEST.json'})
    for item in manifest:
        f=run/item['path'];record('run output hash '+item['path'],f.is_file() and f.stat().st_size==item['bytes'] and sha(f)==item['sha256'])
    rows=raw_rows();write(out/'independent_raw_xml_records.json',rows)
    runner_rows=json.loads((run/'original_per_response_records.json').read_text(encoding='utf8'));compare_raw_records('all raw source cells',rows,runner_rows)
    # Additional strict preservation gates, independent of recomputed statistics.
    original=BASE/'runs/run001'
    for filename in ['all_original_method_metrics.json','all_original_method_details.json','all_fixed_supporting_diagnostics.json','mandatory_target_checks.json']:
        record('repair original scientific bytes '+filename,(run/filename).read_bytes()==(original/filename).read_bytes())
    before=json.loads((original/'original_per_response_records.json').read_text(encoding='utf8'));changes=[]
    record('repair original raw row count',len(before)==len(runner_rows))
    for i,(left,right) in enumerate(zip(before,runner_rows)):
        record('repair original raw keys '+str(i),set(left)==set(right))
        for field in set(left)&set(right):
            if left[field]!=right[field]:changes.append({'record_index':i,'source_excel_row':right['source_excel_row'],'field':field,'original':left[field],'repaired':right[field]})
    expected=[{'record_index':561,'source_excel_row':563,'field':'Optional Comments','original':None,'repaired':''}]
    record('repair only original XML empty comment changed',changes==expected,observed=changes,expected=expected)
    repair=json.loads((run/'RAW_SERIALIZATION_REPAIR_VALIDATION.json').read_text(encoding='utf8'))
    record('repair runner validation explicitly passed',repair['repair_validated'] is True)
    cohorts={m:[r for r in rows if r['Chatbot']==m] for m in NAMES}
    questions=sorted({r['PatientQuestion'] for r in rows});assert len(questions)==222
    assert len({r['UUID'] for r in rows})==888
    lookup={(r['PatientQuestion'],r['Chatbot']):r for r in rows}
    assert len(lookup)==888
    for m in NAMES:assert len(cohorts[m])==222 and all((q,m) in lookup for q in questions)
    for r in rows:
        for k in ['UUID','Chatbot','PatientQuestion','ChatbotResponse','AcceptableVersusProblematic','Range1to5']:assert r[k] is not None
        assert str(r['AcceptableVersusProblematic']).strip().lower() in ('acceptable','problematic')
        assert math.isfinite(float(r['Range1to5'])) and 1<=float(r['Range1to5'])<=5
        for tag in TAGS:assert r[tag] is None or str(r[tag]).strip()
    samples.append(resources('independent raw source validated'))
    metrics={};numbers={m:sum(is_problematic(r) for r in cohorts[m]) for m in NAMES}
    for m,c in numbers.items():
        metrics['problematic count '+m]=c;metrics['problematic percent '+m]=100*c/222;metrics['acceptable percent '+m]=100*(222-c)/222
    metrics['problematic rate order']=sorted(NAMES,key=lambda m:numbers[m])
    h,p=chi([numbers[m] for m in NAMES]);metrics['primary chi-square']=h;metrics['primary omnibus p']=p
    for a,b in PAIR_ORDER:
        d=pooled_z(numbers[a],numbers[b]);k=a+'__'+b
        metrics['primary corrected p '+k]=d['p_bonferroni'];metrics['primary corrected p<0.05 '+k]=d['p_bonferroni']<.05
    ratings={m:[float(r['Range1to5']) for r in cohorts[m]] for m in NAMES}
    for m,v in ratings.items():
        mean=math.fsum(v)/222;sd=math.sqrt(math.fsum((x-mean)**2 for x in v)/221)
        metrics['rating mean '+m]=mean;metrics['rating sample SD '+m]=sd
    metrics['descending mean rating order']=sorted(NAMES,key=lambda m:metrics['rating mean '+m],reverse=True)
    pooled=[x for m in NAMES for x in ratings[m]];rank,freq=rank_values(pooled);n=len(pooled)
    sums={m:math.fsum(rank[x] for x in ratings[m]) for m in NAMES}
    ties=sum(t**3-t for t in freq.values());correction=1-ties/(n**3-n)
    h=(12*math.fsum(sums[m]**2/222 for m in NAMES)/(n*(n+1))-3*(n+1))/correction
    metrics['Kruskal-Wallis H']=h;metrics['Kruskal-Wallis p']=float(gammaincc(1.5,h/2))
    varrank=n*(n+1)/12-ties/(12*(n-1))
    for a,b in PAIR_ORDER:
        z=abs(sums[a]/222-sums[b]/222)/math.sqrt(varrank*(2/222));pv=adjusted(math.erfc(z/math.sqrt(2)));k=a+'__'+b
        metrics['Dunn Bonferroni p '+k]=pv;metrics['Dunn Bonferroni p<0.05 '+k]=pv<.05
    samples.append(resources('independent rank and primary formulas'))
    for tag in TAGS:
        c={m:sum(r[tag] is not None for r in cohorts[m]) for m in NAMES}
        h,p=chi([c[m] for m in NAMES]);metrics['issue chi-square '+tag]=h;metrics['issue omnibus p '+tag]=p
        for m in NAMES:metrics['issue percent '+tag+'__'+m]=100*c[m]/222
        for a,b in PAIR_ORDER:
            p=pooled_z(c[a],c[b])['p_bonferroni'];k=tag+'__'+a+'__'+b
            metrics['issue corrected p '+k]=p;metrics['issue corrected p<0.05 '+k]=p<.05
        samples.append(resources('independent issue '+tag))
    acceptable=[q for q in questions if all(lookup[q,m]['AcceptableVersusProblematic']=='Acceptable' for m in NAMES)]
    problematic=[q for q in questions if all(lookup[q,m]['AcceptableVersusProblematic']=='Problematic' for m in NAMES)]
    metrics['exact-literal agreement total_questions']=222;metrics['exact-literal agreement unanimous_acceptable']=len(acceptable);metrics['exact-literal agreement unanimous_problematic']=len(problematic);metrics['exact-literal unanimous problematic question set']=problematic
    vectors={'exact_literal_binary':{m:[int(lookup[q,m]['AcceptableVersusProblematic']=='Acceptable') for q in questions] for m in NAMES},'numeric_rating':{m:[float(lookup[q,m]['Range1to5']) for q in questions] for m in NAMES}}
    for label,data in vectors.items():
        for a,b in set(PAIR_ORDER)|set(itertools.combinations(NAMES,2)):metrics['Pearson '+label+'__'+a+'__'+b]=corr(data[a],data[b])
    compare('all original-method metrics',metrics,json.loads((run/'all_original_method_metrics.json').read_text(encoding='utf8')))
    diagnostics={'normalized_labels':{},'paired_design':{},'Wilson95percent_intervals':{},'literal_parser_affected_records':[]}
    normalized={m:[not is_problematic(lookup[q,m]) for q in questions] for m in NAMES}
    matrix={b:{a:corr(normalized[a],normalized[b]) for a in NAMES} for b in NAMES}
    na=[q for q in questions if all(not is_problematic(lookup[q,m]) for m in NAMES)]
    np=[q for q in questions if all(is_problematic(lookup[q,m]) for m in NAMES)]
    diagnostics['normalized_labels']={'Pearson_matrix':matrix,'unanimous_problematic_count':len(np),'unanimous_acceptable_count':len(na),'unanimous_problematic_questions':np}
    for r in rows:
        if int(r['AcceptableVersusProblematic']=='Acceptable')!=int(not is_problematic(r)):diagnostics['literal_parser_affected_records'].append({'source_excel_row':r['source_excel_row'],'UUID':r['UUID'],'raw_label':r['AcceptableVersusProblematic']})
    for label in ['primary']+TAGS:
        vectors={m:[is_problematic(lookup[q,m]) if label=='primary' else lookup[q,m][label] is not None for q in questions] for m in NAMES}
        part={}
        for a,b in PAIR_ORDER:
            b1=sum(x and not y for x,y in zip(vectors[a],vectors[b]));c1=sum(y and not x for x,y in zip(vectors[a],vectors[b]));p=paired_p(b1,c1)
            part[a+'__'+b]={'discordant_a_only':b1,'discordant_b_only':c1,'p_raw':p,'p_bonferroni':adjusted(p),'status':'supporting paired diagnostic; no credit'}
        diagnostics['paired_design'][label]=part
        for m in NAMES:diagnostics['Wilson95percent_intervals'][label+'__'+m]=wilson_count(sum(vectors[m]))
    # Independent Friedman within-block average ranks and explicit tie correction.
    rank_sums={m:0. for m in NAMES};within_ties=0
    for q in questions:
        vals=[float(lookup[q,m]['Range1to5']) for m in NAMES];rm,fs=rank_values(vals)
        for m,v in zip(NAMES,vals):rank_sums[m]+=rm[v]
        within_ties+=sum(t**3-t for t in fs.values())
    k=4;nb=222;tie_factor=1-within_ties/(nb*k*(k*k-1))
    fh=(12*math.fsum(x*x for x in rank_sums.values())/(nb*k*(k+1))-3*nb*(k+1))/tie_factor
    diagnostics['paired_design']['numeric_Friedman']={'statistic':fh,'p':float(gammaincc(1.5,fh/2)),'status':'supporting paired diagnostic; no credit'}
    compare('all fixed supporting diagnostics',diagnostics,json.loads((run/'all_fixed_supporting_diagnostics.json').read_text(encoding='utf8')))
    write(out/'independent_all_original_metrics.json',metrics);write(out/'independent_all_fixed_diagnostics.json',diagnostics)
    targetfile=BASE/'PROSPECTIVE_COMPLETE_QUANTITATIVE_TARGETS001.json';targets=json.loads(targetfile.read_text(encoding='utf8'))['all_targets'];assert len(targets)==141
    original_checks=[decide(t,metrics) for t in targets]
    compare('all original target-check objects',original_checks,json.loads((run/'mandatory_target_checks.json').read_text(encoding='utf8')))
    summary=json.loads((run/'RUN_SUMMARY.json').read_text(encoding='utf8'));passed=sum(x['passed'] for x in original_checks)
    record('runner reports all141',summary['all_targets']==141);record('runner passing count reproduced',summary['passed_targets']==passed);record('runner failure count reproduced',summary['failed_targets']==141-passed);record('success flag equivalent to all141',summary['successful_central_result']==(passed==141))
    samples.append(resources('complete independent audit'))
    write(out/'all_independent_integrity_checks.json',checks);write(out/'independent_mandatory_target_checks.json',original_checks)
    invalid=sum(not x['passed'] for x in checks)
    result={'paper_id':'P120','utc_start':start,'utc_end':utc(),'integrity_checks':len(checks),'integrity_passed':len(checks)-invalid,'integrity_failed':invalid,'mandatory_targets':141,'mandatory_targets_passed':passed,'mandatory_targets_failed':141-passed,'successful_central_result':invalid==0 and passed==141,'complete_audit':True,'resource_observations':samples,'audit_exit_policy':'exit0 if all independent integrity checks pass, retaining any scientific failure; exit2 for integrity failures','exit_status':0 if invalid==0 else 2}
    write(out/'AUDIT_SUMMARY.json',result)
    write(out/'AUDIT_MANIFEST.json',[{'path':f.name,'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(out.iterdir()) if f.is_file()])
    print(json.dumps({k:v for k,v in result.items() if k!='resource_observations'}))
    return 0 if invalid==0 else 2
if __name__=='__main__':sys.exit(main())
