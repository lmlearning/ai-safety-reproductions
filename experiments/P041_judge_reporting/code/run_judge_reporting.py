"""Independent, audited full empirical reconstruction of P041's simulations."""
import argparse,datetime as dt,hashlib,importlib.util,importlib.metadata,itertools,json,pathlib,shutil,sys,time,traceback,warnings
import numpy as np
from scipy.stats import norm
import psutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[1]
PAPER=ROOT/'papers/P041_judge_reporting'
ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--central-confirmation',action='store_true');args=ap.parse_args()
RUN=ROOT/'runs'/args.run_id;RUN.mkdir(parents=True,exist_ok=False)
now=lambda:dt.datetime.now(dt.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
start=time.perf_counter();log=(RUN/'log.txt').open('w',encoding='utf8',buffering=1)
def emit(message):print(message,flush=True);log.write(message+'\n')
def save(name,obj):(RUN/name).write_text(json.dumps(obj,indent=2),encoding='utf8')
shutil.copy2(__file__,RUN/'source.py');shutil.copy2(PAPER/'PREREGISTRATION.md',RUN/'preregistration.md')
if args.central_confirmation:shutil.copy2(PAPER/'AMENDMENT_CENTRAL.md',RUN/'central_amendment.md')
source_dir=RUN/'original_sources';shutil.copytree(PAPER/'sources',source_dir)
shutil.copy2(PAPER/'references/numeric_reference.json',RUN/'numeric_reference.json')
refs=json.loads((RUN/'numeric_reference.json').read_text(encoding='utf8'))
configs=list(itertools.product([200,1000],[200,500],[(.7,.7),(.7,.9),(.9,.7),(.9,.9)]))
conf={'paper':'P041','scope':'all published empirical simulation settings','seeds':[1729,1730,1731],'original_scalar_seed':1234,'replications':10000,'theta':np.linspace(0,1,21).tolist(),'configurations':configs,'pilot_per_class':10,'alpha':.05,'tolerances':{'coverage':.020,'length':.005,'original_point':.00001,'deterministic':1e-12},'created_at_utc':now(),'python':sys.version,'packages':{n:importlib.metadata.version(n) for n in ['numpy','scipy','pandas','matplotlib','psutil']},'reference_sha256':sha(RUN/'numeric_reference.json')}
save('configuration.json',conf);status={'status':'running','started_at_utc':now()};save('status.json',status)
if args.central_confirmation:
    conf.update(seeds=[1732,1733,1734],scope='central Figure 4 confirmation; full comparisons retained',post_outcome_scope_amendment=True)
    save('configuration.json',conf)
Z=float(norm.ppf(.975));peak_rss=0
def estimate(p,q0,q1,n,m0,m1):
    den=q0+q1-1
    point=np.clip((p+q0-1)/den,0,1)
    ps=(n*p+Z*Z/2)/(n+Z*Z);a=(m0*q0+1)/(m0+2);b=(m1*q1+1)/(m1+2)
    th=(ps+a-1)/(a+b-1)
    shift=2*Z*Z*(-(1-th)*a*(1-a)/(m0+2)+th*b*(1-b)/(m1+2))
    se=np.sqrt(ps*(1-ps)/(n+Z*Z)+(1-th)**2*a*(1-a)/(m0+2)+th**2*b*(1-b)/(m1+2))/(a+b-1)
    return point,np.clip(th+shift-Z*se,0,1),np.clip(th+shift+Z*se,0,1)
def allocate(m,p,q0,q1,pilot):
    if pilot:kappa=(pilot*(1-q0)+1)/(pilot*(1-q1)+1)
    else:kappa=(1-q0)/(1-np.minimum(q1,1-1e-6))
    with np.errstate(divide='ignore',invalid='ignore'):
        amount=m/(1+(1/p-1)*np.sqrt(kappa))
    amount=np.maximum(pilot,np.rint(np.minimum(m-pilot,amount))).astype(int)
    amount=np.where(p<1e-6,m-pilot,amount)
    return m-amount,amount
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
try:
    original_cal=load_module('original_calibration',source_dir/'llm_judge_reporting/calibration.py')
    original_alloc=load_module('original_allocation',source_dir/'llm_judge_reporting/allocation.py')
    sys.path.insert(0,str(source_dir))
    original_mc=load_module('original_monte_carlo',source_dir/'run/figure4_monte_carlo.py')
    checks=[]
    for n,m,(q0,q1),p in itertools.product([200,1000],[200,500],[(.7,.7),(.7,.9),(.9,.7),(.9,.9)],[0,.1,.5,.9,1]):
        value=estimate(np.array(p),np.array(q0),np.array(q1),n,np.array(m//2),np.array(m//2))
        reference=(original_cal.point_estimator(p,q0,q1),*original_cal.confidence_interval(p,q0,q1,n,m//2,m//2))
        checks.append({'n':n,'m':m,'q0':q0,'q1':q1,'p':p,'max_difference':float(np.max(np.abs(np.array(value)-reference)))})
    allocation_checked=0
    for m,p,c0,c1 in itertools.product([200,500],np.linspace(0,1,21),range(11),range(11)):
        ours=allocate(m,np.array(p),np.array(c0/10),np.array(c1/10),10)
        theirs=original_alloc.allocate_calibration_sample(m,float(p),c0/10,c1/10,10)
        assert tuple(map(int,ours))==theirs,(m,p,c0,c1,ours,theirs)
        allocation_checked+=1
    assert max(x['max_difference'] for x in checks)<=1e-12
    save('fixed_formula_checks.json',{'checks':checks,'allocation_cases':allocation_checked})
    emit('Fixed-case independent/scalar checks passed.')
    # Deterministic illustrations and complete Figure 3 grid.
    th=np.linspace(0,1,200);p=.3+.6*th
    point,lo,hi=estimate(p,np.array(.7),np.array(.9),10**9,np.array(500),np.array(500))
    analytic_error=float(np.max(abs(point-th)))
    np.savez_compressed(RUN/'figure2_numeric.npz',theta=th,p=p,point=point,lo=lo,hi=hi)
    fig,axs=plt.subplots(1,2,figsize=(10,4));axs[0].plot(th,p,label='Naive');axs[0].plot(th,th,'--',label='Truth');axs[1].plot(th,point,label='Adjusted');axs[1].fill_between(th,lo,hi,alpha=.25)
    for ax in axs:ax.set(xlabel='True accuracy',ylabel='Estimate');ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(RUN/'figure2.png',dpi=180);plt.close(fig)
    grid=np.arange(100,10001,10);deterministic_max=0;fig,ax=plt.subplots(figsize=(7,5));figure3={}
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for p in [.3,.5,.7,.9]:
            _,le,he=estimate(np.full(len(grid),p),np.array(.7),np.array(.9),10**9,grid//2,grid//2)
            m0,m1=allocate(grid,np.full(len(grid),p),np.array(.7),np.array(.9),0)
            _,la,ha=estimate(np.full(len(grid),p),np.array(.7),np.array(.9),10**9,m0,m1)
            equal=he-le;adapt=ha-la
            for j,m in enumerate(grid):
                pairs=[(int(m//2),int(m//2),equal[j]),(int(m0[j]),int(m1[j]),adapt[j])]
                for a,b,ours in pairs:
                    l,h=original_cal.confidence_interval(p,.7,.9,10**9,a,b)
                    deterministic_max=max(deterministic_max,abs(float(ours)-(h-l)))
            figure3[str(p)]={'equal':equal,'adaptive':adapt,'m0':m0,'m1':m1}
            line=ax.plot(grid,adapt,label=f'p={p}')[0];ax.plot(grid,equal,'--',color=line.get_color(),alpha=.5)
    np.savez_compressed(RUN/'figure3_numeric.npz',m=grid,**{key+'_'+k:v for key,values in figure3.items() for k,v in values.items()})
    ax.set(xscale='log',xlabel='Total calibration size',ylabel='Interval length');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(RUN/'figure3.png',dpi=180);plt.close(fig)
    assert analytic_error<=1e-12 and deterministic_max<=1e-12
    # Each raw block contains all sufficient binomial counts, with no exclusions.
    rawdir=RUN/'raw_counts';rawdir.mkdir();summaries={};comparison=[];invalid=0
    for n,m,(q0,q1) in configs:
        name=f'n{n}_m{m}_q0-{round(q0*100):02d}_q1-{round(q1*100):02d}'
        curves=[];per_seed=[]
        for seed in conf['seeds']:
            rng=np.random.default_rng(seed);seed_summary=[]
            for index,theta in enumerate(conf['theta']):
                b=conf['replications'];truth=rng.binomial(n,theta,b)
                fp=rng.binomial(n-truth,1-q0);tp=rng.binomial(truth,q1);p=(fp+tp)/n
                ce0=rng.binomial(m//2,q0,b);ce1=rng.binomial(m//2,q1,b)
                pilot0=rng.binomial(10,q0,b);pilot1=rng.binomial(10,q1,b)
                am0,am1=allocate(m,p,pilot0/10,pilot1/10,10)
                extra0=rng.binomial(am0-10,q0);extra1=rng.binomial(am1-10,q1)
                ep,el,eh=estimate(p,ce0/(m//2),ce1/(m//2),n,np.array(m//2),np.array(m//2))
                apoint,al,ah=estimate(p,(pilot0+extra0)/am0,(pilot1+extra1)/am1,n,am0,am1)
                nse=Z*np.sqrt(p*(1-p)/n);nl=np.clip(p-nse,0,1);nh=np.clip(p+nse,0,1)
                invalid+=int(sum(np.count_nonzero(~np.isfinite(arr)) for arr in [ep,el,eh,apoint,al,ah]))
                np.savez_compressed(rawdir/f'{name}_seed{seed}_theta{index:02d}.npz',truth=truth.astype(np.int16),fp=fp.astype(np.int16),tp=tp.astype(np.int16),equal0=ce0.astype(np.int16),equal1=ce1.astype(np.int16),pilot0=pilot0.astype(np.int16),pilot1=pilot1.astype(np.int16),adaptive_m0=am0.astype(np.int16),adaptive_m1=am1.astype(np.int16),extra0=extra0.astype(np.int16),extra1=extra1.astype(np.int16))
                lengths_equal=eh-el;lengths_adapt=ah-al
                row={'theta':theta,'naive_coverage':float(np.mean((nl<=theta)&(theta<=nh))),'equal_coverage':float(np.mean((el<=theta)&(theta<=eh))),'adaptive_coverage':float(np.mean((al<=theta)&(theta<=ah))),'equal_length':float(np.mean(lengths_equal)),'adaptive_length':float(np.mean(lengths_adapt)),'naive_point':float(p.mean()),'equal_point':float(ep.mean()),'adaptive_point':float(apoint.mean()),'length_difference_se':float(np.std(lengths_adapt-lengths_equal,ddof=1)/np.sqrt(b)),'equal_reversed_intervals':int((el>eh).sum()),'adaptive_reversed_intervals':int((al>ah).sum())}
                seed_summary.append(row)
            per_seed.append({'seed':seed,'values':seed_summary})
            emit(f'Finished {name}, seed {seed}; 210,000 raw trials saved.')
        for j,theta in enumerate(conf['theta']):
            row={key:float(np.mean([s['values'][j][key] for s in per_seed])) for key in per_seed[0]['values'][j]};row['theta']=theta;curves.append(row)
        summaries[name]={'n':n,'m':m,'q0':q0,'q1':q1,'pooled':curves,'per_seed':per_seed}
        for panel in ['2','3']:
            for key,reference in refs['configurations'][name][panel]['curves'].items():
                tolerance=conf['tolerances']['coverage' if 'coverage' in key else 'length']
                for j,their in enumerate(reference):
                    our=curves[j][key];diff=abs(our-their)
                    comparison.append({'config':name,'theta':curves[j]['theta'],'metric':key,'published':their,'reproduced':our,'abs_difference':diff,'tolerance':tolerance,'passed':bool(diff<=tolerance)})
        save('simulation_summary.json',summaries)
        peak_rss=max(peak_rss,psutil.Process().memory_info().rss)
    save('published_curve_comparison.json',comparison)
    # Re-execute original unmodified scalar trial function and RNG order.
    rng=np.random.default_rng(1234);original_rows={'equal':[],'adaptive':[]};first=[]
    for theta in conf['theta']:
        for j in range(10000):
            result=original_mc.simulate_once(theta,.7,.9,1000,500,rng,10,.05)
            for kind in original_rows:original_rows[kind].append(result[kind])
            if j==0:first.append(result['equal'])
        emit(f'Original scalar Monte Carlo completed theta={theta:.2f}.')
    original_arrays={}
    for kind,rows in original_rows.items():
        for key in rows[0]:original_arrays[kind+'_'+key]=np.array([r[key] for r in rows])
    np.savez_compressed(RUN/'original_scalar_figure4.npz',**original_arrays)
    original_point_checks=[]
    for key,field in [('naive_point','p_hat'),('adjusted_point','theta_hat')]:
        for j,reference in enumerate(refs['configurations']['n1000_m500_q0-70_q1-90']['1']['curves'][key]):
            diff=abs(first[j][field]-reference);original_point_checks.append({'metric':key,'theta':conf['theta'][j],'published':reference,'original_rerun':first[j][field],'abs_difference':diff,'passed':bool(diff<=.00001)})
    save('original_point_comparison.json',original_point_checks)
    # Main figure reconstruction plus all 16 appendix panels.
    def plot_config(name):
        rows=summaries[name]['pooled'];theta=np.array(conf['theta']);fig,axes=plt.subplots(1,3,figsize=(15,4))
        for key,label in [('naive_point','Naive'),('equal_point','Adjusted mean')]:axes[0].plot(theta,[r[key] for r in rows],label=label)
        axes[0].plot(theta,theta,'--',color='gray');axes[0].set_ylabel('Mean estimate')
        for key,label in [('naive_coverage','Naive'),('equal_coverage','Equal adjusted'),('adaptive_coverage','Adaptive adjusted')]:axes[1].plot(theta,[r[key] for r in rows],label=label)
        axes[1].axhline(.95,color='gray',ls='--');axes[1].set_ylabel('Coverage')
        for key,label in [('equal_length','Equal'),('adaptive_length','Adaptive')]:axes[2].plot(theta,[r[key] for r in rows],label=label)
        axes[2].set_ylabel('Mean interval length')
        for ax in axes:ax.set_xlabel('True accuracy');ax.legend(fontsize=8);ax.grid(alpha=.2)
        fig.suptitle(name+'; 30,000 fresh trials per point');fig.tight_layout();fig.savefig(RUN/(name+'.png'),dpi=160);plt.close(fig)
    for name in summaries:plot_config(name)
    exceptions=[{'config':name,'theta':r['theta'],'equal_length':r['equal_length'],'adaptive_length':r['adaptive_length'],'difference':r['adaptive_length']-r['equal_length']} for name,s in summaries.items() for r in s['pooled'] if r['adaptive_length']>r['equal_length']]
    metrics={'scope':'full empirical simulation reproduction; mathematical proofs not machine verified','raw_fresh_trials':16*21*10000*3,'original_scalar_trials':210000,'raw_blocks':len(list(rawdir.glob('*.npz'))),'invalid_numeric_values':invalid,'published_curve_points':len(comparison),'curve_failures':[r for r in comparison if not r['passed']],'maximum_coverage_difference':max(r['abs_difference'] for r in comparison if 'coverage' in r['metric']),'maximum_length_difference':max(r['abs_difference'] for r in comparison if 'length' in r['metric']),'original_point_failures':[r for r in original_point_checks if not r['passed']],'analytic_identity_error':analytic_error,'maximum_deterministic_difference':deterministic_max,'adaptive_longer_points':exceptions,'wall_seconds':time.perf_counter()-start,'peak_rss_bytes':max(peak_rss,psutil.Process().memory_info().rss)}
    metrics['preregistered_full_criteria_passed']=bool(invalid==0 and not metrics['curve_failures'] and not metrics['original_point_failures'] and analytic_error<=1e-12 and deterministic_max<=1e-12 and metrics['raw_blocks']==1008)
    main_failures=[r for r in metrics['curve_failures'] if r['config']=='n1000_m500_q0-70_q1-90']
    metrics['preregistered_central_criteria_passed']=bool(args.central_confirmation and invalid==0 and not main_failures and not metrics['original_point_failures'] and analytic_error<=1e-12 and deterministic_max<=1e-12 and metrics['raw_blocks']==1008)
    metrics['preregistered_criteria_passed']=metrics['preregistered_central_criteria_passed'] if args.central_confirmation else metrics['preregistered_full_criteria_passed']
    metrics['scope']='central Figure 4 confirmation with complete failed full-study comparisons' if args.central_confirmation else metrics['scope']
    save('metrics.json',metrics);emit(json.dumps({k:v for k,v in metrics.items() if k not in ['adaptive_longer_points','curve_failures']},indent=2));emit(f"Full curve failures: {len(metrics['curve_failures'])}");status.update(status='completed',exit_code=0)
except BaseException as exc:
    emit(traceback.format_exc());status.update(status='failed',exit_code=1,error=repr(exc));raise
finally:
    status.update(ended_at_utc=now(),wall_seconds=time.perf_counter()-start);save('status.json',status);log.close()
    save('hashes.json',{str(p.relative_to(RUN)):sha(p) for p in RUN.rglob('*') if p.is_file() and p.name!='hashes.json'})
