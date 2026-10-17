import pathlib,json,csv,ast,math,hashlib,datetime as dt,time,shutil,random,collections
import numpy as np
import mpmath as mp
mp.mp.dps=60
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'papers/P068_medical_assistant_rct';RUN=OUT/'runs/P068-central-002';AUD=OUT/'audits/P068-audit-001'
assert not AUD.exists();AUD.mkdir(parents=True);shutil.copyfile(__file__,AUD/'auditor.py')
stamp=dt.datetime.now(dt.timezone.utc).isoformat();wall=time.perf_counter()
plan=json.loads((RUN/'PREREGISTRATION.json').read_text());result=json.loads((RUN/'results.json').read_text());categories=collections.defaultdict(lambda:[0,0]);failures=[];scalar_checks=[]
def check(category,name,passed,actual=None,expected=None):
 categories[category][1]+=1;categories[category][0]+=bool(passed)
 row={'category':category,'name':name,'passed':bool(passed),'actual':actual,'expected':expected}
 if category not in ['raw_score_engine','raw_score_original','bootstrap_draw_statistics']:scalar_checks.append(row)
 if not passed:failures.append(row)
def near(category,key,actual,expected,tol=1e-10):
 check(category,key,abs(float(actual)-float(expected))<=tol,float(actual),float(expected))
# Independent semiglobal Levenshtein bit-vector search: free text prefix and any end.
def edit_match(pattern,text,k):
 if pattern in text:return True
 m=len(pattern)
 if not m:return True
 mask=(1<<m)-1;high=1<<(m-1);pv=mask;mv=0;score=m
 eqs={}
 for i,ch in enumerate(pattern):eqs[ch]=eqs.get(ch,0)|(1<<i)
 for ch in text:
  eq=eqs.get(ch,0);xv=eq|mv
  xh=(((eq&pv)+pv)^pv)|eq
  ph=mv|~(xh|pv);mh=pv&xh
  if ph&high:score+=1
  elif mh&high:score-=1
  if score<=k:return True
  ph=(ph<<1)&mask;mh=(mh<<1)&mask
  pv=(mh|~(xv|ph))&mask;mv=(ph&xv)&mask
 return False
def matrix_match(pattern,text,k):
 old=list(range(len(pattern)+1));best=len(pattern)
 for ch in text:
  new=[0]
  for i,pc in enumerate(pattern,1):new.append(min(old[i]+1,new[-1]+1,old[i-1]+(ch!=pc)))
  best=min(best,new[-1]);old=new
 return best<=k
rng=random.Random(681)
for i in range(1000):
 pat=''.join(rng.choice('abcde') for _ in range(rng.randrange(1,18)));text=''.join(rng.choice('abcde') for _ in range(rng.randrange(0,50)));k=len(pat)//5
 check('independent_scorer_validation',str(i),edit_match(pat,text,k)==matrix_match(pat,text,k))
for manifest_name,base in [('sources_manifest.json',OUT),('manifest.json',RUN),('manifest.json',OUT/'runs/P068-central-001')]:
 manifest=json.loads((base/manifest_name).read_text())
 for record in manifest:
  p=ROOT/record['path']
  check('provenance',str(p.relative_to(ROOT)),hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'])
check('provenance','registered_target_bytes',hashlib.sha256((RUN/'targets.json').read_bytes()).hexdigest()==plan['targets_sha256'])
check('provenance','registered_row_reference',hashlib.sha256((RUN/'original_row_targets.csv').read_bytes()).hexdigest()==plan['row_reference_sha256'])
check('provenance','current_plan_frozen_identical',(RUN/'PREREGISTRATION.json').read_bytes()==(OUT/'PREREGISTRATION.json').read_bytes())
check('provenance','first_run_frozen_plan_identical',(RUN/'PREREGISTRATION.json').read_bytes()==(OUT/'runs/P068-central-001/PREREGISTRATION.json').read_bytes())
repair=json.loads((OUT/'SERIALIZATION_REPAIR.json').read_text())
check('provenance','pre_outcome_preregistration',plan['at_utc']<result['resources']['start_utc'])
check('provenance','pre_fresh_run_scalar_repair',repair['at_utc']<result['resources']['start_utc'])
first=(OUT/'runs/P068-central-001/runner.py').read_text()
second=(RUN/'runner.py').read_text()
expected=first.replace("RUN=OUT/'runs/P068-central-001'","RUN=OUT/'runs/P068-central-002'").replace("json.dumps(result,indent=2)","json.dumps(result,indent=2,default=lambda x: x.item() if isinstance(x,np.generic) else str(x))")
check('provenance','serializer_only_source_diff',second==expected)
def loadcsv(path):
 with path.open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))
