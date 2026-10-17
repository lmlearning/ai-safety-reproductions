"""Independent scalar exact-sum audit of P069; no experiment, NumPy or SciPy import."""
import pathlib,json,hashlib,datetime,time,math,collections,statistics
from fractions import Fraction as F
import mpmath as mp
mp.mp.dps=70
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'papers/P069_ideation_execution';R=ROOT/'runs/P069-central-001'
A=ROOT/'audits/P069-audit-002';A.mkdir(parents=True);start=time.perf_counter()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
checks=[]
def check(name,ok,detail=None):checks.append({'check':name,'pass':bool(ok),'detail':detail})
def near(name,x,y,tol=mp.mpf('1e-11')):check(name,abs(mp.mpf(str(x))-mp.mpf(str(y)))<=tol,{'independent':str(x),'experiment':str(y),'tolerance':str(tol)})
plan=read(P/'PREREGISTRATION.json');run=read(R/'results.json')
for s in read(P/'sources_manifest.json'):check('source:'+s['path'],sha(P/s['path'])==s['sha256'])
for e in read(R/'manifest.json'):check('run-file:'+e['path'],sha(R/e['path'])==e['sha256'])
for f in ['PREREGISTRATION.json','PREREGISTRATION.md','targets.json','sources_manifest.json']:check('frozen:'+f,sha(P/f)==sha(R/f))
for f in ['execution_reviews_initial.json','ideation_reviews_initial.json']:check('raw-input:'+f,sha(P/'sources'/f)==sha(R/f))
check('prereg-target-hash',plan['targets_sha256']==sha(R/'targets.json'))
check('prereg-source-hash',plan['sources_manifest_sha256']==sha(R/'sources_manifest.json'))
usage=read(R/'resource_usage.json')
check('prospective-timing',plan['at_utc']<usage['started_at_utc'])
check('CPU-only-zero-cost',not usage['gpu'] and usage['paid_api_calls']==0 and usage['usd_spend']==0)
release=read(P/'sources/first_release_tree_evidence.json')
check('no-preexisting-execution-files',release['parent_execution_files']=='')
check('first-commit-execution-file-present','reviews_execution/data_points_all_execution.json' in release['first_execution_files'])
citation=read(P/'sources/citation_snapshot.json')
check('citation-gate',citation['paper']['citationCount']>=40 and citation['paper']['externalIds']['ArXiv']=='2506.20803')
check('raw-citation-hash',sha(P/'sources/citation_query_raw.json')==citation['retrieval']['sha256'])
def unpack(d):
 names=tuple(d.keys());n=len(d['idea_id']);assert all(len(d[k])==n for k in names)
 return tuple(tuple(d[k][j] for k in names) for j in range(n)),{k:i for i,k in enumerate(names)}
p,pi=unpack(read(R/'ideation_reviews_initial.json'));q,qi=unpack(read(R/'execution_reviews_initial.json'))
ids=sorted(set(z[qi['idea_id']] for z in q));pre_ids=set(z[pi['idea_id']] for z in p)
check('complete-intersection',set(ids)<=pre_ids and len(ids)==43 and len(q)==181)
M=['novelty','excitement','effectiveness','overall'];ALL=['novelty','excitement','soundness','effectiveness','overall','faithfulness','codebase']
def field(m):return 'codebase_quality' if m=='codebase' else m+'_score'
def frac(v):return F(str(v))
def m(v):return mp.mpf(v.numerator)/v.denominator if isinstance(v,F) else mp.mpf(v)
def avg(x):return sum(x,F(0))/len(x)
def var(x,ddof):u=avg(x);return sum(((z-u)**2 for z in x),F(0))/(len(x)-ddof)
def tprob(t,df,side):
 tail=mp.betainc(df/2,mp.mpf('.5'),0,df/(df+t*t),regularized=True)/2
 lower=tail if t<0 else 1-tail
 return lower if side=='less' else 1-lower if side=='greater' else 2*tail
