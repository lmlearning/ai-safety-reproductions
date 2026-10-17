"""P134 independent source/formula auditor; prospective source only until root review.
No root-main imports. Character CSV parser and Decimal80 effect/pool arithmetic.
"""
from pathlib import Path
from decimal import Decimal,localcontext
import argparse,datetime,hashlib,json,math,os,sys,time
import psutil
BASE=Path(__file__).resolve().parents[1]
D=Decimal
FAMILY_MODELS={'overall_mental':'random','depression':'random','anxiety':'random','positive_affect':'random','negative_affect':'random','stress':'fixed','psychosomatic':'random','self_ambivalence':'fixed','life_satisfaction':'fixed','self_efficacy':'random','health':'fixed'}
FILES={f:f+'_means_source001.csv' for f in FAMILY_MODELS}
FILES.update(overall_mental='overall_mental_effects_source001.csv',health='health_effects_source001.csv')
NUMERIC_TOLERANCE=1e-9
REML_SOLVER_COMPARISON_TOLERANCE=1e-7
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=True,indent=2,allow_nan=False)+'\n',encoding='utf8')
def csv_chars(text):
 if text.startswith('\ufeff'):text=text[1:]
 table=[];row=[];cell=[];quoted=False;i=0
 while i<len(text):
  c=text[i]
  if quoted:
   if c=='"':
    if i+1<len(text) and text[i+1]=='"':cell.append('"');i+=1
    else:quoted=False
   else:cell.append(c)
  elif c=='"' and not cell:quoted=True
  elif c==',':row.append(''.join(cell));cell=[]
  elif c in '\r\n':
   row.append(''.join(cell));cell=[];table.append(row);row=[]
   if c=='\r' and i+1<len(text) and text[i+1]=='\n':i+=1
  else:cell.append(c)
  i+=1
 if quoted:raise ValueError('Unterminated quoted source CSV')
 if row or cell:row.append(''.join(cell));table.append(row)
 assert table and len(set(table[0]))==len(table[0])
 assert all(len(r)==len(table[0]) for r in table[1:])
 return [dict(zip(table[0],r)) for r in table[1:]]
def gamma_upper(a,x):
 # Normalized upper incomplete gamma: series below a+1, Lentz above.
 if x==0:return 1.
 eps=2e-15;tiny=1e-300;logscale=a*math.log(x)-x-math.lgamma(a)
 if x<a+1:
  term=total=1./a
  for n in range(1,100001):
   term*=x/(a+n);total+=term
   if abs(term)<=abs(total)*eps:return max(0.,min(1.,1.-total*math.exp(logscale)))
  raise ArithmeticError('Gamma series failed')
 b=x+1-a;c=1./tiny;d=1./b;h=d
 for n in range(1,100001):
  an=-n*(n-a);b+=2;d=an*d+b
  if abs(d)<tiny:d=tiny
  c=b+an/c
  if abs(c)<tiny:c=tiny
  d=1./d;delta=d*c;h*=delta
  if abs(delta-1.)<eps:return max(0.,min(1.,math.exp(logscale)*h))
 raise ArithmeticError('Gamma fraction failed')
def beta_fraction(a,b,x):
 tiny=1e-300;eps=2e-15;qab=a+b;qap=a+1.;qam=a-1.;c=1.;d=1.-qab*x/qap
 if abs(d)<tiny:d=tiny
 d=1./d;h=d
 for m in range(1,100001):
  m2=2*m;aa=m*(b-m)*x/((qam+m2)*(a+m2));d=1.+aa*d
  if abs(d)<tiny:d=tiny
  c=1.+aa/c
  if abs(c)<tiny:c=tiny
  d=1./d;h*=d*c
  aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));d=1.+aa*d
  if abs(d)<tiny:d=tiny
  c=1.+aa/c
  if abs(c)<tiny:c=tiny
  d=1./d;delta=d*c;h*=delta
  if abs(delta-1.)<eps:return h
 raise ArithmeticError('Beta fraction failed')
