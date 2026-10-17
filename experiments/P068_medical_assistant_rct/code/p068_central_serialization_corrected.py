import os
for var in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[var]='1'
import pathlib,json,csv,ast,shutil,hashlib,datetime as dt,time,platform,sys
import numpy as np,regex,scipy
from scipy import stats
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'papers/P068_medical_assistant_rct';RUN=OUT/'runs/P068-central-002'
assert not RUN.exists();RUN.mkdir(parents=True)
start=dt.datetime.now(dt.timezone.utc);wall=time.perf_counter();cpu=time.process_time()
for name in ['PREREGISTRATION.json','PREREGISTRATION.md','targets.json','original_row_targets.csv','sources_manifest.json']:shutil.copyfile(OUT/name,RUN/name)
shutil.copyfile(__file__,RUN/'runner.py')
for name in ['original_examples_initial.csv','original_scoring_scenarios_initial.csv']:shutil.copyfile(OUT/'sources'/name,RUN/name)
plan=json.loads((RUN/'PREREGISTRATION.json').read_text());assert start.isoformat()>plan['at_utc']
assert hashlib.sha256((RUN/'targets.json').read_bytes()).hexdigest()==plan['targets_sha256']
scens={}
with (RUN/'original_scoring_scenarios_initial.csv').open(encoding='utf8',newline='') as f:
 for row in csv.DictReader(f):
  row['urgency']=int(row['urgency'])
  for col in ['full_differential','red_flags']:row[col]=ast.literal_eval(row[col])
  scens[row['scenario_id']]=row
