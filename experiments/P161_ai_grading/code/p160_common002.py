"""Dormant scoped P160 authority/resources; no numerical imports at module load."""
import datetime as dt,hashlib,importlib.util,json,os,shutil,stat,sys,time
from pathlib import Path
ROOT=Path('{{REPRODUCTION_ROOT}}');SOURCE=Path(__file__).absolute().parent
OUT=ROOT/'runs/P160_complete_hiring001';B=ROOT/'literature/root_additional_correlation_and_source_screen_oct15_003/correlated_original_v1_material277'
GiB=1024**3;MiB=1024**2;WHOLE=int(2.75*GiB);FLOOR=35*GiB
CAPS={'binary':2144000000,'rng':64*MiB,'systemic':16*MiB,'scalar':64*MiB,'dependencies':400*MiB,'metadata':160*MiB,'temp_cache':16*MiB}
JOINT_GROUPS=[
 {'name':'P157_input4GiB','cap_bytes':4*GiB,'roots':[str(ROOT/'papers/P157_loop_think_generalize/inputs/acquisition001')],'file_selectors':[]},
 {'name':'P157_science14GiB','cap_bytes':14*GiB,'roots':[str(ROOT/'runs/P157_complete_main001')],'file_selectors':[]},
 {'name':'P019_joint2GiB','cap_bytes':2*GiB,'roots':[str(ROOT/'runs/P019_g9_complete_original001'),str(ROOT/'runs/P019_g9_complete_original001_meta')],'file_selectors':[{'parent':str(ROOT/'environment'),'prefix':'toolsafe_audit_P019_g9_complete_original001_','suffix':'.json','maximum_files':1}]}]
HELPER=ROOT/'papers/P157_loop_think_generalize/review/source_preparation001/p157_common001.py'
sp=importlib.util.spec_from_file_location('p160_existing_native002',HELPER);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
pin=H.pin;verify=H.verify
def utc():return dt.datetime.now(dt.timezone.utc)
def require(ok,text):
 if not ok:raise RuntimeError(text)
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 enc=json.JSONEncoder(indent=2,allow_nan=False,ensure_ascii=True);count=1;h=hashlib.sha256()
 for s in enc.iterencode(v):b=s.encode('ascii');count+=len(b);h.update(b)
 h.update(b'\n');preview(p,count);written=0;actual=hashlib.sha256()
 with p.open('xb')as f:
  for s in enc.iterencode(v):
   b=s.encode('ascii');require(f.write(b)==len(b),'Complete bounded JSON write');written+=len(b);actual.update(b)
  require(f.write(b'\n')==1,'Complete newline');written+=1;actual.update(b'\n')
 require(written==count and actual.digest()==h.digest(),'Exact two-pass JSON bytes')
 return pin(p)
def preview(path,extra):
 path=Path(path).absolute();require(path.is_relative_to(OUT),'All programme output owned');rel=path.relative_to(OUT).parts;k=rel[0]if rel and rel[0]in CAPS else'metadata';root=OUT/k
 total=sum(p.stat().st_size for p in root.rglob('*')if p.is_file())if root.exists()else 0
 require(total+extra<=CAPS[k],'Finite '+k+' logical writer reservation')