def beta_regularized(a,b,x):
 if x<=0:return 0.
 if x>=1:return 1.
 bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
 if x<(a+1)/(a+b+2):return bt*beta_fraction(a,b,x)/a
 return 1.-bt*beta_fraction(b,a,1.-x)/b
def student_p(t,df):return beta_regularized(df/2.,.5,df/(df+t*t))
def normal_p(z):return math.erfc(abs(z)/math.sqrt(2.))
def loggamma_decimal(z):
 # Independent Stirling/Bernoulli expansion with recurrence to z>=32.
 pi=D('3.141592653589793238462643383279502884197169399375105820974944592307816406286')
 corrections=D(0)
 while z<32:corrections-=z.ln();z+=1
 result=(z-D('.5'))*z.ln()-z+(2*pi).ln()/2
 terms=[(1,12),(-1,360),(1,1260),(-1,1680),(1,1188),(-691,360360),(1,156),(-3617,122400),(43867,244188),(-174611,125400)]
 for k,(a,c) in enumerate(terms):result+=D(a)/D(c)/z**(2*k+1)
 return result+corrections
def alternative_rows(raw,variant):
 rows=[]
 for item in raw:
  n1=int(item['experimental_n']);n2=int(item['control_n']);N=D(n1+n2)
  sd=(((D(n1)-1)*D(item['experimental_sd'])**2+(D(n2)-1)*D(item['control_sd'])**2)/(N-2)).sqrt()
  d=(D(item['experimental_mean'])-D(item['control_mean']))/sd
  g=d*(1-D(3)/(4*N-9))
  if variant=='variance_N':v=N/D(n1*n2)+g*g/(2*N)
  elif variant=='variance_N_minus2':v=N/D(n1*n2)+g*g/(2*(N-2))
  elif variant=='exact_J_historical_variance':
   df=N-2;J=(loggamma_decimal(df/2)-loggamma_decimal((df-1)/2)).exp()*(2/df).sqrt();g=d*J
   v=N/D(n1*n2)+g*g/(2*(N-D('3.94')))
  else:raise ValueError(variant)
  se=v.sqrt();rows.append({'row':int(item['row']),'study_key':item['study_key'],'g':g,'variance':v,'CI_low':g-D('1.96')*se,'CI_high':g+D('1.96')*se})
 return rows
def row_effect(raw,generic):
 if generic:g=D(raw['printed_effect']);v=D(raw['printed_se'])**2
 else:
  n1=int(raw['experimental_n']);n2=int(raw['control_n']);assert n1>1 and n2>1
  N=D(n1+n2);s1=D(raw['experimental_sd']);s2=D(raw['control_sd'])
  sd=(((D(n1)-1)*s1*s1+(D(n2)-1)*s2*s2)/(N-2)).sqrt();assert sd>0
  d=(D(raw['experimental_mean'])-D(raw['control_mean']))/sd
  g=d*(1-D(3)/(4*N-9))
  v=N/D(n1*n2)+g*g/(2*(N-D('3.94')))
 assert v>0
 se=v.sqrt()
 return {'row':int(raw['row']),'study_key':raw['study_key'],'g':g,'variance':v,'CI_low':g-D('1.96')*se,'CI_high':g+D('1.96')*se}
def json_row(r):return {k:str(v) if k=='row' else float(v) if isinstance(v,D) else v for k,v in r.items()}
def pool(rows,model):
 k=len(rows);assert k>0 and model in ('fixed','random')
 w=[1/r['variance'] for r in rows];sw=sum(w);fixed=sum(x*r['g'] for x,r in zip(w,rows))/sw
 Q=sum(x*(r['g']-fixed)**2 for x,r in zip(w,rows));df=k-1
 C=sw-sum(x*x for x in w)/sw
 tau=max(D(0),(Q-D(df))/C) if model=='random' and C>0 else D(0)
 weights=[1/(r['variance']+tau) for r in rows];s=sum(weights)
 g=sum(x*r['g'] for x,r in zip(weights,rows))/s;se=(1/s).sqrt();z=g/se;p=normal_p(float(z))
 interpretation=('negative_significant' if g<0 else 'positive_significant') if p<.05 else 'not_significant'
 return {'k':k,'g':float(g),'SE':float(se),'CI_low':float(g-D('1.96')*se),'CI_high':float(g+D('1.96')*se),'Q':float(Q),'Q_p':gamma_upper(df/2.,float(Q)/2.) if df>0 else None,'df':df,'I2':float(max(D(0),(Q-D(df))/Q)*100) if k>1 and Q>0 else 0.,'tau2':float(tau) if model=='random' else None,'Z':abs(float(z)),'p':p,'interpretation':interpretation,'model':model,'row_weights_percent':[float(x/s*100) for x in weights]}
