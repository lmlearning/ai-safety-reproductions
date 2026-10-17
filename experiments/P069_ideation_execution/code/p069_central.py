"""P069 central human-review analysis, original methods, no source runner import."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import pathlib,json,hashlib,datetime,time,shutil,collections,platform
import numpy as np
from scipy import stats
import scipy,psutil
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'papers/P069_ideation_execution'
RUN=ROOT/'runs/P069-central-001';RUN.mkdir()
start=datetime.datetime.now(datetime.timezone.utc).isoformat();wall=time.perf_counter();cpu=time.process_time()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,default=lambda z:z.item() if isinstance(z,np.generic) else str(z)),encoding='utf8')
plan=json.loads((P/'PREREGISTRATION.json').read_text(encoding='utf8'))
assert start>plan['at_utc'];assert sha(P/'targets.json')==plan['targets_sha256'];assert sha(P/'sources_manifest.json')==plan['sources_manifest_sha256']
for name in ['PREREGISTRATION.json','PREREGISTRATION.md','targets.json','sources_manifest.json']:shutil.copyfile(P/name,RUN/name)
shutil.copyfile(__file__,RUN/'runner.py')
for rel in plan['raw_inputs']:shutil.copyfile(P/rel,RUN/pathlib.Path(rel).name)
frozen_sources=json.loads((P/'sources_manifest.json').read_text(encoding='utf8'))
assert all(sha(P/s['path'])==s['sha256'] for s in frozen_sources)
dump(RUN/'source_verification.json',frozen_sources)
pre=json.loads((RUN/'ideation_reviews_initial.json').read_text(encoding='utf8'))
post=json.loads((RUN/'execution_reviews_initial.json').read_text(encoding='utf8'))
def records(d):
 assert len(set(map(len,d.values())))==1
 return [dict(zip(d,(d[k][i] for k in d))) for i in range(len(d['idea_id']))]
before=records(pre);after=records(post);common=set(pre['idea_id'])&set(post['idea_id'])
assert common==set(post['idea_id']);assert len(common)==43;assert len(after)==181
M=['novelty','excitement','effectiveness','overall'];ALL=['novelty','excitement','soundness','effectiveness','overall','faithfulness','codebase']
def field(m):return 'codebase_quality' if m=='codebase' else m+'_score'
def col(rs,m):return np.array([float(r[field(m)]) for r in rs],dtype=float)
def bh(ps):
 p=np.array(ps);idx=np.argsort(p);out=np.empty(len(p));out[idx]=np.minimum(1,np.minimum.accumulate((p[idx]*len(p)/np.arange(1,len(p)+1))[::-1])[::-1]);return out
def welch(x,y,alt='two-sided'):
 a=stats.ttest_ind(x,y,equal_var=False,alternative=alt)
 return {'t':float(a.statistic),'p_raw':float(a.pvalue),'df':float(a.df)}
V={};D={'review':{},'idea':{},'gap':{},'correlation':{},'per_project':[]}
def means(rs):
 out={}
 for i in sorted(common):
  rr=[r for r in rs if r['idea_id']==i]
  if rr:out[i]={'condition':rr[0]['condition'],'topic':rr[0]['topic'],'n':len(rr),**{m:float(np.mean(col(rr,m))) for m in M}}
 return out
pr=means(before);po=means(after)
for i in sorted(common):
 assert pr[i]['condition']==po[i]['condition']
 D['per_project'].append({'idea_id':i,'condition':po[i]['condition'],'topic':po[i]['topic'],'pre_reviews':pr[i]['n'],'post_reviews':po[i]['n'],'pre':{m:pr[i][m] for m in M},'post':{m:po[i][m] for m in M},'gap':{m:po[i][m]-pr[i][m] for m in M}})
for group in ['Human','AI']:
 rr=[r for r in after if r['condition']==group];ii=[i for i in common if po[i]['condition']==group]
 V['reviews.'+group]=len(rr);V['projects.'+group]=len(ii)
 for topic in ['Bias','Coding','Safety','Multilingual','Factuality','Math','Uncertainty']:
  V['topic.'+topic+'.'+group]=sum(str(po[i]['topic']).lower()==topic.lower() for i in ii)
V['reviews.total']=len(after);V['projects.total']=len(common);V['matched.projects']=len(common)
p_main=[]
for m in ALL:
 x=col([r for r in after if r['condition']=='AI'],m);y=col([r for r in after if r['condition']=='Human'],m);w=welch(x,y,'less');D['review'][m]=w
 for group,z in [('Human',y),('AI',x)]:
  sd=float(np.std(z));mean=float(np.mean(z));ci=float(stats.t.ppf(.975,len(z)-1)*sd/np.sqrt(len(z)))
  V['review.'+m+'.'+group+'.mean']=mean;V['review.'+m+'.'+group+'.sd']=sd
  D['review'][m][group]={'n':len(z),'mean':mean,'sd':sd,'median':float(np.median(z)),'min':float(min(z)),'max':float(max(z)),'ci95':[mean-ci,mean+ci],'raw_scores':z.tolist()}
 if m in ALL[:5]:p_main.append(w['p_raw'])
for m,p in zip(ALL[:5],bh(p_main)):D['review'][m]['p_FDR']=float(p)
for m in ALL:
 p=D['review'][m]['p_FDR'] if m in ALL[:5] else D['review'][m]['p_raw']
 V['review.'+m+'.p']=p;V['claim.review.'+m+'.significant']=bool(p<.05)
for m,p in zip(ALL[5:],bh([D['review'][m]['p_raw'] for m in ALL[5:]])):D['review'][m]['source_control_script_adjusted_p']=float(p)
for phase,agg in [('pre',pr),('post',po)]:
 ps=[]
 for m in M:
  a=np.array([agg[i][m] for i in sorted(common) if po[i]['condition']=='AI']);h=np.array([agg[i][m] for i in sorted(common) if po[i]['condition']=='Human'])
  w=welch(a,h);D['idea'][phase+'.'+m]=w;ps.append(w['p_raw'])
  V['idea.'+m+'.'+phase+'.Human']=float(np.mean(h));V['idea.'+m+'.'+phase+'.AI']=float(np.mean(a))
 for m,p in zip(M,bh(ps)):
  V['idea.'+m+'.'+phase+'.p']=float(p);V['claim.idea.'+m+'.'+phase+'.significant']=bool(p<.05)
for m in M:V['claim.idea.'+m+'.ranking.flip']=bool(V['idea.'+m+'.pre.AI']>V['idea.'+m+'.pre.Human'] and V['idea.'+m+'.post.AI']<V['idea.'+m+'.post.Human'])
for variant in ['full','exclude6']:
 ids=sorted(common-set(plan['exclude6_only_for_original_robustness'])) if variant=='exclude6' else sorted(common)
 ps=[]
 for m in M:
  h=np.array([po[i][m]-pr[i][m] for i in ids if po[i]['condition']=='Human']);a=np.array([po[i][m]-pr[i][m] for i in ids if po[i]['condition']=='AI'])
  w=welch(h,a,'greater');D['gap'][variant+'.'+m]={**w,'Human':h.tolist(),'AI':a.tolist()};ps.append(w['p_raw'])
  V['gap.'+variant+'.'+m+'.Human']=float(np.mean(h));V['gap.'+variant+'.'+m+'.AI']=float(np.mean(a));V['gap.'+variant+'.'+m+'.difference']=float(np.mean(h)-np.mean(a))
 for m,p in zip(M,bh(ps)):V['gap.'+variant+'.'+m+'.p']=float(p);V['claim.gap.'+variant+'.'+m+'.significant']=bool(p<.05)
for group in ['Human','AI']:
 ids=sorted(i for i in common if po[i]['condition']==group)
 for m in M:
  x=[pr[i][m] for i in ids];y=[po[i][m] for i in ids]
  for method,fn in [('pearson',stats.pearsonr),('spearman',stats.spearmanr)]:
   corr,p=fn(x,y);V['correlation.'+group+'.'+method+'.'+m]=float(corr);D['correlation'][group+'.'+method+'.'+m]={'coefficient':float(corr),'p_raw':float(p),'n':len(ids)}
checks=[]
for t in json.loads((RUN/'targets.json').read_text(encoding='utf8')):
 actual=V[t['key']];ok=(actual==t['expected']) if t['absolute_tolerance']==0 else abs(actual-t['expected'])<=t['absolute_tolerance']
 checks.append({**t,'actual':actual,'pass':bool(ok)})
dump(RUN/'results.json',{'values':V,'details':D,'checks':checks,'all_pass':all(c['pass'] for c in checks),'passed':sum(c['pass'] for c in checks),'total':len(checks)})
usage={'started_at_utc':start,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.perf_counter()-wall,'cpu_seconds':time.process_time()-cpu,'peak_working_set_bytes':getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss),'numeric_threads':1,'gpu':False,'paid_api_calls':0,'usd_spend':0,'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}
dump(RUN/'resource_usage.json',usage)
dump(RUN/'manifest.json',[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(RUN.iterdir()) if p.is_file()])
print(json.dumps({'passed':sum(c['pass'] for c in checks),'total':len(checks),'failures':[c for c in checks if not c['pass']],'resources':usage},default=lambda z:z.item() if isinstance(z,np.generic) else str(z)))