def append(p,v,cap=4096):
 raw=(json.dumps(v,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('ascii');require(len(raw)<=cap,'Complete record exceeds finite bound')
 preview(p,len(raw))
 with Path(p).open('ab')as f:require(f.write(raw)==len(raw),'Short complete record')
def grant(path,phase,explicit):
 require(explicit and phase in('primary','audit'),'Explicit ROOT current phase command required')
 a=json.loads(Path(path).read_bytes());require(a.get('execution_authorized')is True and a.get('schema')=='P160_COMPLETE_HIRING24H_GRANT002','No P160 clock or authority')
 require(a['total_seconds']==86400 and a['phase_authorized']==phase,'Finite declared current phase only')
 r=json.loads(verify(a['source_review_ref']).read_bytes());require(r.get('ROOT_complete_P160_source_review_passed')is True and r['current_source_packet_ref']==a['source_packet_ref'],'Current whole source review')
 packet=json.loads(verify(a['source_packet_ref']).read_bytes())
 for x in packet['current_source_refs']:verify(x)
 require(a['frozen_input_refs']==packet['frozen_input_refs'],'Complete fixed original input/criterion/source set')
 for x in a['frozen_input_refs']:verify(x)
 joint=json.loads(verify(a['ROOT_joint_current_resource_review_ref']).read_bytes());require(joint.get('ROOT_complete_current_joint_reservations_reviewed')is True and joint.get('other_active_programme_reservations_complete')is True,'Complete prospective joint programme reservations required');require(json.dumps(joint['other_owned_output_groups'],sort_keys=True)==json.dumps(JOINT_GROUPS,sort_keys=True),'Exact approved P1574+14 and single aggregate P0192GiB joint groups');rr=json.loads(verify(a['runtime_review_ref']).read_bytes())
 require(rr.get('ROOT_private_author_OLS_runtime_source_review_passed')is True,'Actual exact private wheel source/compatibility review absent')
 require(rr['current_runtime_source_manifest_ref']==packet['runtime_source_manifest_ref'],'Exact reviewed study-private runtime source mapping');rm=json.loads(verify(packet['runtime_source_manifest_ref']).read_bytes());require(rr['all_runtime_payload_refs']==rm['all_runtime_payload_refs']and rr['actual_frozen_versions']==rm['actual_frozen_versions'],'No unreviewed private payload/version substitution')
 for x in rr['all_runtime_source_and_distribution_refs']:verify(x)
 start=dt.datetime.fromisoformat(a['origin_UTC']);end=dt.datetime.fromisoformat(a['deadline_UTC'])
 require(start.tzinfo is not None and end-start==dt.timedelta(seconds=86400),'No renewed or unbounded programme origin')
 cutoff=min(end,start+dt.timedelta(seconds=64800 if phase=='primary'else 82800))
 require(start<=utc()<cutoff,'Actual fixed phase cutoff')
 if phase=='audit':
  first=json.loads(verify(a['initial_primary_grant_ref']).read_bytes());require(first['phase_authorized']=='primary'and all(a[k]==first[k]for k in('origin_UTC','deadline_UTC','total_seconds','source_packet_ref','runtime_review_ref')),'No new audit origin/source/runtime authority')
  t=json.loads(verify(a['closed_primary_terminal_ref']).read_bytes());verify(a['complete_primary_manifest_ref'])
  require(t['child_Popen_exit']==0 and t['child_terminal']['native_exit_or_STILL_ACTIVE']==0 and t['failure']is None and t['handle_closed']is True and not t['cleanup_errors'],'Actual closed primary required')
 require(a['whole_output_bytes']==WHOLE and a['bucket_caps']==CAPS,'Complete finite writer allocation changed')
 a.update(_phase=phase,_start=start,_cutoff=cutoff,_work_cutoff=cutoff-dt.timedelta(seconds=120),_packet=packet,_runtime=rr,_joint=joint,_authority_ref=pin(path));return a
def census(n,a):
 rows={k:{'logical':0,'charged':0,'physical':0}for k in CAPS};files=dirs=0
 if OUT.exists():
  H.safe_root(OUT);stack=[OUT]
  while stack:
   p=stack.pop();s=p.lstat();require(not stat.S_ISLNK(s.st_mode)and not getattr(s,'st_file_attributes',0)&0x400,'Owned reparse path');require(p.resolve().is_relative_to(OUT.resolve()),'Owned escape')
   d=stat.S_ISDIR(s.st_mode);require(d or stat.S_ISREG(s.st_mode),'Nonregular owned object');parts=p.relative_to(OUT).parts;k=parts[0]if parts and parts[0]in CAPS else'metadata';m=n.allocation(p,d);rows[k]['physical']+=m['physical']
   if d:dirs+=1;require(dirs<=4096,'4096directory cap');stack.extend(p.iterdir())
   else:files+=1;require(files<=16384 and m['links']==1,'Finite regular single-link output census');rows[k]['logical']+=s.st_size;rows[k]['charged']+=max(s.st_size,m['standard_allocation'])
 for k,x in rows.items():require(x['charged']<=CAPS[k]and x['physical']<=CAPS[k],'Complete '+k+' bucket overflow')
 actual=sum(x['physical']for x in rows.values());charged=sum(x['charged']for x in rows.values());free=shutil.disk_usage(str(ROOT)).free
 others=other_reservations(n,a)
 required=FLOOR+max(0,WHOLE-actual)+sum(r['unspent']for r in others);free=shutil.disk_usage(str(ROOT)).free
 require(actual<=WHOLE and charged<=WHOLE and free>=required,'Complete2.75GiB and35GiB plus ALL joint unspent native allocations: '+json.dumps({'own':rows,'other':others,'free':free,'required':required},separators=(',',':')))
 return {'buckets':rows,'files':files,'directories':dirs,'physical':actual,'charged':charged,'free':free,'required_free':required,'other_joint_roots':others,'atomic_global_quota':False}
def other_reservations(n,a):
 groups=a['_joint']['other_owned_output_groups'];require(len(groups)<=16,'Finite joint groups');rows=[];allroots=[];allseen=set();names=set()
 for group in groups:
  name=group['name'];cap=group['cap_bytes'];require(isinstance(name,str)and name not in names and type(cap)is int and cap>=0,'Exact unique group/cap');names.add(name);roots=[Path(x).absolute()for x in group['roots']];require(len(roots)<=16 and len(group['file_selectors'])<=4,'Finite complete group membership');stack=[];extras=[]
  for root in roots:
   require(root.is_relative_to(ROOT)and not root.is_relative_to(OUT)and not OUT.is_relative_to(root),'Separate approved joint root containment');require(all(not root.is_relative_to(x)and not x.is_relative_to(root)for x in allroots),'No nested or overlapping joint roots');allroots.append(root)
   if root.exists():H.safe_root(root);stack.append((root,root,False))
  for selector in group['file_selectors']:
   parent=Path(selector['parent']).absolute();prefix=selector['prefix'];suffix=selector['suffix'];bound=selector['maximum_files'];require(parent.is_relative_to(ROOT)and not parent.is_relative_to(OUT)and type(bound)is int and 0<=bound<=16 and isinstance(prefix,str)and prefix and not any(x in prefix for x in('*','?','/','\\'))and isinstance(suffix,str)and suffix.startswith('.')and not any(x in suffix for x in('*','?','/','\\')),'Exact bounded file selector');H.safe_root(parent)
   selected=sorted((p for p in parent.iterdir()if p.name.startswith(prefix)and p.name.endswith(suffix)),key=lambda p:p.name);require(len(selected)<=bound,'Whole joint selected-artifact cardinality');extras.extend(str(p)for p in selected);stack.extend((p,parent,True)for p in selected)
  physical=charge=count=0
  while stack:
   p,owner,selected=stack.pop();s=p.lstat();resolved=p.resolve();key=str(resolved).casefold();require(key not in allseen,'No joint file/directory double counting');allseen.add(key);require(not stat.S_ISLNK(s.st_mode)and not getattr(s,'st_file_attributes',0)&0x400 and resolved.is_relative_to(owner.resolve()),'Joint group reparse/escape');d=stat.S_ISDIR(s.st_mode);require((d or stat.S_ISREG(s.st_mode))and not(selected and d),'Complete joint ordinary object/artifact type');m=n.allocation(p,d);physical+=m['physical'];count+=1;require(count<=20000,'Finite complete joint group census')
   if d:stack.extend((q,owner,False)for q in p.iterdir())
   else:require(m['links']==1,'No joint hardlink alias/double allocation');charge+=max(s.st_size,m['standard_allocation'])
  require(physical<=cap and charge<=cap,'ONE complete separately admitted joint group cap');rows.append({'name':name,'roots':list(map(str,roots)),'selected_extra_files':extras,'cap':cap,'physical':physical,'charged':charge,'objects':count,'unspent':max(0,cap-physical)})
 return rows
class Guard:
 def __init__(self,a,meta,parent=False):self.a=a;self.meta=Path(meta);self.parent=parent;self.n=H.Native();self.last=-1e30;self.lastdisk=-1e30;self.samples=0
 def observe(self,label,full=False,child=None):
  disk=census(self.n,self.a)if full else None;n=self.n.read();ws=max(n['working'],n['peak_working']);private=max(n['private'],n['peak_pagefile'])
  if child is not None:ws+=max(child['working'],child['peak_working']);private+=max(child['private'],child['peak_pagefile'])
  bad=[]
  if ws>2*GiB or private>4*GiB:bad.append('Whole current retained pair2GiB working/4GiB private')
  if self.parent and max(n['working'],n['peak_working'])>64*MiB:bad.append('Parent64MiB')
  if n['available_RAM']<GiB or n['available_commit']<4*GiB:bad.append('Continuous1GiB RAM/4GiB commit')
  if utc()>=self.a['_cutoff']:bad.append('Actual phase deadline after observations')
  return {'UTC':utc().isoformat(),'label':label,'native':n,'child':child,'storage':disk,'elapsed':(utc()-self.a['_start']).total_seconds(),'violations':bad}
 def check(self,label,force=False,child=None):
  require(utc()<self.a['_cutoff'],'Absolute fixed phase cutoff')
  if not force and time.monotonic()-self.last<5:return
  full=force or time.monotonic()-self.lastdisk>=30;row=self.observe(label,full,child)
  if full:self.lastdisk=time.monotonic()
  self.samples+=1;require(self.samples<=17296,'Complete finite resource-record count');append(self.meta/'resources.jsonl',row,4096);self.last=time.monotonic();require(not row['violations'],'Captured resource stop: '+json.dumps(row,separators=(',',':')))
def runtime(a):
 rr=a['_runtime'];owned=OUT/'dependencies/runtime';private=owned/'site-packages';cpu=ROOT/'environment/p092_cpu_stage_001/venv/Lib/site-packages';host=Path(sys.base_prefix)/'Lib/site-packages'
 total=0
 seen=set()
 for row in rr['all_runtime_payload_refs']:
  ref=row['ref'];src=verify(ref);rel=Path(row['owned_relative']);require(not rel.is_absolute()and'..'not in rel.parts and str(rel).casefold()not in seen,'Exact unique staged runtime path containment');seen.add(str(rel).casefold());dst=owned/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():
   require(a['_phase']=='primary','Audit cannot create new runtime input');shutil.copyfile(src,dst)
  actual=pin(dst);require((actual['bytes'],actual['sha256'])==(ref['bytes'],ref['sha256']),'Complete copied private runtime payload');total+=actual['bytes']
 require(total<=320*MiB,'Complete wheels+extracted runtime320MiB suballocation')
 sys.path[:]=[str(SOURCE),str(private),str(cpu),str(host),str(Path(sys.base_prefix)/'Lib'),str(Path(sys.base_prefix)/'DLLs'),str(Path(sys.base_prefix)/'python312.zip')]
 import numpy as np,pandas as pd,scipy,statsmodels.formula.api as smf
 import statsmodels,patsy
 actual={'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__,'patsy':patsy.__version__}
 require(actual==rr['actual_frozen_versions']and actual['statsmodels']=='0.14.4'and actual['patsy']=='1.0.1'and actual['scipy']=='1.15.3','Exact reviewed numerical runtime versions')
 require(all(Path(m.__file__).is_relative_to(private)for m in(scipy,statsmodels,patsy)),'Private original OLS/SciPy origin')
 save(OUT/'metadata'/('ACTUAL_'+a['_phase']+'_RUNTIME.json'),{'versions':actual,'origins':{k:str(m.__file__)for k,m in(('numpy',np),('pandas',pd),('scipy',scipy),('statsmodels',statsmodels),('patsy',patsy))},'original_OS_BLAS_Python_identity_not_claimed':True})
 return np,pd,smf