def study_metadata(key,mapping):
 matches=[m for m in mapping if key.startswith(m)];assert len(matches)==1,(key,matches)
 base=matches[0];meta=mapping[base];female=meta['female_percent_literal'];trials=meta.get('trial_specific_female') or {}
 if trials:
  matches=[value for trial,value in trials.items() if trial in key]
  assert len(matches)==1,(key,matches);female=matches[0]
 assert female is not None
 return meta,female
def wls(rows,x,tau):
 weights=[1/(r['variance']+tau) for r in rows];s00=sum(weights);s01=sum(w*a for w,a in zip(weights,x));s11=sum(w*a*a for w,a in zip(weights,x));det=s00*s11-s01*s01;assert det>0
 c00=s11/det;c01=-s01/det;c11=s00/det
 y0=sum(w*r['g'] for w,r in zip(weights,rows));y1=sum(w*a*r['g'] for w,a,r in zip(weights,x,rows))
 b0=c00*y0+c01*y1;b1=c01*y0+c11*y1
 Q=sum(w*(r['g']-b0-b1*a)**2 for w,a,r in zip(weights,x,rows))
 return b0,b1,c00,c01,c11,Q,det,weights
def gender_fit(rows,raw_female,method):
 x=list(map(D,raw_female));n=len(rows);assert n>=10 and len(x)==n
 fixed=wls(rows,x,D(0));weights=fixed[-1];c00,c01,c11=fixed[2:5]
 t00=sum(w*w for w in weights);t01=sum(w*w*a for w,a in zip(weights,x));t11=sum(w*w*a*a for w,a in zip(weights,x))
 C=sum(weights)-(c00*t00+2*c01*t01+c11*t11)
 dl=max(D(0),(fixed[5]-D(n-2))/C) if C>0 else D(0)
 converged=True
 if method=='fixed':tau=D(0)
 elif method=='DL':tau=dl
 elif method=='REML':
  # independent golden-section bounded scalar search, then exact boundary-zero objective comparison
  gs=[r['g'] for r in rows];mean=sum(gs)/D(n);variance=sum((g-mean)**2 for g in gs)/D(n);upper=max(1.,float(100*variance))
  def objective(t):
   tau=D(str(t));fit=wls(rows,x,tau)
   return .5*(sum(math.log(float(r['variance']+tau)) for r in rows)+math.log(float(fit[6]))+float(fit[5]))
  a=0.;b=upper;ratio=(math.sqrt(5.)-1.)/2.;c=b-ratio*(b-a);d=a+ratio*(b-a);fc=objective(c);fd=objective(d)
  for iteration in range(160):
   if b-a<=1e-12:break
   if fc<=fd:b=d;d=c;fd=fc;c=b-ratio*(b-a);fc=objective(c)
   else:a=c;c=d;fc=fd;d=a+ratio*(b-a);fd=objective(d)
  converged=b-a<=1e-12
  best=c if fc<=fd else d
  tau=D(0) if objective(0.)<=objective(best) else D(str(best))
 else:raise ValueError(method)
 fit=wls(rows,x,tau);se=fit[4].sqrt();z=fit[1]/se
 return {'k':n,'method':method,'tau2':float(tau),'intercept':float(fit[0]),'slope':float(fit[1]),'SE_slope':float(se),'normal_p':normal_p(float(z)),'student_p':student_p(float(z),n-2),'df':n-2,'converged':converged,'raw_female_percent':raw_female}
