"""P109 frozen central analysis. No original outcome work at import."""
from pathlib import Path
import csv,ctypes,datetime,hashlib,importlib.metadata,json,math,os,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'papers/P109_higher_order_thinking'
OUT=PAPER/'runs/P109-central-001'
Z975=1.959963984540054
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
class PMC(ctypes.Structure):
 _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t),('PrivateUsage',ctypes.c_size_t)]
class MEM(ctypes.Structure):
 _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
def resource(phase,started):
 k=ctypes.WinDLL('kernel32',use_last_error=True);a=ctypes.WinDLL('psapi',use_last_error=True)
 k.GetCurrentProcess.restype=ctypes.c_void_p
 pm=PMC();pm.cb=ctypes.sizeof(pm)
 if not a.GetProcessMemoryInfo(ctypes.c_void_p(k.GetCurrentProcess()),ctypes.byref(pm),pm.cb):raise ctypes.WinError(ctypes.get_last_error())
 mem=MEM();mem.dwLength=ctypes.sizeof(mem)
 if not k.GlobalMemoryStatusEx(ctypes.byref(mem)):raise ctypes.WinError(ctypes.get_last_error())
 row={'utc':now(),'actual_pid':os.getpid(),'phase':phase,'elapsed_seconds':time.monotonic()-started,'rss_bytes':pm.WorkingSetSize,'peak_rss_bytes':pm.PeakWorkingSetSize,'private_commit_bytes':pm.PrivateUsage,'available_ram_bytes':mem.ullAvailPhys,'available_commit_bytes':mem.ullAvailPageFile,'disk_free_bytes':shutil.disk_usage(ROOT).free}
 with (OUT/'resources.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
 if row['elapsed_seconds']>600 or row['peak_rss_bytes']>1024**3 or row['available_ram_bytes']<1024**3 or row['disk_free_bytes']<35*1024**3:
  save('resource_stop.json',row);raise RuntimeError('Frozen resource bound reached; no auto restart')
 return row
def run():
 started=time.monotonic()
 if OUT.exists():raise RuntimeError('Existing immutable run preserved; no automatic restart')
 freeze=PAPER/'RUN_FREEZE_001.json';auth=PAPER/'ROOT_EXECUTION_AUTHORIZATION001.json'
 plan=json.loads((PAPER/'PREREGISTRATION_001.json').read_text())
 fx=json.loads(freeze.read_text());au=json.loads(auth.read_text())
 if au.get('approved_by')!='root' or au.get('execution_authorized') is not True or au.get('freeze_sha256')!=sha(freeze):raise RuntimeError('Exact root authorization required')
 for p,h in fx['sha256'].items():
  if sha(ROOT/p)!=h:raise RuntimeError('Frozen input/code/runtime mismatch '+p)
 os.environ.update({'OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','MPLBACKEND':'Agg'})
 OUT.mkdir(parents=True)
 save('run_start.json',{'started_at_utc':now(),'actual_pid':os.getpid(),'argv':sys.argv,'python':sys.version,'python_executable':sys.executable,'freeze_sha256':sha(freeze),'authorization_sha256':sha(auth),'preregistration_sha256':sha(PAPER/'PREREGISTRATION_001.json'),'class':plan['proposed_class'],'no_auto_restart':True})
 try:
  resource('before numerical imports',started)
  global np,stats,optimize
  import numpy as np
  from scipy import stats,optimize
  resource('after numerical imports',started)
  save('runtime_versions.json',{n:importlib.metadata.version(n) for n in ['numpy','scipy','mpmath','matplotlib']})
  rows=list(csv.DictReader((PAPER/'sources/figure3_literal_transcription_001.csv').open(newline='',encoding='utf-8')))
  if len(rows)!=59 or [int(r['figure3_row']) for r in rows]!=list(range(1,60)):raise RuntimeError('Complete ordered59-row census required')
  for r in rows:
   for name in ['g','se','variance','ci_lower','ci_upper','z','p_display']:
    if not math.isfinite(float(r[name])):raise RuntimeError('Invalid original field')
  g=np.array([float(r['g']) for r in rows]);s=np.array([float(r['se']) for r in rows]);vp=np.array([float(r['variance']) for r in rows])
  vlo=np.maximum((s-.0005)**2,vp-.0005);vhi=np.minimum((s+.0005)**2,vp+.0005)
  if np.any(vlo<=0) or np.any(vlo>vhi):raise RuntimeError('Unrounded source variance/SE intersection empty; no outcome-target fitting')
  v=np.clip(s*s,vlo,vhi);gl=g-.0005;gh=g+.0005
  source=[dict(r,point_variance=float(v[i]),variance_lower=float(vlo[i]),variance_upper=float(vhi[i]),g_lower=float(gl[i]),g_upper=float(gh[i])) for i,r in enumerate(rows)]
  save('source_rows_and_precision.json',source)
  resource('before primary aggregation',started)
  def pool(values,variances,tau=0.):
   w=1/(variances+tau);mu=float(np.dot(w,values)/w.sum());var=float(1/w.sum());se=math.sqrt(var);z=mu/se
   return {'k':len(values),'mean':mu,'se':se,'variance':var,'ci_low':mu-Z975*se,'ci_high':mu+Z975*se,'z':z,'p':float(2*stats.norm.sf(abs(z)))}
  def hetero(values,variances):
   w=1/variances;mu=float(np.dot(w,values)/w.sum());q=float(np.dot(w,(values-mu)**2));c=float(w.sum()-np.dot(w,w)/w.sum());df=len(values)-1
   return {'Q':q,'df':df,'Q_p':float(stats.chi2.sf(q,df)),'I2':100*max(0.,(q-df)/q) if q else 0.,'C':c,'tau2_DL':max(0.,(q-df)/c)}
  ht=hetero(g,v);fixed=pool(g,v);random=pool(g,v,ht['tau2_DL'])
  def extreme_mean(lo,hi,wl,wh,upper):
   arr=hi if upper else lo;a=float(lo.min());b=float(hi.max())
   for _ in range(150):
    mid=(a+b)/2;diff=arr-mid;weights=np.where(diff>0,wh,wl) if upper else np.where(diff<0,wh,wl)
    val=float(np.dot(weights,diff))
    if val>0:a=mid
    else:b=mid
   return (a+b)/2
  def pool_box(lo,hi,wl,wh):
   ml=extreme_mean(lo,hi,wl,wh,False);mh=extreme_mean(lo,hi,wl,wh,True)
   vl=1/float(wh.sum());vh=1/float(wl.sum());sl=math.sqrt(vl);sh=math.sqrt(vh)
   zs=[m/e for m in [ml,mh] for e in [sl,sh]];zl=min(zs);zh=max(zs)
   if zl<=0<=zh:pl=float(2*stats.norm.sf(max(abs(zl),abs(zh))));ph=1.
   else:pl=float(2*stats.norm.sf(max(abs(zl),abs(zh))));ph=float(2*stats.norm.sf(min(abs(zl),abs(zh))))
   return {'mean':[ml,mh],'variance':[vl,vh],'se':[sl,sh],'ci_low':[ml-Z975*sh,mh-Z975*sl],'ci_high':[ml+Z975*sl,mh+Z975*sh],'z':[zl,zh],'p':[pl,ph]}
  wl=1/vhi;wh=1/vlo
  def q_at(w):
   m=float(np.dot(w,g)/w.sum());return float(np.dot(w,(g-m)**2))
  qlo=max(0.,math.sqrt(q_at(wl))-.0005*math.sqrt(float(wl.sum())))**2
  qhi=(math.sqrt(q_at(wh))+.0005*math.sqrt(float(wh.sum())))**2
  clo=float(wl.sum()-np.dot(wl,wl)/wl.sum());chi=float(wh.sum()-np.dot(wh,wh)/wh.sum())
  tlo=max(0.,(qlo-58)/chi);thi=max(0.,(qhi-58)/clo)
  boxes={'fixed':pool_box(gl,gh,wl,wh),'random':pool_box(gl,gh,1/(vhi+thi),1/(vlo+tlo)),
   'Q':[qlo,qhi],'df':[58,58],'Q_p':[float(stats.chi2.sf(qhi,58)),float(stats.chi2.sf(qlo,58))],
   'I2':[100*max(0.,1-58/qlo) if qlo else 0.,100*max(0.,1-58/qhi) if qhi else 0.],
   'tau2_DL':[tlo,thi],'C':[clo,chi]}
  def get(obj,key):
   for part in key.split('.'):obj=obj[part]
   return obj
  points={'fixed':fixed,'random':random,**ht};comparisons=[]
  for t in plan['targets']:
   key=t['id'];point=get(points,key);rule=t['cap_key'];target=t['target']
   if rule=='exact':
    record={**t,'actual':point,'passed':point==target}
   else:
    bounds=get(boxes,key);lo=bounds[0]-1e-9;hi=bounds[1]+1e-9
    if key.endswith('.p') or key=='Q_p':lo=max(0.,lo);hi=min(1.,hi)
    elif key.endswith('.variance') or key.endswith('.se'):lo=max(0.,lo)
    if rule=='threshold':
     threshold=float(target[1:]);passed=hi<threshold
     record={**t,'actual':point,'rounding_envelope':[lo,hi],'passed':passed,'required_upper_threshold':threshold}
    else:
     width=hi-lo;cap=plan['width_caps'][rule];overlap=lo<=float(target)+t['rounding_half_unit'] and hi>=float(target)-t['rounding_half_unit']
     record={**t,'actual':point,'rounding_envelope':[lo,hi],'envelope_width':width,'width_cap':cap,'target_interval_overlap':overlap,'passed':overlap and width<=cap}
   comparisons.append(record)
  positive=boxes['random']['ci_low'][0]-1e-9>0
  save('primary_statistics.json',points);save('source_rounding_enclosures.json',boxes);save('comparisons.json',comparisons)
  resource('after complete primary aggregation',started)
  indices={d:np.array([i for i,r in enumerate(rows) if r['dimension']==d]) for d in ['Cr','CT','PS']}
  if {d:len(i) for d,i in indices.items()}!={'Cr':23,'CT':20,'PS':16}:raise RuntimeError('Complete dimension label census differs')
  hs={d:hetero(g[i],v[i]) for d,i in indices.items()}
  within_tau=max(0.,(sum(h['Q'] for h in hs.values())-sum(h['df'] for h in hs.values()))/sum(h['C'] for h in hs.values()))
  dimensions={}
  for scheme in ['independent_DL','shared_within_DL','shared_overall_DL']:
   sub={}
   for d,i in indices.items():
    tau=hs[d]['tau2_DL'] if scheme=='independent_DL' else within_tau if scheme=='shared_within_DL' else ht['tau2_DL']
    sub[d]={**pool(g[i],v[i],tau),'tau2':tau,'heterogeneity':hs[d]}
   wg=np.array([1/sub[d]['variance'] for d in indices]);mg=np.array([sub[d]['mean'] for d in indices]);grand=float(np.dot(wg,mg)/wg.sum());between=float(np.dot(wg,(mg-grand)**2))
   dimensions[scheme]={'groups':sub,'between_Q':between,'between_df':2,'between_p':float(stats.chi2.sf(between,2))}
  x=1/s;y=g/s;X=np.column_stack([np.ones(59),x]);beta=np.linalg.lstsq(X,y,rcond=None)[0];resid=y-X@beta;mse=float(np.dot(resid,resid)/57);cov=mse*np.linalg.inv(X.T@X);se0=math.sqrt(float(cov[0,0]));t=float(beta[0])/se0;pv=float(2*stats.t.sf(abs(t),57))
  egger={'k_effects':59,'df':57,'intercept':float(beta[0]),'slope':float(beta[1]),'intercept_se':se0,'t':t,'p_two_sided':pv,'source_t':1.871,'source_p':.066,'t_difference':t-1.871,'p_difference':pv-.066,'descriptive_t_absolute_tolerance_0p02':abs(t-1.871)<=.02,'descriptive_p_absolute_tolerance_0p005':abs(pv-.066)<=.005,'paper_calls_cohort_29studies':True}
  funnels={}
  for label,center in [('fixed',fixed['mean']),('random',random['mean'])]:
   flag=np.abs(g-center)>Z975*s
   funnels[label]={'center':center,'outside_count':int(flag.sum()),'source_outside_count':8,'outside_figure3_rows':(np.flatnonzero(flag)+1).tolist(),'source_count_agrees':int(flag.sum())==8}
  def reml_objective(tau):
   w=1/(v+tau);m=float(np.dot(w,g)/w.sum());return .5*(float(np.log(v+tau).sum())+math.log(float(w.sum()))+float(np.dot(w,(g-m)**2)))
  reml_fit=optimize.minimize_scalar(reml_objective,bounds=(0.,100.),method='bounded',options={'xatol':1e-12})
  if not reml_fit.success:raise RuntimeError('REML sensitivity solver failed; keep all primary records')
  rt=float(reml_fit.x) if reml_fit.fun<reml_objective(0) else 0.
  def q_residual(tau):
   w=1/(v+tau);m=float(np.dot(w,g)/w.sum());return float(np.dot(w,(g-m)**2))-58
  if q_residual(0)<=0:pt=0.
  elif q_residual(100)>=0:raise RuntimeError('Frozen PM bracket insufficient; no automatic changed bracket')
  else:pt=float(optimize.brentq(q_residual,0,100,xtol=1e-12))
  sensitivity={'REML':{**pool(g,v,rt),'tau2':rt,'objective':reml_objective(rt)},'Paule_Mandel':{**pool(g,v,pt),'tau2':pt,'score_residual':q_residual(pt)}}
  supporting={'dimensions_all_three_schemes':dimensions,'original_Table4':{'Cr':{'k':23,'mean':.444,'ci_low':.259,'ci_high':.629,'z':4.698},'CT':{'k':20,'mean':.691,'ci_low':.464,'ci_high':.918,'z':5.973},'PS':{'k':16,'mean':.745,'ci_low':.521,'ci_high':.970,'z':6.507},'between_Q':4.961,'between_p':.084},'egger':egger,'funnel':funnels,'overall_estimator_sensitivity':sensitivity,'success_scope_not_expanded':True}
  save('supporting_diagnostics.json',supporting)
  resource('after all supporting diagnostics',started)
  save('result.json',{'finished_at_utc':now(),'actual_pid':os.getpid(),'central_gate_count':len(comparisons),'passed_gates':sum(c['passed'] for c in comparisons),'all_central_gates_passed':all(c['passed'] for c in comparisons),'all_rounding_random_lower_ci_positive':positive,'source_rows':59,'independent_audit_required':True,'counted_success':False,'class':plan['proposed_class'],'original_CMA_tau_setting_verified':False,'elapsed_seconds':time.monotonic()-started})
  save('run_end.json',{'finished_at_utc':now(),'actual_pid':os.getpid(),'status':'completed','exit_code':0,'elapsed_seconds':time.monotonic()-started,'root_credit_review_required':True})
 except BaseException as e:
  save('failure.json',{'at_utc':now(),'actual_pid':os.getpid(),'error':repr(e),'elapsed_seconds':time.monotonic()-started,'no_auto_restart':True})
  raise
if __name__=='__main__':run()