urgency_map={s['urgency_text']:s['urgency'] for s in scens.values()}
arms=['GPT 4o','Llama 3 70B','Command R+','Control']
treatmap={'1':'Llama 3 70B','2':'GPT 4o','3':'Control','4':'Command R+'}
cache={}
def fuzzy_count(targets,text):
 text=text.lower()
 return sum(regex.search('('+target.lower()+'){e<='+str(20*len(target)//100)+'}',text) is not None for target in targets)
scores=[]
with (RUN/'original_examples_initial.csv').open(encoding='utf8',newline='') as f:
 for raw in csv.DictReader(f):
  sc=scens[raw['scenario_id']];text=raw['likely_cause']
  diff=fuzzy_count(sc['full_differential'],text);red=fuzzy_count(sc['red_flags'],text)
  urg=urgency_map[raw['next_step']]
  scores.append({'id':raw['id'],'participant_id':raw['participant_id'],'scenario_id':raw['scenario_id'],'model':treatmap[raw['treatment_id']],'urgency_response':urg,'urgency':sc['urgency'],'answer_delta':urg-sc['urgency'],'correct':urg==sc['urgency'],'red_flag_correct_count':red,'differential_correct_count':diff,'red_flag_correct':red>0,'differential_correct':diff>0})
with (RUN/'scores.csv').open('w',encoding='utf8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
# Comparison oracle is opened only after every score has been independently generated.
with (RUN/'original_row_targets.csv').open(encoding='utf8',newline='') as f:reference={r['id']:r for r in csv.DictReader(f)}
row_fail=[]
assert set(reference)=={s['id'] for s in scores}
for s in scores:
 for col in plan['row_reference_columns']:
  raw=reference[s['id']][col];expect=raw=='True' if raw in ['True','False'] else int(raw)
  if s[col]!=expect:row_fail.append({'id':s['id'],'field':col,'expected':expect,'actual':s[col]})
groups={arm:[s for s in scores if s['model']==arm] for arm in arms}
values={'total_n':len(scores),'total_unique_participants':len({s['participant_id'] for s in scores})}
counts={};boot_indices={};boot_details={}
rng=np.random.default_rng(plan['bootstrap_seed'])
for arm,rows in groups.items():
 values[arm+'.n']=len(rows);values[arm+'.unique_participants']=len({s['participant_id'] for s in rows})
 for out,col in [('condition','differential_correct'),('disposition','correct')]:
  arr=np.array([s[col] for s in rows],dtype=int);n=len(arr);k=int(arr.sum());counts[(arm,out)]=(k,n-k)
  ci=stats.binomtest(k,n).proportion_ci(.95,method='exact')
  values.update({arm+'.'+out+'.mean':k/n,arm+'.'+out+'.ci_low':ci.low,arm+'.'+out+'.ci_high':ci.high})
 arr=np.array([s['differential_correct_count'] for s in rows],dtype=float);captured=[]
 def mean_by_indices(indices,axis=-1):
  if indices.ndim==2 and indices.shape==(1000,600):captured.append(indices.copy())
  return arr[indices].mean(axis=axis)
 bs=stats.bootstrap((np.arange(len(arr)),),mean_by_indices,vectorized=True,n_resamples=plan['bootstrap_resamples'],rng=rng,method='BCa',confidence_level=.95)
 assert len(captured)==1;boot_indices[arm]=captured[0]
 boot_details[arm]={'sample_mean':float(arr.mean()),'bootstrap_distribution':bs.bootstrap_distribution.tolist(),'ci_low':float(bs.confidence_interval.low),'ci_high':float(bs.confidence_interval.high)}
 for label in ['paper','notebook']:
  values[arm+'.count_bootstrap.'+label+'.ci_low']=float(bs.confidence_interval.low);values[arm+'.count_bootstrap.'+label+'.ci_high']=float(bs.confidence_interval.high)
np.savez_compressed(RUN/'bootstrap_indices.npz',**boot_indices)
all_cond=np.array([counts[(a,'condition')] for a in arms]);values['condition.overall_chi2']=float(stats.chi2_contingency(all_cond).statistic)
for arm in arms[:3]:
 for out in ['condition','disposition']:
  result=stats.chi2_contingency([counts[(arm,out)],counts[('Control',out)]])
  values[arm+'.'+out+'.chi2']=float(result.statistic);values[arm+'.'+out+'.p']=float(result.pvalue)
 values[arm+'.condition.lower_than_control']=values[arm+'.condition.mean']<values['Control.condition.mean']
 values[arm+'.condition.significant']=values[arm+'.condition.p']<.05/3
 values[arm+'.disposition.nonsignificant']=values[arm+'.disposition.p']>=.05/3
# Equivalent to original pandas crosstab: rows False(LLM)/True(Control); columns False/True outcome.
odds_grids={}
for outcome,col in [('condition','differential_correct'),('red_flag','red_flag_correct')]:
 grid=[[sum(not s[col] for s in scores if s['model']!='Control'),sum(s[col] for s in scores if s['model']!='Control')],[sum(not s[col] for s in groups['Control']),sum(s[col] for s in groups['Control'])]]
 odds_grids[outcome]=grid;rr=stats.contingency.odds_ratio(grid);ci=rr.confidence_interval()
 values[outcome+'.or']=float(rr.statistic);values[outcome+'.ci_low']=float(ci.low);values[outcome+'.ci_high']=float(ci.high);values[outcome+'.or_greater_than_one']=rr.statistic>1
totalcorrect=sum(s['correct'] for s in scores);ci=stats.binomtest(totalcorrect,len(scores)).proportion_ci(.95,method='exact')
values['overall.disposition.mean']=totalcorrect/len(scores);values['overall.disposition.ci_low']=ci.low;values['overall.disposition.ci_high']=ci.high
under_U=[];diagnostics={}
for arm,rows in groups.items():
 delta=[s['answer_delta'] for s in rows];gold=[s['urgency'] for s in rows];response=[s['urgency_response'] for s in rows]
 original=stats.mannwhitneyu(delta,gold,alternative='two-sided',method='asymptotic',use_continuity=True)
 under_U.append(float(original.statistic));values[arm+'.original_underestimate.p']=float(original.pvalue)
 correct_test=stats.mannwhitneyu(response,gold,alternative='two-sided',method='asymptotic',use_continuity=True)
 diagnostics[arm]={'original_delta_versus_gold_U':float(original.statistic),'original_delta_versus_gold_p':float(original.pvalue),'response_versus_gold_U':float(correct_test.statistic),'response_versus_gold_p':float(correct_test.pvalue),'underestimate_count':sum(s['answer_delta']<0 for s in rows),'overestimate_count':sum(s['answer_delta']>0 for s in rows),'correct_count':sum(s['answer_delta']==0 for s in rows)}
for i,u in enumerate(sorted(under_U)):values['original_underestimate.sorted_U.'+str(i)]=u
for arm in arms[:3]:
 first,second=('Control',arm) if arm=='Command R+' else (arm,'Control')
 result=stats.mannwhitneyu([s['answer_delta'] for s in groups[first]],[s['answer_delta'] for s in groups[second]],alternative='two-sided',method='asymptotic',use_continuity=True)
 values[arm+'.acuity.U']=float(result.statistic);values[arm+'.acuity.f']=result.statistic/(len(groups[first])*len(groups[second]));values[arm+'.acuity.p']=float(result.pvalue);values[arm+'.acuity.nonsignificant_bonferroni']=result.pvalue>=.05/3
targets=json.loads((RUN/'targets.json').read_text());checks=[]
for target in targets:
 actual=values[target['key']];kind=target['kind'];expect=target['expected'];tol=target['tolerance']
 passed=(actual==expect) if kind=='eq' else (actual<expect) if kind=='lt' else (abs(actual-expect)<=tol)
 checks.append({**target,'actual':actual,'passed':bool(passed),'absolute_error':None if kind!='abs' else abs(actual-expect)})
end=dt.datetime.now(dt.timezone.utc)
performance={'start_utc':start.isoformat(),'end_utc':end.isoformat(),'wall_seconds':time.perf_counter()-wall,'cpu_seconds':time.process_time()-cpu,'peak_working_set_bytes':getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss),'gpu':False,'paid_api_calls':0,'spend':0,'numerical_threads':1,'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'regex':regex.__version__}
result={'paper_id':'P068','run_id':RUN.name,'status':'success' if all(c['passed'] for c in checks) and not row_fail else 'failed','summary_checks_passed':sum(c['passed'] for c in checks),'summary_checks_total':len(checks),'row_checks_passed':len(scores)*len(plan['row_reference_columns'])-len(row_fail),'row_checks_total':len(scores)*len(plan['row_reference_columns']),'row_failures':row_fail,'summary_checks':checks,'values':values,'odds_grids':odds_grids,'bootstrap':boot_details,'diagnostics':diagnostics,'resources':performance}
(RUN/'results.json').write_text(json.dumps(result,indent=2,default=lambda x: x.item() if isinstance(x,np.generic) else str(x)),encoding='utf8')
manifest=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(RUN.rglob('*')) if p.is_file()]
(RUN/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(json.dumps({k:result[k] for k in ['status','summary_checks_passed','summary_checks_total','row_checks_passed','row_checks_total']}))
print(json.dumps([c for c in checks if not c['passed']],indent=2))
print(json.dumps(row_fail[:20],indent=2))
print(json.dumps(performance))