def egger(rows):
 k=len(rows);assert k>=10
 x=[1/r['variance'].sqrt() for r in rows];y=[r['g']/r['variance'].sqrt() for r in rows]
 mx=sum(x)/D(k);my=sum(y)/D(k);Sxx=sum((a-mx)**2 for a in x);assert Sxx>0
 slope=sum((a-mx)*(b-my) for a,b in zip(x,y))/Sxx;intercept=my-slope*mx
 sigma2=sum((b-intercept-slope*a)**2 for a,b in zip(x,y))/D(k-2)
 se=(sigma2*(1/D(k)+mx*mx/Sxx)).sqrt();assert se>0;z=intercept/se
 return {'k':k,'intercept':float(intercept),'SE_intercept':float(se),'student_p':student_p(float(z),k-2),'normal_p':normal_p(float(z)),'df':k-2}
def supporting(rows,raw,mapping,model,family):
 loo={str(r['row']):pool([x for x in rows if x['row']!=r['row']],model) if len(rows)>1 else None for r in rows}
 trial_labels=sorted({r['study_key'].split('Measure')[0] for r in rows})
 trials={key:pool([r for r in rows if r['study_key'].split('Measure')[0]!=key],model) if any(r['study_key'].split('Measure')[0]!=key for r in rows) else None for key in trial_labels}
 fields=('control_type','duration','target_sample','reminders','interaction_mode','deployment','dialogue_system');subgroups={}
 for field in fields:
  groups={};unknown=[]
  for r in rows:
   meta,female=study_metadata(r['study_key'],mapping);label=meta[field]
   if label is None:unknown.append(str(r['row']))
   else:groups.setdefault(label,[]).append(r)
  grouped={label:{'row_ids':[str(r['row']) for r in selected],'original_family_method':pool(selected,model),'uniform_DL_random':pool(selected,'random'),'uniform_fixed':pool(selected,'fixed')} for label,selected in sorted(groups.items())}
  subgroups[field]={'unresolved_row_ids':unknown,'groups':grouped,'original_complete_claim':'unavailable for unresolved allocations' if unknown else 'conventional reconstruction'}
 female=[study_metadata(r['study_key'],mapping)[1] for r in rows]
 gender={m:gender_fit(rows,female,m) for m in ('REML','DL','fixed')} if len(rows)>=10 else {}
 e={'literal_more_than10_eligible':len(rows)>10,'source_life10_alternative_eligible':family=='life_satisfaction' and len(rows)==10,'result':egger(rows)} if len(rows)>=10 else {}
 trim={'status':'original implementation unspecified; no copied adjusted estimate','source_conflict':'mental zeroimputed sameobserved-.372 differs RevMan-.35'} if family in ('overall_mental','depression') else None
 result={'leave_one_row_out':loo,'leave_one_trial_out':trials,'subgroups':subgroups,'gender':gender,'egger':e,'original_trim_fill':trim}
 if family not in ('overall_mental','health'):
  controls={}
  for variant in ('variance_N','variance_N_minus2','exact_J_historical_variance'):
   alt=alternative_rows(raw,variant)
   controls[variant]={'pool':pool(alt,model),'rows':{str(r['row']):json_row(r) for r in alt},'supports_primary_rescue':False}
  result['uniform_variance_alternatives']=controls
 return result
def walk(obj,path):
 for key in path:obj=obj[key]
 return obj
def gatecheck(g,computed):
 actual=walk(computed,g['path']);target=g['target']
 if g['kind']=='rounded':
  difference=actual-float(target);passed=abs(D(str(actual))-D(target))<=D(g['tolerance'])
 else:difference=None;passed=actual==target and type(actual)==type(target)
 return dict(g,actual=actual,difference=difference,passed=passed)
def supporting_gatecheck(g,computed):
 actual=walk(computed,g['path']);kind=g['kind']
 assert g['primary_rescue'] is False
 difference=None
 if kind=='unprinted':passed=None
 elif kind=='exact':passed=actual==int(g['numeric_target'])
 elif kind=='relation':
  assert g['relation']=='<'
  passed=actual<float(g['numeric_target'])
 elif kind=='rounded':
  difference=actual-float(g['numeric_target']);passed=abs(difference)<=float(g['tolerance'])
 else:raise ValueError('Unknown supporting source display kind '+kind)
 return dict(g,actual=actual,difference=difference,passes_source_display=passed)
