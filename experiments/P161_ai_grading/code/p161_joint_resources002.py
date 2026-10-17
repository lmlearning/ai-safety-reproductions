"""P161 complete joint storage; native calls only after actual ROOT authority.
Other-group algorithm is exact P160 source. P157 allocation API is pinned.
All observations are sampled/non-atomic; no global quota guarantee.
"""
from pathlib import Path
import importlib.util,json,os,shutil,stat,time
ROOT=Path('{{REPRODUCTION_ROOT}}')
OUT=ROOT/'runs/P161_complete_original002'
MiB=1024**2
GiB=1024**3
H=None

def require(ok,text):
    if not ok:raise RuntimeError(text)

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


class Joint:
    def __init__(self,cfg,work,deadline,clock):
        global H
        self.cfg=cfg;self.work=work;self.deadline=deadline;self.clock=clock;self.last=-1e30;self.last_full=None
        prior=cfg['charged_prior_output_roots']
        require(prior==[str(ROOT/'runs/P161_complete_original001'),str(ROOT/'runs/P161_complete_original001_meta')],'Exactly two prior failed roots remain charged')
        self.roots=[Path(cfg['output_root']),Path(cfg['metadata_root'])]+[Path(p)for p in prior]
        self.a={'_joint':{'other_owned_output_groups':cfg['other_owned_output_groups']}}
        ref=cfg['allocation_helper_ref'];p=Path(ref['path']);import hashlib
        require(p.stat().st_size==ref['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256'],'Exact source-reviewed P157 allocator')
        spec=importlib.util.spec_from_file_location('P161_PINNED_ALLOCATION_HELPER',p);H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
        self.native=H.Native()
    def phase(self,closure=False):
        require(self.clock()<(self.deadline if closure else self.work),'One original540 work/600 inclusive cutoff')
    def own_logical(self):
        total=files=dirs=0
        for root in self.roots:
            if not root.exists():continue
            H.safe_root(root);stack=[root]
            while stack:
                p=stack.pop();s=p.lstat();d=stat.S_ISDIR(s.st_mode)
                require(not stat.S_ISLNK(s.st_mode)and not getattr(s,'st_file_attributes',0)&0x400 and p.resolve().is_relative_to(root.resolve()),'Owned path reparse/escape')
                require(d or stat.S_ISREG(s.st_mode),'Owned ordinary object only')
                if d:
                    dirs+=1;require(dirs<=4096,'Owned4096directory cap');stack.extend(p.iterdir())
                else:
                    files+=1;require(files<=10000 and s.st_nlink==1,'Owned10000 single-link regular files');total+=s.st_size
        require(total<=self.cfg['joint_output_bytes'],'Whole64MiB scientific/metadata/TEMP/log pool')
        return {'logical':total,'files':files,'directories':dirs}
    def full(self):
        physical=charged=logical=files=dirs=0
        for root in self.roots:
            if not root.exists():continue
            H.safe_root(root);stack=[root]
            while stack:
                p=stack.pop();s=p.lstat();d=stat.S_ISDIR(s.st_mode)
                require(not stat.S_ISLNK(s.st_mode)and not getattr(s,'st_file_attributes',0)&0x400 and p.resolve().is_relative_to(root.resolve()),'Owned physical reparse/escape')
                require(d or stat.S_ISREG(s.st_mode),'Owned physical ordinary object only');m=self.native.allocation(p,d);physical+=m['physical']
                if d:
                    dirs+=1;require(dirs<=4096,'Owned physical directory cap');stack.extend(p.iterdir())
                else:
                    files+=1;require(files<=10000 and m['links']==1,'Owned physical single-link file cap');logical+=s.st_size;charged+=max(s.st_size,m['standard_allocation'])
        cap=self.cfg['joint_output_bytes'];require(max(physical,charged,logical)<=cap,'All owned logical/charged/nativephysical<=64MiB')
        others=other_reservations(self.native,self.a)
        return dict(physical=physical,charged=charged,logical=logical,files=files,directories=dirs,other_groups=others,observed_monotonic=time.monotonic())
    def observe(self,force=False,closure=False):
        self.phase(closure);logical=self.own_logical();full=None
        if force or self.last_full is None or time.monotonic()-self.last>=30:
            full=self.full();self.last_full=full;self.last=time.monotonic()
        cached=self.last_full;cap=self.cfg['joint_output_bytes'];floor=self.cfg['disk_floor_bytes']
        physical_required=floor+max(0,cap-cached['physical'])+sum(r['unspent']for r in cached['other_groups'])+self.cfg['ROOT_outside_bytes']
        logical_required=floor+max(0,cap-logical['logical'])+self.cfg['ROOT_outside_bytes']
        required=max(physical_required,logical_required);free=shutil.disk_usage(str(ROOT)).free
        row=dict(whole_owned_logical=logical,complete_native_storage=full,last_complete_native_UTC_or_monotonic=cached['observed_monotonic'],required_free_bytes=required,actual_free_bytes=free,
            all_other_groups_names=[r['name']for r in cached['other_groups']],native_census_max_interval_seconds=30,sampled_nonatomic=True,foreign_future_write_guarantee=False)
        require(free>=required,'Complete own+all4 other unspent reservations: '+json.dumps(row,separators=(',',':')))
        self.phase(closure);return row