def welch(x,y,side='two-sided'):
 ax=var(x,1)/len(x);ay=var(y,1)/len(y);df=(ax+ay)**2/(ax**2/(len(x)-1)+ay**2/(len(y)-1));t=m(avg(x)-avg(y))/mp.sqrt(m(ax+ay))
 return {'t':t,'df':m(df),'p_raw':tprob(t,m(df),side)}
def adjust(ps):
 order=sorted(range(len(ps)),key=lambda j:ps[j]);r=[None]*len(ps);minimum=mp.mpf(1)
 for k in range(len(ps),0,-1):
  j=order[k-1];minimum=min(minimum,ps[j]*len(ps)/k);r[j]=minimum
 return r
def correlate(x,y):
 a=avg(x);b=avg(y);num=sum(((u-a)*(v-b) for u,v in zip(x,y)),F(0));den=mp.sqrt(m(sum(((u-a)**2 for u in x),F(0)))*m(sum(((v-b)**2 for v in y),F(0))))
 return m(num)/den
def ranks(x):
 order=sorted(range(len(x)),key=lambda j:x[j]);r=[F(0)]*len(x);lo=0
 while lo<len(x):
  hi=lo+1
  while hi<len(x) and x[order[hi]]==x[order[lo]]:hi+=1
  for j in order[lo:hi]:r[j]=F(lo+1+hi,2)
  lo=hi
 return r
groups={i:next(z[qi['condition']] for z in q if z[qi['idea_id']]==i) for i in ids}
topics={i:next(z[qi['topic']] for z in q if z[qi['idea_id']]==i) for i in ids}
def project(data,idx):
 out={}
 for i in ids:
  rr=[z for z in data if z[idx['idea_id']]==i]
  out[i]={k:avg([frac(z[idx[field(k)]]) for z in rr]) for k in M}
 return out
pre=project(p,pi);post=project(q,qi);V={}
for g in ['Human','AI']:
 V['reviews.'+g]=sum(z[qi['condition']]==g for z in q);V['projects.'+g]=sum(groups[i]==g for i in ids)
 for topic in ['Bias','Coding','Safety','Multilingual','Factuality','Math','Uncertainty']:V['topic.'+topic+'.'+g]=sum(groups[i]==g and str(topics[i]).lower()==topic.lower() for i in ids)
V['reviews.total']=len(q);V['projects.total']=len(ids);V['matched.projects']=len(ids)
for rr in run['details']['per_project']:
 i=rr['idea_id'];check('project-condition:'+i,rr['condition']==groups[i]);check('project-topic:'+i,rr['topic']==topics[i])
 near('pre-review-count:'+i,rr['pre_reviews'],sum(z[pi['idea_id']]==i for z in p))
 near('post-review-count:'+i,rr['post_reviews'],sum(z[qi['idea_id']]==i for z in q))
 for k in M:
  for phase,values in [('pre',pre),('post',post)]:near('project:'+i+':'+phase+':'+k,m(values[i][k]),rr[phase][k])
  near('project:'+i+':gap:'+k,m(post[i][k]-pre[i][k]),rr['gap'][k])
review_tests={}
for k in ALL:
 data={g:[frac(z[qi[field(k)]]) for z in q if z[qi['condition']]==g] for g in ['Human','AI']}
 for g,x in data.items():
  V['review.'+k+'.'+g+'.mean']=m(avg(x));V['review.'+k+'.'+g+'.sd']=mp.sqrt(m(var(x,0)))
 w=welch(data['AI'],data['Human'],'less');review_tests[k]=w
 for label,v in w.items():near('review:'+k+':'+label,v,run['details']['review'][k][label])