def frozen_configuration(freeze):
 config=freeze['config']
 required={'input_root','metadata_path','targets_path','supporting_targets_path','mode'}
 assert required.issubset(config)
 mode=config['mode'];assert mode in ('synthetic','original')
 paths={k:Path(config[k]).resolve() for k in required if k!='mode'}
 assert all(Path(config[k]).is_absolute() for k in paths)
 if config.get('row_targets_path'):
  assert mode=='original' and Path(config['row_targets_path']).is_absolute()
  paths['row_targets_path']=Path(config['row_targets_path']).resolve()
 files={str(Path(f['absolute_path']).resolve()):f for f in freeze['files']}
 assert len(files)==len(freeze['files'])
 for path in list(paths.values())+[paths['input_root']/n for n in FILES.values()]:
  if path==paths['input_root']:continue
  assert str(path) in files,('Configured input not frozen',str(path))
 original_raw=(BASE/'source_transcription002').resolve()
 original_meta=(BASE/'metadata_preparation001/ALL31_FIXED_METADATA_MAPPING001.json').resolve()
 if mode=='synthetic':
  assert paths['input_root']!=original_raw and paths['metadata_path']!=original_meta
  for name in files:
   path=Path(name)
   assert not path.is_relative_to(original_raw) and path!=original_meta,('Original raw input in synthetic freeze',name)
 return config,paths