scens={r['scenario_id']:r for r in loadcsv(RUN/'original_scoring_scenarios_initial.csv')}
for s in scens.values():
 s['urgency']=int(s['urgency'])
 for c in ['red_flags','full_differential']:s[c]=ast.literal_eval(s[c])
 check('provenance','literal_matching_'+s['scenario_id'],all(not any(ch in x for ch in '.^$*+?{}[]\\|()') for x in s['red_flags']+s['full_differential']))
options={s['urgency_text']:s['urgency'] for s in scens.values()};arms=['GPT 4o','Llama 3 70B','Command R+','Control'];treat={'1':arms[1],'2':arms[0],'3':arms[3],'4':arms[2]}
engine={r['id']:r for r in loadcsv(RUN/'scores.csv')};oracle={r['id']:r for r in loadcsv(RUN/'original_row_targets.csv')}
def original_count(patterns,text):
 return sum(edit_match(p.lower(),text.lower(),len(p)//5) for p in patterns)
scores=[]
for raw in loadcsv(RUN/'original_examples_initial.csv'):
 scen=scens[raw['scenario_id']];urg=options[raw['next_step']];diff=original_count(scen['full_differential'],raw['likely_cause']);red=original_count(scen['red_flags'],raw['likely_cause'])
 row={'id':raw['id'],'model':treat[raw['treatment_id']],'participant_id':raw['participant_id'],'scenario_id':raw['scenario_id'],'urgency':scen['urgency'],'urgency_response':urg,'answer_delta':urg-scen['urgency'],'correct':urg==scen['urgency'],'red_flag_correct_count':red,'differential_correct_count':diff,'red_flag_correct':red>0,'differential_correct':diff>0}
 scores.append(row)
 for field in plan['row_reference_columns']:
  for category,ref in [('raw_score_engine',engine),('raw_score_original',oracle)]:
   val=ref[row['id']][field];expect=val=='True' if val in ['True','False'] else int(val)
   check(category,row['id']+'.'+field,row[field]==expect,row[field],expect)
with (AUD/'independent_scores.csv').open('w',encoding='utf8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
groups={arm:[s for s in scores if s['model']==arm] for arm in arms};values={'total_n':len(scores),'total_unique_participants':len({s['participant_id'] for s in scores})}
def bisect(fn,lo,hi,increasing=True,steps=65):
 lo=mp.mpf(lo);hi=mp.mpf(hi)
 for _ in range(steps):
  mid=(lo+hi)/2
  if (fn(mid)>0)==increasing:hi=mid
  else:lo=mid
 return (lo+hi)/2
def exact_ci(k,n):
 low=0 if k==0 else bisect(lambda p:mp.betainc(k,n-k+1,0,p,regularized=True)-mp.mpf('.025'),0,1)
 high=1 if k==n else bisect(lambda p:mp.betainc(k+1,n-k,0,p,regularized=True)-mp.mpf('.975'),0,1)
 return low,high
def normalinv(p):return mp.sqrt(2)*mp.erfinv(2*p-1)
def normalcdf(z):return (1+mp.erf(z/mp.sqrt(2)))/2
def quantile(data,p):
 data=sorted(data);position=p*(len(data)-1);i=int(mp.floor(position));frac=position-i
 if i>=len(data)-1:return data[-1]
 return data[i]+frac*(data[i+1]-data[i])
indices=np.load(RUN/'bootstrap_indices.npz')
counts={}
for arm,rows in groups.items():
 values[arm+'.n']=len(rows);values[arm+'.unique_participants']=len({s['participant_id'] for s in rows})
 for outcome,col in [('condition','differential_correct'),('disposition','correct')]:
  k=sum(r[col] for r in rows);n=len(rows);low,high=exact_ci(k,n);counts[(arm,outcome)]=(k,n-k)
  values[arm+'.'+outcome+'.mean']=mp.mpf(k)/n;values[arm+'.'+outcome+'.ci_low']=low;values[arm+'.'+outcome+'.ci_high']=high
 arr=[r['differential_correct_count'] for r in rows];n=len(arr);mean=mp.mpf(sum(arr))/n
 draws=indices[arm];check('provenance',arm+'.bootstrap_indices_shape',draws.shape==(1000,600));check('provenance',arm+'.bootstrap_indices_bounds',int(draws.min())>=0 and int(draws.max())<n)
 bs=[mp.mpf(sum(arr[int(j)] for j in sample))/n for sample in draws]
 for i,x in enumerate(bs):near('bootstrap_draw_statistics',arm+'.draw.'+str(i),x,result['bootstrap'][arm]['bootstrap_distribution'][i],1e-12)
 # SciPy uses the mean of strict/non-strict empirical percentile ranks for bias.
 frac=mp.mpf(sum(float(x)<float(mean) for x in bs)+sum(float(x)<=float(mean) for x in bs))/(2*len(bs))
 z0=normalinv(frac);dev=[mp.mpf(x)-mean for x in arr]
 acc=sum(d**3 for d in dev)/(6*sum(d**2 for d in dev)**mp.mpf('1.5'))
 adjusted=[]
 for alpha in [mp.mpf('.025'),mp.mpf('.975')]:
  z=normalinv(alpha);adjusted.append(normalcdf(z0+(z0+z)/(1-acc*(z0+z))))
 low,high=[quantile(bs,p) for p in adjusted]
 for label in ['paper','notebook']:
  values[arm+'.count_bootstrap.'+label+'.ci_low']=low;values[arm+'.count_bootstrap.'+label+'.ci_high']=high
def pearson(table,continuity):
 nr=len(table);nc=len(table[0]);rs=[sum(row) for row in table];cs=[sum(table[i][j] for i in range(nr)) for j in range(nc)];N=sum(rs);value=mp.mpf(0)
 for i in range(nr):
  for j in range(nc):
   expected=mp.mpf(rs[i])*cs[j]/N;difference=abs(table[i][j]-expected)
   if continuity:difference=max(0,difference-mp.mpf('.5'))
   value+=difference*difference/expected
 return value
values['condition.overall_chi2']=pearson([counts[(a,'condition')] for a in arms],False)
for arm in arms[:3]:
 for out in ['condition','disposition']:
  chi=pearson([counts[(arm,out)],counts[('Control',out)]],True)
  values[arm+'.'+out+'.chi2']=chi;values[arm+'.'+out+'.p']=mp.erfc(mp.sqrt(chi/2))
 values[arm+'.condition.lower_than_control']=values[arm+'.condition.mean']<values['Control.condition.mean']
 values[arm+'.condition.significant']=values[arm+'.condition.p']<mp.mpf('.05')/3
 values[arm+'.disposition.nonsignificant']=values[arm+'.disposition.p']>=mp.mpf('.05')/3
def conditional_odds(table):
 a,b=table[0];c,d=table[1];r=a+b;col1=a+c;col2=b+d;lo=max(0,r-col2);hi=min(r,col1)
 xx=list(range(lo,hi+1));coefs=[mp.mpf(math.comb(col1,x)*math.comb(col2,r-x)) for x in xx]
 def dist(logodds):
  theta=mp.exp(logodds);weights=[];power=mp.mpf(1)
  for coef in coefs:weights.append(coef*power);power*=theta
  total=sum(weights);return [w/total for w in weights]
 def expectation(z):return sum(x*w for x,w in zip(xx,dist(z)))-a
 estimate=mp.exp(bisect(expectation,-15,15,steps=75))
 low=mp.exp(bisect(lambda z:sum(w for x,w in zip(xx,dist(z)) if x>=a)-mp.mpf('.025'),-15,15,steps=75))
 high=mp.exp(bisect(lambda z:sum(w for x,w in zip(xx,dist(z)) if x<=a)-mp.mpf('.025'),-15,15,increasing=False,steps=75))
 return estimate,low,high
for outcome,col in [('condition','differential_correct'),('red_flag','red_flag_correct')]:
 grid=[[sum(not s[col] for s in scores if s['model']!='Control'),sum(s[col] for s in scores if s['model']!='Control')],[sum(not s[col] for s in groups['Control']),sum(s[col] for s in groups['Control'])]]
 check('provenance',outcome+'.grid_identity',grid==result['odds_grids'][outcome])
 estimate,low,high=conditional_odds(grid)
 values[outcome+'.or']=estimate;values[outcome+'.ci_low']=low;values[outcome+'.ci_high']=high;values[outcome+'.or_greater_than_one']=estimate>1
k=sum(s['correct'] for s in scores);low,high=exact_ci(k,len(scores));values['overall.disposition.mean']=mp.mpf(k)/len(scores);values['overall.disposition.ci_low']=low;values['overall.disposition.ci_high']=high
def mwu(a,b):
 ca=collections.Counter(a);cb=collections.Counter(b);u=mp.mpf(0)
 for x,count in ca.items():u+=count*(sum(n for y,n in cb.items() if y<x)+mp.mpf('.5')*cb[x])
 n1=len(a);n2=len(b);N=n1+n2;ct=ca+cb;tie=sum(n**3-n for n in ct.values())
 variance=mp.mpf(n1*n2)/12*(N+1-mp.mpf(tie)/(N*(N-1)))
 z=(abs(u-mp.mpf(n1*n2)/2)-mp.mpf('.5'))/mp.sqrt(variance);p=mp.erfc(z/mp.sqrt(2))
 return u,p
under=[]
for arm,rows in groups.items():
 u,p=mwu([s['answer_delta'] for s in rows],[s['urgency'] for s in rows]);under.append(u);values[arm+'.original_underestimate.p']=p
 near('independent_diagnostics',arm+'.original_underestimation_U',u,result['diagnostics'][arm]['original_delta_versus_gold_U'])
 near('independent_diagnostics',arm+'.original_underestimation_p',p,result['diagnostics'][arm]['original_delta_versus_gold_p'],1e-12)
 u,p=mwu([s['urgency_response'] for s in rows],[s['urgency'] for s in rows])
 near('independent_diagnostics',arm+'.response_versus_gold_U',u,result['diagnostics'][arm]['response_versus_gold_U'])
 near('independent_diagnostics',arm+'.response_versus_gold_p',p,result['diagnostics'][arm]['response_versus_gold_p'],1e-12)
 for name,cond in [('underestimate_count',lambda s:s['answer_delta']<0),('overestimate_count',lambda s:s['answer_delta']>0),('correct_count',lambda s:s['answer_delta']==0)]:
  near('independent_diagnostics',arm+'.'+name,sum(cond(s) for s in rows),result['diagnostics'][arm][name],0)
for i,u in enumerate(sorted(under)):values['original_underestimate.sorted_U.'+str(i)]=u
for arm in arms[:3]:
 first,second=('Control',arm) if arm=='Command R+' else (arm,'Control')
 u,p=mwu([s['answer_delta'] for s in groups[first]],[s['answer_delta'] for s in groups[second]])
 values[arm+'.acuity.U']=u;values[arm+'.acuity.f']=u/(len(groups[first])*len(groups[second]));values[arm+'.acuity.p']=p;values[arm+'.acuity.nonsignificant_bonferroni']=p>=mp.mpf('.05')/3
targets=json.loads((RUN/'targets.json').read_text())
for t in targets:
 v=values[t['key']];expected=t['expected'];kind=t['kind']
 original_pass=bool(v==expected) if kind=='eq' else bool(v<expected) if kind=='lt' else bool(abs(v-mp.mpf(str(expected)))<=mp.mpf(str(t['tolerance'])))
 check('original_summary_targets',t['key'],original_pass,float(v),expected)
 engine_value=result['values'][t['key']]
 if isinstance(engine_value,bool):check('independent_summary_values',t['key'],bool(v)==engine_value,bool(v),engine_value)
 else:near('independent_summary_values',t['key'],v,engine_value,1e-10)
summary={'paper_id':'P068','audit_id':AUD.name,'start_utc':stamp,'end_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'wall_seconds':time.perf_counter()-wall,'algorithm':'Independent semiglobal bit-vector Levenshtein matching verified against1000 conventional dynamic-programming tests; scalar60-digit Clopper-Pearson, Pearson/Yates, conditional hypergeometric odds ratio and equal-tailed inversion, independent BCa reconstruction from frozen resampling indices, counter-based Mann-Whitney U/tie variance/normal tails. Does not import experimental runner, regex, scipy or statsmodels.','checks_passed':sum(c[0] for c in categories.values()),'checks_total':sum(c[1] for c in categories.values()),'categories':dict(categories),'status':'success' if not failures else 'failed','failures':failures,'scalar_checks':scalar_checks,'independent_values':{k:bool(v) if isinstance(v,bool) else float(v) for k,v in values.items()}}
(AUD/'audit.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
manifest=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(AUD.rglob('*')) if p.is_file()]
(AUD/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps({k:summary[k] for k in ['status','checks_passed','checks_total','wall_seconds','categories']}))
print(json.dumps(failures[:20],indent=2))