for k,v in zip(ALL[:5],adjust([review_tests[k]['p_raw'] for k in ALL[:5]])):V['review.'+k+'.p']=v
for k in ALL[5:]:V['review.'+k+'.p']=review_tests[k]['p_raw']
for k in ALL:V['claim.review.'+k+'.significant']=V['review.'+k+'.p']<mp.mpf('.05')
for phase,values in [('pre',pre),('post',post)]:
 ps=[]
 for k in M:
  data={g:[values[i][k] for i in ids if groups[i]==g] for g in ['Human','AI']}
  for g,x in data.items():V['idea.'+k+'.'+phase+'.'+g]=m(avg(x))
  w=welch(data['AI'],data['Human']);ps.append(w['p_raw'])
  for label,v in w.items():near('idea:'+phase+':'+k+':'+label,v,run['details']['idea'][phase+'.'+k][label])
 for k,v in zip(M,adjust(ps)):V['idea.'+k+'.'+phase+'.p']=v;V['claim.idea.'+k+'.'+phase+'.significant']=v<mp.mpf('.05')
for k in M:V['claim.idea.'+k+'.ranking.flip']=V['idea.'+k+'.pre.AI']>V['idea.'+k+'.pre.Human'] and V['idea.'+k+'.post.AI']<V['idea.'+k+'.post.Human']
for variant in ['full','exclude6']:
 ii=[i for i in ids if variant=='full' or i not in plan['exclude6_only_for_original_robustness']];ps=[]
 for k in M:
  data={g:[post[i][k]-pre[i][k] for i in ii if groups[i]==g] for g in ['Human','AI']}
  for g,x in data.items():V['gap.'+variant+'.'+k+'.'+g]=m(avg(x))
  V['gap.'+variant+'.'+k+'.difference']=m(avg(data['Human'])-avg(data['AI']))
  w=welch(data['Human'],data['AI'],'greater');ps.append(w['p_raw'])
  for label,v in w.items():near('gap:'+variant+':'+k+':'+label,v,run['details']['gap'][variant+'.'+k][label])
 for k,v in zip(M,adjust(ps)):V['gap.'+variant+'.'+k+'.p']=v;V['claim.gap.'+variant+'.'+k+'.significant']=v<mp.mpf('.05')
for g in ['Human','AI']:
 ii=[i for i in ids if groups[i]==g]
 for k in M:
  x=[pre[i][k] for i in ii];y=[post[i][k] for i in ii]
  V['correlation.'+g+'.pearson.'+k]=correlate(x,y);V['correlation.'+g+'.spearman.'+k]=correlate(ranks(x),ranks(y))
original=[]
for target in read(R/'targets.json'):
 k=target['key'];x=V[k];y=run['values'][k]
 if isinstance(target['expected'],bool):check('independent:'+k,x==y)
 else:near('independent:'+k,x,y)
 ok=(x==target['expected']) if target['absolute_tolerance']==0 else abs(m(x)-mp.mpf(str(target['expected'])))<=mp.mpf(str(target['absolute_tolerance']))
 original.append({**target,'independent_actual':str(x),'pass':bool(ok)})
 recorded=next(c for c in run['checks'] if c['key']==k)
 check('original-gate-decision:'+k,ok==recorded['pass'])
check('all-target-counts',len(original)==plan['target_count']==len(run['checks'])==155)
check('gate-result-identity',sum(c['pass'] for c in original)==run['passed'] and all(c['pass'] for c in original)==run['all_pass'])
audit={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'70-digit scalar mpmath with exact rational raw-score sums, independent Welch/incomplete-beta tails and BH adjustment; exact tie-ranking and Pearson sums. No NumPy/SciPy/pandas or experimental runner import. All original gates re-evaluated without changing tolerances.','computational_all_pass':all(c['pass'] for c in checks),'computational_passed':sum(c['pass'] for c in checks),'computational_total':len(checks),'original_target_all_pass':all(c['pass'] for c in original),'original_target_passed':sum(c['pass'] for c in original),'original_target_total':len(original),'checks':checks,'original_target_checks':original,'wall_seconds':time.perf_counter()-start}
(A/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
(A/'independent_values.json').write_text(json.dumps({k:str(v) for k,v in V.items()},indent=2),encoding='utf8')
(A/'auditor.py').write_bytes(pathlib.Path(__file__).read_bytes())
(A/'manifest.json').write_text(json.dumps([{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(A.iterdir()) if p.is_file()],indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['checks','original_target_checks']},indent=2))
print(json.dumps([c for c in checks if not c['pass']],indent=2))
