"""Independent integrity and sufficient-count audit; does not alter run artifacts."""
import argparse,datetime as dt,hashlib,json,pathlib,re
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);args=p.parse_args();run=ROOT/'runs'/args.run_id
hashes=json.loads((run/'hashes.json').read_text());bad=[name for name,digest in hashes.items() if hashlib.sha256((run/name).read_bytes()).hexdigest()!=digest]
blocks=list((run/'raw_counts').glob('*.npz'));trials=0;violations=[]
for path in blocks:
    n,m,q0,q1,seed,theta=map(int,re.fullmatch(r'n(\d+)_m(\d+)_q0-(\d+)_q1-(\d+)_seed(\d+)_theta(\d+)\.npz',path.name).groups())
    with np.load(path) as data:
        a={k:data[k] for k in data.files}
    valid=all(len(v)==10000 for v in a.values()) and all(np.all(v>=0) for v in a.values())
    valid &= np.all(a['truth']<=n) and np.all(a['tp']<=a['truth']) and np.all(a['fp']<=n-a['truth'])
    valid &= np.all(a['equal0']<=m//2) and np.all(a['equal1']<=m//2)
    valid &= np.all(a['pilot0']<=10) and np.all(a['pilot1']<=10)
    valid &= np.all(a['adaptive_m0']+a['adaptive_m1']==m) and np.all(a['adaptive_m0']>=10) and np.all(a['adaptive_m1']>=10)
    valid &= np.all(a['extra0']<=a['adaptive_m0']-10) and np.all(a['extra1']<=a['adaptive_m1']-10)
    if not valid:violations.append(path.name)
    trials+=len(a['truth'])
result={'run_id':args.run_id,'audited_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'manifest_files':len(hashes),'bad_hashes':bad,'raw_blocks':len(blocks),'raw_trials':trials,'invalid_count_blocks':violations,'passed':not bad and not violations and trials==10080000 and len(blocks)==1008}
out=ROOT/'environment'/('audit_'+args.run_id+'.json');out.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