def main(run,out,freeze_path):
 assert run.exists() and not out.exists();out.mkdir(parents=True)
 freeze=json.loads(freeze_path.read_text(encoding='utf8'))
 config,paths=frozen_configuration(freeze)
 checks=[]
 def check(key,actual,expected,passed,extra=None):
  item={'id':key,'actual':actual,'expected':expected,'passed':bool(passed)}
  if extra:item.update(extra)
  checks.append(item)
 def guard():
  m=psutil.virtual_memory().available;rss=psutil.Process().memory_info().rss;disk=psutil.disk_usage(str(BASE)).free
  policy=freeze['resource_policy']
  if m<policy['available_RAM_floor_bytes'] or rss>policy['process_tree_RSS_cap_bytes'] or disk<policy['free_disk_floor_bytes']:raise RuntimeError('Frozen independent audit resource guard breached')
 def compare(key,a,b):
  if isinstance(a,bool) or isinstance(b,bool):check(key,a,b,type(a)==type(b) and a==b);return
  if isinstance(a,(int,float)) and isinstance(b,(int,float)):
   tol=REML_SOLVER_COMPARISON_TOLERANCE if '/gender/REML/' in key else NUMERIC_TOLERANCE
   passed=math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol*max(1.,abs(a),abs(b));check(key,a,b,passed,{'relative_tolerance':tol});return
  if isinstance(a,dict) and isinstance(b,dict):
   check(key+'/keys',sorted(a),sorted(b),set(a)==set(b))
   for k in sorted(set(a)&set(b)):compare(key+'/'+k,a[k],b[k])
  elif isinstance(a,list) and isinstance(b,list):
   check(key+'/length',len(a),len(b),len(a)==len(b))
   for i,(x,z) in enumerate(zip(a,b)):compare(key+'/'+str(i),x,z)
  else:check(key,a,b,type(a)==type(b) and a==b)
 guard()
 for f in freeze['files']:
  guard();p=Path(f['absolute_path']);actual_sha=sha(p);actual_bytes=p.stat().st_size
  check('frozen/'+f['absolute_path'],actual_sha,f['sha256'],actual_sha==f['sha256'])
  check('frozen_bytes/'+f['absolute_path'],actual_bytes,f['bytes'],actual_bytes==f['bytes'])
 assert all(x['passed'] for x in checks),'Frozen file integrity failed before independent reconstruction'
 manifest_path=run/'OUTPUT_MANIFEST.json'
 if manifest_path.exists():
  for f in json.loads(manifest_path.read_text(encoding='utf8')):
   p=run/f['path'];check('outputhash/'+f['path'],sha(p),f['sha256'],sha(p)==f['sha256'])
 mappingdoc=json.loads(paths['metadata_path'].read_text(encoding='utf8'))
 mapping=mappingdoc['metadata'];check('metadata/study_count',len(mapping),31,len(mapping)==31)
 main_result=json.loads((run/'ALL_ORIGINAL_COMPUTATIONS.json').read_text(encoding='utf8'))
 check('metadata/exact_all31',main_result['metadata_used'],mapping,main_result['metadata_used']==mapping)
 computed={'families':{},'raw_source_records':{},'metadata_used':mapping};census={}
 with localcontext() as ctx:
  ctx.prec=80
  for family,model in FAMILY_MODELS.items():
   guard();raw=csv_chars((paths['input_root']/FILES[family]).read_bytes().decode('utf8'));computed['raw_source_records'][family]=raw
   check('raw_exact/'+family,main_result['raw_source_records'][family],raw,main_result['raw_source_records'][family]==raw)
   identifiers=[r['row'] for r in raw];check('raw_ids/'+family,identifiers,[str(i) for i in range(1,len(raw)+1)],identifiers==[str(i) for i in range(1,len(raw)+1)])
   generic=family in ('overall_mental','health');rows=[row_effect(r,generic) for r in raw]
   result={'pool':pool(rows,model),'rows':{str(r['row']):json_row(r) for r in rows},'supporting':supporting(rows,raw,mapping,model,family)}
   if not generic:result['arm_totals']={'experimental_n':sum(int(r['experimental_n']) for r in raw),'control_n':sum(int(r['control_n']) for r in raw)}
   computed['families'][family]=result;census[family]=len(raw)
 guard();check('families/whole11',list(computed['families']),list(FAMILY_MODELS),len(computed['families'])==11)
 check('raw/whole145',sum(census.values()),145,sum(census.values())==145)
 check('mean/whole88',sum(census[f] for f in census if f not in ('overall_mental','health')),88,sum(census[f] for f in census if f not in ('overall_mental','health'))==88)
 fixed=json.loads(paths['targets_path'].read_text(encoding='utf8'));gates=[gatecheck(g,computed) for g in fixed['gates']]
 check('targets/whole337',len(gates),337,len(gates)==337)
 main_gates=json.loads((run/'ALL337_PRIMARY_CHECKS.json').read_text(encoding='utf8'))
 byid={g['id']:g for g in main_gates};check('target_ids',list(byid),[g['id'] for g in gates],list(byid)==[g['id'] for g in gates])
 for g in fixed['gates']:
  check('target_source_exact/'+g['id'],{k:byid[g['id']].get(k) for k in g},g,{k:byid[g['id']].get(k) for k in g}==g)
 compare('primary_checks',main_gates,gates)
 compare('computations',main_result,computed)
 if 'row_targets_path' in paths:
  target_raw=csv_chars(paths['row_targets_path'].read_bytes().decode('utf8'))
  check('source_target_rows/88',len(target_raw),88,len(target_raw)==88)
  # Explicitly frozen optional original-only literal target coherence; never a formula input.
  for row in target_raw:
   for field in ('effect','CI_low','CI_high'):
    metric='g' if field=='effect' else field
    target=next(g for g in fixed['gates'] if g['path']==['families',row['family'],'rows',row['row'],metric])
    check('printed_row_target/'+target['id'],row[field],target['target'],row[field]==target['target'])
 supporting_fixed=json.loads(paths['supporting_targets_path'].read_text(encoding='utf8'))
 supporting_gates=[supporting_gatecheck(g,computed) for g in supporting_fixed['checks']]
 check('supporting_targets/whole336',len(supporting_gates),336,len(supporting_gates)==336)
 check('supporting_targets/whole332_numeric',sum(g['kind']!='unprinted' for g in supporting_gates),332,sum(g['kind']!='unprinted' for g in supporting_gates)==332)
 check('supporting_targets/whole4_unprinted',sum(g['kind']=='unprinted' for g in supporting_gates),4,sum(g['kind']=='unprinted' for g in supporting_gates)==4)
 main_supporting=json.loads((run/'ALL_SUPPORTING_SOURCE_COMPARISONS.json').read_text(encoding='utf8'))
 support_byid={g['id']:g for g in main_supporting}
 check('supporting_target_ids',[g['id'] for g in main_supporting],[g['id'] for g in supporting_gates],len(support_byid)==336 and [g['id'] for g in main_supporting]==[g['id'] for g in supporting_gates])
 for g in supporting_fixed['checks']:
  actual={k:support_byid.get(g['id'],{}).get(k) for k in g}
  check('supporting_source_exact/'+g['id'],actual,g,actual==g)
 compare('supporting_source_comparisons',main_supporting,supporting_gates)
 science=all(g['passed'] for g in gates)
 expected_summary={'complete_families':11,'raw_rows':145,'gates':337,'passed':sum(g['passed'] for g in gates),'all_passed':science,'original_human_trials_repeated':False,'complete_337_and_rule':True,'mode':config['mode']}
 main_summary=json.loads((run/'SUMMARY.json').read_text(encoding='utf8'))
 check('main_summary/keys',sorted(main_summary),sorted(set(expected_summary)|{'utc'}),set(main_summary)==set(expected_summary)|{'utc'})
 compare('main_summary',{k:main_summary.get(k) for k in expected_summary},expected_summary)
 try:
  parsed_utc=datetime.datetime.fromisoformat(main_summary['utc']);valid_utc=parsed_utc.tzinfo is not None
 except (ValueError,TypeError,KeyError):valid_utc=False
 check('main_summary/utc_valid',main_summary.get('utc'),'timezone-aware ISO timestamp',valid_utc)
 integrity=all(x['passed'] for x in checks);science=all(g['passed'] for g in gates)
 report={'paper_id':'P134','created_utc':utc(),'complete':True,'independent_integrity_checks':len(checks),'passed_integrity_checks':sum(x['passed'] for x in checks),'all_integrity_passed':integrity,'mandatory_target_count':len(gates),'passed_mandatory_targets':sum(g['passed'] for g in gates),'all_mandatory_targets_passed':science,'all11_families_145_raw_88_mean_rows_337_gates_complete':True,'census':census,'no_root_main_import':True,'method':'character-state raw CSV parser; Decimal80 RevMan formulas; custom gamma/beta tails; independent WLS/golden-section REML; exact raw strings/metadata/source gate metadata','default_numeric_audit_tolerance':NUMERIC_TOLERANCE,'REML_solver_audit_tolerance':REML_SOLVER_COMPARISON_TOLERANCE,'supporting_unresolved_allocations_not_rescues':True,'mode':config['mode'],'complete336_supporting_source_comparisons':True,'supporting_comparison_count':len(supporting_gates),'supporting_numeric_count':332,'supporting_unprinted_count':4,'supporting_source_display_passed':sum(g['passes_source_display'] is True for g in supporting_gates),'supporting_source_display_failed':sum(g['passes_source_display'] is False for g in supporting_gates),'supporting_displays_do_not_rescue_primary':True,'all_input_paths_from_frozen_config':True}
 save(out/'INDEPENDENT_ALL_ORIGINAL_COMPUTATIONS.json',computed);save(out/'INDEPENDENT_ALL337_PRIMARY_CHECKS.json',gates);save(out/'INDEPENDENT_ALL_SUPPORTING_SOURCE_COMPARISONS.json',supporting_gates);save(out/'INDEPENDENT_INTEGRITY_CHECKS.json',checks);save(out/'SUMMARY.json',report)
 save(out/'OUTPUT_MANIFEST.json',[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.is_file()])
 print(json.dumps(report));return 0 if integrity and science else 2
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--audit',nargs=2,type=Path,required=True);ap.add_argument('--freeze',type=Path,required=True);args=ap.parse_args()
 try:sys.exit(main(args.audit[0],args.audit[1],args.freeze))
 except Exception as error:
  if args.audit[1].exists():save(args.audit[1]/'ENGINEERING_FAILURE.json',{'utc':utc(),'error_type':type(error).__name__,'error':str(error)})
  raise
