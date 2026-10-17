"""Independent P135 block auditor mathematics. Source-only staged; never import the matrix primary."""
from decimal import Decimal, localcontext, getcontext
import math,json,hashlib,sys,os,time
from pathlib import Path
import mpmath as mp
getcontext().prec=80
mp.mp.dps=80
D=Decimal
ZERO=D(0);ONE=D(1);TWO=D(2)
PI=D("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628")
TCACHE={}
def char_csv(path):
 s=Path(path).read_text(encoding="utf-8-sig")
 records=[];row=[];cell=[];quoted=False;i=0
 while i<len(s):
  c=s[i]
  if quoted:
   if c=='"':
    if i+1<len(s) and s[i+1]=='"':cell.append('"');i+=1
    else:quoted=False
   else:cell.append(c)
  elif c=='"' and not cell:quoted=True
  elif c==",":row.append("".join(cell));cell=[]
  elif c=="\n":
   row.append("".join(cell));cell=[]
   if row!=[""]:records.append(row)
   row=[]
  elif c!="\r":cell.append(c)
  i+=1
 if quoted:raise ValueError("Unclosed original CSV quotation")
 if cell or row:row.append("".join(cell));records.append(row)
 if not records:raise ValueError("Empty CSV")
 keys=records[0]
 if len(set(keys))!=len(keys):raise ValueError("Duplicate header")
 if any(len(r)!=len(keys) for r in records[1:]):raise ValueError("CSV geometry")
 return [dict(zip(keys,r)) for r in records[1:]]
def dot(x,y):return sum((a*b for a,b in zip(x,y)),ZERO)
def invert(a):
 n=len(a);b=[[D(x) for x in r]+[ONE if i==j else ZERO for j in range(n)] for i,r in enumerate(a)]
 det=ONE
 for j in range(n):
  pivot=max(range(j,n),key=lambda i:abs(b[i][j]))
  if abs(b[pivot][j])<D("1e-60"):raise ArithmeticError("Singular fixed design")
  if pivot!=j:b[j],b[pivot]=b[pivot],b[j];det=-det
  v=b[j][j];det*=v;b[j]=[z/v for z in b[j]]
  for i in range(n):
   if i!=j:
    v=b[i][j];b[i]=[q-v*r for q,r in zip(b[i],b[j])]
 if det<=0:raise ArithmeticError("Nonpositive information determinant")
 return [r[n:] for r in b],det
def mv(a,x):return [dot(r,x) for r in a]
def atan_decimal(x):
 sign=-ONE if x<0 else ONE;x=abs(x)
 reciprocal=x>ONE
 if reciprocal:x=ONE/x
 factor=ONE
 while x>D(".1"):x=x/(ONE+(ONE+x*x).sqrt());factor*=TWO
 term=x;val=x;n=1
 while True:
  term*=-x*x;n+=2;inc=term/D(n);val+=inc
  if abs(inc)<D("1e-76"):break
 val*=factor
 if reciprocal:val=PI/TWO-val
 return sign*val
def student_p(t,df):
 if df<=0:raise ArithmeticError("No residual t degrees of freedom")
 t=abs(D(t))
 if t==0:return ONE
 nu=D(df);x=t/nu.sqrt();theta=atan_decimal(x)
 sin=x/(ONE+x*x).sqrt();cos=ONE/(ONE+x*x).sqrt()
 m=df-1
 if m%2==0:
  integral=theta;start=2
 else:integral=sin;start=3
 for j in range(start,m+1,2):integral=sin*(cos**(j-1))/D(j)+D(j-1)/D(j)*integral
 if df%2:
  r=(df-1)//2;c=D(4**r*math.factorial(r)**2)/(PI*D(math.factorial(2*r)))
 else:
  r=df//2;c=D(math.factorial(2*r))/D(4**r*math.factorial(r)*math.factorial(r-1))
 return max(ZERO,min(ONE,ONE-TWO*c*integral))
def student_critical(df):
 if df not in TCACHE:
  lo=ZERO;hi=ONE
  while student_p(hi,df)>D(".05"):hi*=TWO
  for _ in range(100):
   mid=(lo+hi)/TWO
   if student_p(mid,df)>D(".05"):lo=mid
   else:hi=mid
  TCACHE[df]=(lo+hi)/TWO
 return TCACHE[df]
def chi_p(q,df):
 if df<=0:return None
 x=mp.mpf(str(max(ZERO,q)))/2
 return D(str(mp.gammainc(mp.mpf(df)/2,x,mp.inf,regularized=True)))
def f_p(f,df1,df2):
 if df1<=0 or df2<=0:return None
 x=mp.mpf(df2)/(df2+df1*mp.mpf(str(max(ZERO,f))))
 return D(str(mp.betainc(mp.mpf(df2)/2,mp.mpf(df1)/2,0,x,regularized=True)))
def normal_p(t):return D(str(mp.erfc(abs(mp.mpf(str(t)))/mp.sqrt(2))))
def sampling(rows,y,kind="LS"):
 out=[]
 for r,g in zip(rows,y):
  n1=D(r["intervention_n"]);n2=D(r["control_n"]);n=n1+n2
  if n1<=0 or n2<=0:raise ValueError("Nonpositive exact N")
  base=ONE/n1+ONE/n2
  if kind=="LS":v=base+g*g/(TWO*n)
  elif kind in ["LS2","UB"]:
   m=n-TWO;J=D(str(mp.gamma(mp.mpf(str(m))/2)/(mp.sqrt(mp.mpf(str(m))/2)*mp.gamma((mp.mpf(str(m))-1)/2))))
   if kind=="LS2":v=J*J*base+g*g/(TWO*n)
   else:v=base+(ONE-(m-TWO)/(m*J*J))*g*g
  elif kind=="CI_derived":
   v=((D(r["printed_CI_high"])-D(r["printed_CI_low"]))/(D("3.92")))**2
  else:raise ValueError("Unknown sampling variance control")
  if v<=0:raise ArithmeticError("Nonpositive sampling variance")
  out.append(v)
 return out
class Block:
 def __init__(self,y,v,keys,X=None):
  self.y=list(y);self.v=list(v);self.keys=list(keys);self.k=len(y)
  self.X=[[ONE] for _ in y] if X is None else [[D(z) for z in r] for r in X]
  self.p=len(self.X[0]);self.groups=[]
  for key in dict.fromkeys(keys):self.groups.append([i for i,k in enumerate(keys) if k==key])
  self.identifiable=any(len(g)>1 for g in self.groups)
  self.cols=[[r[j] for r in self.X] for j in range(self.p)]
 def evaluate(self,a,b,gradient=True):
  a=D(a);b=D(b)
  if a<0 or b<0:raise ArithmeticError("Negative variance component")
  w=[ONE/(v+a) for v in self.v]
  denominators=[ONE+b*sum((w[i] for i in ix),ZERO) for ix in self.groups]
  def precision(z):
   ans=[w[i]*z[i] for i in range(self.k)]
   for ix,den in zip(self.groups,denominators):
    weighted=sum((w[i]*z[i] for i in ix),ZERO)
    for i in ix:ans[i]-=b*w[i]*weighted/den
   return ans
  U=[precision(x) for x in self.cols];uy=precision(self.y)
  A=[[dot(x,u) for u in U] for x in self.cols]
  inverse,det=invert(A);B=[dot(x,uy) for x in self.cols];coef=mv(inverse,B)
  residual=dot(self.y,uy)-dot(B,coef)
  if residual<0 and residual>D("-1e-50"):residual=ZERO
  if residual<0:raise ArithmeticError("Negative generalized residual")
  ld=sum(((v+a).ln() for v in self.v),ZERO)+sum((z.ln() for z in denominators),ZERO)
  objective=(ld+det.ln()+residual)/TWO
  result={"nll":objective,"coefficients":coef,"covariance":inverse,"weights":w,"denominators":denominators}
  if gradient:
   rp=[uy[i]-sum((U[j][i]*coef[j] for j in range(self.p)),ZERO) for i in range(self.k)]
   tracea=sum(w,ZERO)-sum((b*sum((w[i]*w[i] for i in ix),ZERO)/den for ix,den in zip(self.groups,denominators)),ZERO)
   traceb=sum((sum((w[i] for i in ix),ZERO)/den for ix,den in zip(self.groups,denominators)),ZERO)
   corr_a=sum((inverse[c][d]*dot(U[c],U[d]) for c in range(self.p) for d in range(self.p)),ZERO)
   sums=[[sum((u[i] for i in ix),ZERO) for u in U] for ix in self.groups]
   corr_b=sum((inverse[c][d]*sum((z[c]*z[d] for z in sums),ZERO) for c in range(self.p) for d in range(self.p)),ZERO)
   scorea=(tracea-corr_a-dot(rp,rp))/TWO
   scoreb=(traceb-corr_b-sum((sum((rp[i] for i in ix),ZERO)**2 for ix in self.groups),ZERO))/TWO
   result["gradient"]=[scorea,scoreb]
  return result
def projected(theta,gradient,U):
 return [ZERO if (x==0 and g>=0) or (x==U and g<=0) else g for x,g in zip(theta,gradient)]
def optimize(block,ordinary=False):
 mean=sum(block.y,ZERO)/D(block.k);popvar=sum(((z-mean)**2 for z in block.y),ZERO)/D(block.k)
 U=max(ONE,D(100)*popvar);candidates=[]
 def candidate(theta,kind,iterations):
  out=block.evaluate(*theta);pg=projected(theta,out["gradient"],U)
  if ordinary:pg[1]=ZERO
  out.update({"a":theta[0],"b":theta[1],"kind":kind,"iterations":iterations,
   "projected_gradient":max(abs(x) for x in pg),"upper_bound":U,
   "upper_hit":any(x>=U-D("1e-7") for x in theta)})
  candidates.append(out);return out
 for xy in [(ZERO,ZERO),(ZERO,U),(U,ZERO),(U,U)]:
  if not ordinary or xy[1]==0:candidate(xy,"corner",0)
 # Independent boundary derivative brackets, not a borrowed matrix optimizer.
 fractions=[ZERO,D("1e-8"),D("1e-6"),D(".0001"),D(".001"),D(".01"),D(".05"),D(".1"),D(".25"),D(".5"),D(".75"),ONE]
 for axis in ([0] if ordinary else [0,1]):
  grid=[U*z for z in fractions];scores=[]
  for x in grid:
   theta=[ZERO,ZERO];theta[axis]=x;scores.append(block.evaluate(*theta)["gradient"][axis])
  for j in range(len(grid)-1):
   if scores[j]*scores[j+1]<=0:
    lo=grid[j];hi=grid[j+1];gl=scores[j]
    for n in range(100):
     mid=(lo+hi)/TWO;theta=[ZERO,ZERO];theta[axis]=mid
     gm=block.evaluate(*theta)["gradient"][axis]
     if abs(gm)<D("1e-24"):lo=hi=mid;break
     if gm*gl>0:lo=mid;gl=gm
     else:hi=mid
    theta=[ZERO,ZERO];theta[axis]=(lo+hi)/TWO;candidate(theta,"boundary_root",n+1)
 if block.identifiable and not ordinary:
  starts=[(".0001",".0001"),(".01",".01"),(".1",".1"),(".5",".5"),(".01",".5"),(".5",".01")]
  for sa,sb in starts:
   theta=[U*D(sa),U*D(sb)]
   for iteration in range(180):
    out=block.evaluate(*theta);g=out["gradient"];pg=projected(theta,g,U)
    if max(abs(z) for z in pg)<D("1e-18"):break
    free=[j for j in range(2) if pg[j]!=0];H=[[ZERO,ZERO],[ZERO,ZERO]]
    for j in free:
     h=D("1e-12")*(ONE+theta[j]);low=max(ZERO,theta[j]-h);high=min(U,theta[j]+h)
     xp=theta.copy();xm=theta.copy();xp[j]=high;xm[j]=low
     gp=block.evaluate(*xp)["gradient"];gm=block.evaluate(*xm)["gradient"]
     for i in free:H[i][j]=(gp[i]-gm[i])/(high-low)
    step=[ZERO,ZERO]
    if len(free)==1:
     j=free[0];step[j]=-g[j]/H[j][j] if H[j][j]>0 else -g[j]/max(ONE,abs(g[j]))
    else:
     cross=(H[0][1]+H[1][0])/TWO;det=H[0][0]*H[1][1]-cross*cross
     if det>0 and H[0][0]>0 and H[1][1]>0:
      step=[(-H[1][1]*g[0]+cross*g[1])/det,(cross*g[0]-H[0][0]*g[1])/det]
     else:step=[-z/max(ONE,abs(g[0])+abs(g[1])) for z in pg]
    accepted=False
    alpha=ONE
    for _ in range(100):
     nxt=[min(U,max(ZERO,x+alpha*s)) for x,s in zip(theta,step)]
     if nxt==theta:break
     descent=dot(g,[n-x for n,x in zip(nxt,theta)])
     if descent<0 and block.evaluate(*nxt,gradient=False)["nll"]<=out["nll"]+D(".0001")*descent:
      theta=nxt;accepted=True;break
     alpha/=TWO
    if not accepted:break
   candidate(theta,"independent_projected_newton",iteration+1)
 selected=min(candidates,key=lambda r:(r["nll"],r["a"],r["b"]))
 if selected["upper_hit"] or selected["projected_gradient"]>D("1e-10"):raise ArithmeticError("Independent REML convergence failure")
 if not block.identifiable and not ordinary:
  total=selected["a"]+selected["b"];selected=block.evaluate(ZERO,total)
  selected.update({"a":ZERO,"b":total,"upper_bound":U,"upper_hit":False,"projected_gradient":abs(selected["gradient"][1])})
 selected=dict(selected);selected["candidates"]=candidates
 return selected
def fit(rows,y=None,kind="LS",X=None,ordinary=False):
 y=[D(r["printed_g"]) for r in rows] if y is None else list(y)
 v=sampling(rows,y,kind);keys=[r["study_key"] for r in rows];block=Block(y,v,keys,X)
 if len(rows)<=block.p:raise ArithmeticError("No residual degrees of freedom")
 selected=optimize(block,ordinary=ordinary);a=selected["a"];b=selected["b"];coef=selected["coefficients"];cov=selected["covariance"];df=block.k-block.p
 qref=Block(y,v,keys,block.X).evaluate(ZERO,ZERO)
 fixedcov=qref["covariance"];fixedcoef=qref["coefficients"]
 weighted=[z/vv for z,vv in zip(y,v)]
 Q=dot(y,weighted)-dot([dot(x,weighted) for x in block.cols],fixedcoef)
 if Q<0 and Q>D("-1e-50"):Q=ZERO
 W=[ONE/z for z in v];traceP=sum(W,ZERO)-sum((fixedcov[c][d]*sum((W[i]**2*block.cols[c][i]*block.cols[d][i] for i in range(block.k)),ZERO) for c in range(block.p) for d in range(block.p)),ZERO)
 typical=D(df)/traceP;g=coef[0];se=cov[0][0].sqrt();t=g/se;critical=student_critical(df)
 prec1=block.evaluate(a,b)["weights"];den=block.evaluate(a,b)["denominators"];roww=[ZERO]*block.k
 for ix,z in zip(block.groups,den):
  for i in ix:roww[i]=prec1[i]/z
 rowtotal=sum(roww,ZERO);roww=[D(100)*z/rowtotal for z in roww]
 if block.p>1:roww=None
 out={"k":block.k,"parameters":block.p,"trials":len(block.groups),"coefficients":coef,"covariance":cov,"df":df,
 "g":g,"SE":se,"CI_low":g-critical*se,"CI_high":g+critical*se,"t":t,"p_value":student_p(t,df),
 "a":a,"b":b,"total_tau2":a+b,"nll":selected["nll"],"Q":Q,"Q_df":df,"Q_p":chi_p(Q,df),
 "I2_Q":max(ZERO,(Q-D(df))/Q)*D(100) if Q>0 else ZERO,
 "I2_components":D(100)*(a+b)/(a+b+typical),"sampling_typical_variance":typical,"row_weights_percent":roww,
 "converged":True,"identifiability":"total_only_fixed_b_zero" if ordinary else "identified" if block.identifiable else "only_total_variance",
 "component_identifiable":block.identifiable and not ordinary,"projected_gradient":selected["projected_gradient"],
 "independent_optimizer_candidates":selected["candidates"]}
 return out,v

def direction(x):return "negative" if x<0 else "positive" if x>0 else "zero"
def classification(pool):
 lo=pool["CI_low"];hi=pool["CI_high"]
 return "negative_significant" if hi<0 else "positive_significant" if lo>0 else "crosses_zero"
def radical_inverse(index,base):
 x=ZERO;place=ONE/D(base)
 while index:
  index,remainder=divmod(index,base);x+=D(remainder)*place;place/=D(base)
 return x
def first_primes(k):
 result=[];n=2
 while len(result)<k:
  if all(n%p for p in result if p*p<=n):result.append(n)
  n+=1
 return result
def egger(rows):
 y=[D(r["printed_g"]) for r in rows];v=sampling(rows,y);n=len(rows)
 x=[ONE/z.sqrt() for z in v];z=[g/s.sqrt() for g,s in zip(y,v)]
 X=[[ONE,q] for q in x];cols=[[r[j] for r in X] for j in range(2)]
 A=[[dot(a,b) for b in cols] for a in cols];inverse,_=invert(A);coef=mv(inverse,[dot(c,z) for c in cols])
 residual=[zz-coef[0]-coef[1]*xx for zz,xx in zip(z,x)];sigma=dot(residual,residual)/D(n-2)
 se=(sigma*inverse[0][0]).sqrt();t=coef[0]/se
 return {"k":n,"intercept":coef[0],"SE":se,"t":t,"df":n-2,"p_value":student_p(t,n-2),"method":"unweighted standardized Egger OLS; exact original producer unavailable"}
def subgroup(rows,family,factor,metadata):
 # Public categories is the complete study assignment map, independently rebuilt from frozen rows/metadata.
 category_map={r["study_key"]:metadata["studies"][r["study_key"]][factor] for r in rows}
 for unavailable in metadata.get("unavailable_families",[]):
  if unavailable["family"]==family and unavailable["factor"]==factor:
   return {"status":"unavailable_original_split_arm_inputs","reason":unavailable["reason"],"categories":category_map,"omnibus":None,"groups":{},"full_moderator_pool":None}
 allocations=[metadata["studies"][r["study_key"]][factor] for r in rows]
 if any(x is None for x in allocations):raise ValueError("Missing original category; cannot impute")
 categories=[c for c in metadata["category_order"][factor] if c in allocations]
 if set(allocations)!=set(categories):raise ValueError("Unmapped original category")
 X=[[ONE]+[ONE if a==c else ZERO for c in categories[1:]] for a in allocations]
 pool,_=fit(rows,X=X);p=len(categories);coef=pool["coefficients"];cov=pool["covariance"];df=pool["df"]
 if p>1:
  contrast=[r[1:] for r in cov[1:]];inverse,_=invert(contrast);coef_test=coef[1:]
  F=dot(coef_test,mv(inverse,coef_test))/D(p-1)
  omnibus={"F":F,"df1":p-1,"df2":df,"p_value":f_p(F,p-1,df)}
 else:omnibus={"F":None,"df1":0,"df2":df,"p_value":None}
 groups={}
 for j,c in enumerate(categories):
  weights=[ONE]+[ONE if i==j else ZERO for i in range(1,p)]
  g=dot(weights,coef);se=dot(weights,mv(cov,weights)).sqrt();t=g/se;crit=student_critical(df)
  selected=[r for r,a in zip(rows,allocations) if a==c]
  groups[c]={"g":g,"SE":se,"CI_low":g-crit*se,"CI_high":g+crit*se,"t":t,"p_value":student_p(t,df),"trials":len(set(r["study_key"] for r in selected)),"effects":len(selected)}
 return {"status":"conventional_source_category_reconstruction","reason":"Joint source-cohort mixed model; original implementation unavailable","categories":category_map,"omnibus":omnibus,"groups":groups,"full_moderator_pool":pool}
def reconstruct_family(rows,family,metadata,probe_contract):
 y=[D(r["printed_g"]) for r in rows];k=len(y);mid,v=fit(rows,y);e=D(".005");h=D(".0001");fields=["g","CI_low","CI_high"]
 records=[];jrecords=[];Jacobian={q:[ZERO]*k for q in fields}
 def probe(delta,kind,ident,jacobian=False):
  p,_=fit(rows,[yy+dd for yy,dd in zip(y,delta)])
  record={"id":ident,"delta":delta,"pool":p}
  if not jacobian:record.update({"kind":kind,"point_direction":direction(p["g"]),"CI_classification":classification(p)})
  (jrecords if jacobian else records).append(record);return p
 # The final public probe contract fixes kinds/IDs; no matrix results become inputs.
 for i in range(k):
  plus=[ZERO]*k;minus=[ZERO]*k;plus[i]=h;minus[i]=-h
  b=probe(minus,probe_contract["jac_minus_kind"],probe_contract["jac_minus_id"].format(i=i+1),jacobian=True)
  a=probe(plus,probe_contract["jac_plus_kind"],probe_contract["jac_plus_id"].format(i=i+1),jacobian=True)
  for q in fields:Jacobian[q][i]=(a[q]-b[q])/(TWO*h)
 primes=first_primes(k)
 for index in range(1,65):
  point=[radical_inverse(index,p) for p in primes]
  for complement in [False,True]:
   delta=[(TWO*(ONE-u if complement else u)-ONE)*e for u in point]
   probe(delta,probe_contract["halton_complement_kind"] if complement else probe_contract["halton_kind"],
    (probe_contract["halton_complement_id"] if complement else probe_contract["halton_id"]).format(index=index))
 for i in range(k):
  for sign in [-1,1]:
   delta=[ZERO]*k;delta[i]=D(sign)*e
   probe(delta,probe_contract["coordinate_kind"],probe_contract["coordinate_id"].format(i=i+1,sign="minus" if sign<0 else "plus"))
 for sign in [-1,1]:probe([D(sign)*e]*k,probe_contract["uniform_kind"],probe_contract["uniform_id"].format(sign="minus" if sign<0 else "plus"))
 for q in fields:
  for sign in [-1,1]:
   delta=[D(sign)*e*(ONE if z>0 else -ONE if z<0 else ZERO) for z in Jacobian[q]]
   probe(delta,probe_contract["gradient_kind"],probe_contract["gradient_id"].format(q=q,sign="minus" if sign<0 else "plus"))
 radius={};allowance={}
 for q in fields:
  nonlinear=max((abs(r["pool"][q]-mid[q]-dot(Jacobian[q],r["delta"])) for r in records),default=ZERO)
  radius[q]=e*sum((abs(z) for z in Jacobian[q]),ZERO)+nonlinear
  allowance[q]=min(D(".02"),D(".005")+radius[q])+D("1e-9")
 outrows={}
 for i,(r,yy,vv) in enumerate(zip(rows,y,v)):
  se=vv.sqrt();outrows[r["row"]]={"row":r["row"],"study_key":r["study_key"],"g":yy,"variance":vv,"SE":se,"CI_low":yy-D("1.96")*se,"CI_high":yy+D("1.96")*se,"row_weight_percent":mid["row_weights_percent"][i]}
 loo={}
 for key in dict.fromkeys(r["study_key"] for r in rows):
  retained=[r for r in rows if r["study_key"]!=key];p,_=fit(retained)
  loo[key]={"pool":p,"remaining_row_ids":[r["row"] for r in retained],"point_direction":direction(p["g"]),"CI_classification":classification(p),"removed_trial_literal":metadata["studies"][key].get("leave_out_source_literal")}
 alternatives={}
 for kind in ["LS2","UB","CI_derived","ordinary_two_level_REML"]:
  p,vv=fit(rows,kind="LS" if kind=="ordinary_two_level_REML" else kind,ordinary=kind=="ordinary_two_level_REML")
  rr={}
  for i,(r,yy,s) in enumerate(zip(rows,y,vv)):
   se=s.sqrt();rr[r["row"]]={"row":r["row"],"study_key":r["study_key"],"g":yy,"variance":s,"SE":se,"CI_low":yy-D("1.96")*se,"CI_high":yy+D("1.96")*se,"row_weight_percent":p["row_weights_percent"][i]}
  alternatives[kind]={"pool":p,"rows":rr}
 return {"geometry":{"effects":k,"trials":len(set(r["study_key"] for r in rows)),"trial_keys":list(dict.fromkeys(r["study_key"] for r in rows)),"row_ids":[r["row"] for r in rows]},
  "primary":mid,"rows":outrows,"rounding":{"e":e,"h":h,"Halton_points":64,"Jacobian":Jacobian,"radius":radius,"allowance":allowance,"Jacobian_fit_records":jrecords,"probe_records":records,"finite_probe_allowance_not_rigorous_enclosure":True},
  "leave_one_trial_out":loo,"supporting":{"sampling_alternatives":alternatives,"egger":egger(rows),
   "subgroups":{factor:subgroup(rows,family,factor,metadata) for factor in metadata["category_order"]},"all_controls_supporting_only":True}}
def trial_key(literal):
 name=literal.lstrip("-").replace(" ","").replace("(","").replace(")","")
 return name
def primary_checks(result,targets):
 checks=[]
 def add(family,kind,source,target,actual,allowance=None):
  difference=abs(actual-D(str(target))) if isinstance(actual,(Decimal,int,float)) and not isinstance(actual,bool) else None
  passed=difference<=allowance if allowance is not None else actual==target
  checks.append({"id":f"primary_{len(checks)+1:03d}","family":family,"kind":kind,"source_literal":str(target),"target":target,"actual":actual,"allowance":allowance,"difference":difference,"passed":passed,"source":source})
 for family,target in targets["families"].items():
  r=result["families"][family];p=r["primary"]
  for q in ["g","CI_low","CI_high"]:add(family,q,"Original pooled source",D(target[q]),p[q],r["rounding"]["allowance"][q])
  point={"midpoint":direction(p["g"]),"all_fixed_probes":all(z["point_direction"]==target["point_direction"] for z in r["rounding"]["probe_records"])}
  classes={"midpoint":classification(p),"all_fixed_probes":all(z["CI_classification"]==target["CI_classification"] for z in r["rounding"]["probe_records"])}
  add(family,"point_direction","Original pooled source",{"midpoint":target["point_direction"],"all_fixed_probes":True},point)
  add(family,"CI_classification","Original pooled source",{"midpoint":target["CI_classification"],"all_fixed_probes":True},classes)
  add(family,"effects","Original forest complete geometry",target["effects"],r["geometry"]["effects"])
  add(family,"trials","Original forest complete geometry",target["trials"],r["geometry"]["trials"])
  for item in targets["all_whole_trial_leave_out_robustness_mandatory"][family]:
   key=trial_key(item["removed_trial_literal"])
   if key not in r["leave_one_trial_out"]:raise KeyError("Whole-trial source identity")
   r["leave_one_trial_out"][key]["removed_trial_literal"]=item["removed_trial_literal"]
   entry=r["leave_one_trial_out"][key]
   add(family,"LOO_point_direction:"+key,item["source"],item["point_direction"],entry["point_direction"])
   add(family,"LOO_CI_classification:"+key,item["source"],item["CI_classification"],entry["CI_classification"])
 if len(checks)!=50:raise ValueError("Complete mandatory gate geometry")
 return checks
def supporting_checks(result,source):
 checks=[]
 for target in source["checks"]:
  actual=result;missing=False
  try:
   for key in target["path"]:actual=actual[key]
  except (KeyError,TypeError):actual=None;missing=True
  difference=None;passed=False
  if not missing and actual is not None:
   if target["kind"]=="exact":passed=actual==D(str(target["target"]))
   else:
    val=D(actual);expected=D(str(target["target"]));difference=abs(val-expected)
    if target["relation"]=="<":passed=val<expected
    elif target["relation"]=="<=":passed=val<=expected
    elif target["relation"]==">":passed=val>expected
    elif target["relation"]==">=":passed=val>=expected
    else:passed=difference<=D(str(target["tolerance"]))
  checks.append(dict(target,actual=actual,difference=difference,passes_source_display=None if missing or actual is None else passed,unavailable=missing or actual is None,primary_rescue=False))
 return checks
def jsonable(x):
 if isinstance(x,Decimal):return float(x)
 if isinstance(x,dict):return {k:jsonable(v) for k,v in x.items()}
 if isinstance(x,list):return [jsonable(v) for v in x]
 return x

PROBE_CONTRACT={
 "jac_plus_kind":"Jacobian","jac_minus_kind":"Jacobian",
 "jac_plus_id":"Jacobian_{i:02d}_plus","jac_minus_id":"Jacobian_{i:02d}_minus",
 "halton_kind":"Halton","halton_complement_kind":"Halton_complement",
 "halton_id":"halton_{index:03d}","halton_complement_id":"complement_{index:03d}",
 "coordinate_kind":"coordinate_endpoint","coordinate_id":"coordinate_{i:02d}_{sign}",
 "uniform_kind":"uniform_corner","uniform_id":"uniform_{sign}",
 "gradient_kind":"gradient_sign_corner","gradient_id":"gradient_{q}_{sign}"
}
class AuditComparison:
 def __init__(self):self.checks=[]
 def add(self,label,main,independent,tolerance=None):
  if tolerance is None:passed=main==independent;difference=None
  else:
   try:
    x=D(str(main));y=D(str(independent));difference=abs(x-y);limit=D(tolerance)*max(ONE,abs(x),abs(y));passed=difference<=limit
   except (TypeError,ValueError,ArithmeticError):difference=None;passed=False
  self.checks.append({"id":label,"main":main,"independent":independent,"tolerance":tolerance,"difference":difference,"passed":passed})
 def tree(self,main,own,label="",pool=False):
  if isinstance(own,dict):
   if label.endswith("/categories"):
    if not isinstance(main,dict):self.add(label,"wrong_category_mapping_type",sorted(own));return
    self.add(label+"/complete_study_key_census",sorted(main),sorted(own))
   unidentifiable=own.get("component_identifiable") is False
   for key,val in own.items():
    if key in ["independent_optimizer_candidates","projected_gradient","identifiability","removed_trial_literal"]:continue
    if unidentifiable and key in ["a","b"]:continue
    if key not in main:self.add(label+"/"+key,"missing",val);continue
    self.tree(main[key],val,label+"/"+key,pool=pool)
  elif isinstance(own,list):
   if not isinstance(main,list):self.add(label,"wrong_array_type",len(own));return
   self.add(label+"/length",len(main),len(own))
   for i,(a,b) in enumerate(zip(main,own)):self.tree(a,b,label+f"/{i}",pool=pool)
  elif isinstance(own,Decimal):
   tol="1e-6" if label.rsplit("/",1)[-1] in ["a","b","total_tau2","nll"] else "1e-7"
   self.add(label,main,own,tol)
  else:self.add(label,main,own)
def exact_json(x):return str(x) if isinstance(x,Decimal) else x
def write_json(path,obj):
 p=Path(path)
 if p.exists():raise FileExistsError(p)
 p.write_text(json.dumps(obj,indent=2,ensure_ascii=True,default=exact_json)+"\n",encoding="utf-8")
def preflight(freeze_path,run,audit):
 freeze=json.loads(Path(freeze_path).read_text(encoding="utf-8"));references=freeze["files"]
 seen=set();self_seen=False
 for ref in references:
  p=Path(ref["absolute_path"]).resolve()
  if p in seen:raise ValueError("Duplicate frozen file")
  seen.add(p);b=p.read_bytes()
  if len(b)!=ref["bytes"] or hashlib.sha256(b).hexdigest()!=ref["sha256"]:raise ValueError("Frozen source/runtime changed:"+str(p))
  if p==Path(__file__).resolve():self_seen=True
 if not self_seen:raise ValueError("Independent executable absent from freeze")
 config=freeze["config"]
 if config["mode"] not in ["synthetic","original"]:raise ValueError("Mode")
 if config["mode"]=="synthetic":
  forbidden=(Path(__file__).resolve().parent.parent/"papers/P135_young_people_chatbot_meta").resolve()
  fixture=Path(config["input_root"]).resolve()
  if fixture!=forbidden/"synthetic_fixture001":raise ValueError("Isolated frozen synthetic input root required")
  for field in ["metadata_path","targets_path","supporting_targets_path","primary_descriptors_path","output_contract_path"]:
   if not Path(config[field]).resolve().is_relative_to(fixture):raise ValueError("Synthetic engine configuration leaves isolated fixture:"+field)
  allowed=[fixture,Path(run).resolve(),Path(audit).resolve()]
  original_dirs=[forbidden/x for x in ["sources","published_summary_transcription001","method_preparation001","independent_auditor_preparation001"]]
  for output in allowed[1:]:
   if output==forbidden or forbidden.is_relative_to(output) or any(output.is_relative_to(x) or x.is_relative_to(output) for x in original_dirs):
    raise ValueError("Synthetic output root overlaps original source")
  def hook(event,args):
   if event!="open":return
   raw=args[0]
   if not isinstance(raw,(str,bytes,os.PathLike)):return
   p=Path(os.fsdecode(raw)).resolve()
   # Fixture cannot open original mathematical inputs, outputs or labels.
   try:inside=p.is_relative_to(forbidden)
   except AttributeError:inside=str(p).casefold().startswith(str(forbidden).casefold()+os.sep)
   if inside and not any(p.is_relative_to(x) for x in allowed):raise PermissionError("Synthetic engine cannot read original P135 source:"+str(p))
  sys.addaudithook(hook)
 return freeze,config
def validate_original_metadata(metadata):
 from zipfile import ZipFile
 import xml.etree.ElementTree as ET
 path=Path(__file__).resolve().parent.parent/"papers/P135_young_people_chatbot_meta/sources/supplement_archive_contents002/WVN-22-0-s001.docx"
 with ZipFile(path) as z:root=ET.fromstring(z.read("word/document.xml"))
 ns={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
 original=[]
 for table in root.findall(".//w:tbl",ns):
  for row in table.findall("w:tr",ns):
   original.append(["".join(t.text or "" for t in cell.findall(".//w:t",ns)) for cell in row.findall("w:tc",ns)])
 for key,record in metadata["studies"].items():
  for field in ["source_S3","source_S4"]:
   if record[field] not in original:raise ValueError("Metadata row not literal original DOCX:"+key+":"+field)
  sample=record["source_S3"][3]
  expected="Nonclinical" if "Sample type: Nonclinical" in sample else "Clinical/subclinical" if "Sample type: Clinical" in sample or "Sample type: Subclinical" in sample else None
  if expected!=record["sample_type"]:raise ValueError("Independent sample category mismatch:"+key)
  raw=record["source_S4"][2]
  expected=next((c for c in ["Instant messenger","Mobile application","Web-based"] if raw.startswith(c)),None)
  if expected!=record["platform"]:raise ValueError("Independent platform category mismatch:"+key)
  if key=="Karhiy2023":
   if record["response_generation"] is not None or record["interaction_mode"] is not None:raise ValueError("Do not impute split arms")
  else:
   response=record["source_S4"][3]
   expected="AI-based" if response.startswith("AI-based") else "Rule-based" if response.startswith("Rule-based") else None
   if expected!=record["response_generation"]:raise ValueError("Independent response category mismatch:"+key)
   modalities=record["source_S4"][5]+" "+record["source_S4"][6]
   expected="Multimodal" if "Spoken" in modalities or "visual" in modalities.lower() else "Text-based"
   if expected!=record["interaction_mode"]:raise ValueError("Independent modality category mismatch:"+key)
def verify_main_manifest(run):
 manifest=json.loads((run/"OUTPUT_MANIFEST.json").read_text(encoding="utf-8"))
 entries=manifest if isinstance(manifest,list) else manifest.get("files",manifest.get("artifacts"))
 if not isinstance(entries,list):raise ValueError("Output manifest schema")
 listed=set()
 for r in entries:
  raw=r.get("absolute_path",r.get("path",r.get("name")))
  if raw is None:raise ValueError("Missing manifest path")
  p=Path(raw)
  if not p.is_absolute():p=run/p
  p=p.resolve()
  if not p.is_relative_to(run.resolve()):raise ValueError("Output reference outside run")
  if p in listed:raise ValueError("Duplicate output manifest file")
  listed.add(p);b=p.read_bytes()
  if len(b)!=r["bytes"] or hashlib.sha256(b).hexdigest()!=r["sha256"]:raise ValueError("Original output hash mismatch")
 for name in ["ALL_ORIGINAL_COMPUTATIONS.json","ALL50_PRIMARY_CHECKS.json","ALL_SUPPORTING_SOURCE_COMPARISONS.json","SUMMARY.json","NUMERICAL_OPTIMIZER_TRACE.json"]:
  if (run/name).resolve() not in listed:raise ValueError("Incomplete original output manifest")
 return len(listed)
def compare_families(main,own,comparison):
 comparison.add("mode",main["mode"],own["mode"])
 comparison.add("raw_source_records",main["raw_source_records"],own["raw_source_records"])
 comparison.add("metadata_used",main["metadata_used"],own["metadata_used"])
 comparison.add("complete_family_membership",sorted(main["families"]),sorted(own["families"]))
 for family,r in own["families"].items():
  m=main["families"][family];base="families/"+family
  comparison.add(base+"/geometry/effects",m["geometry"]["effects"],r["geometry"]["effects"])
  comparison.add(base+"/geometry/trials",m["geometry"]["trials"],r["geometry"]["trials"])
  comparison.add(base+"/geometry/row_ids",m["geometry"]["row_ids"],r["geometry"]["row_ids"])
  comparison.add(base+"/geometry/trial_keys",sorted(m["geometry"]["trial_keys"]),sorted(r["geometry"]["trial_keys"]))
  comparison.tree(m["primary"],r["primary"],base+"/primary",pool=True)
  comparison.tree(m["rows"],r["rows"],base+"/rows")
  for field in ["e","h","Halton_points","Jacobian","radius","allowance","finite_probe_allowance_not_rigorous_enclosure"]:
   comparison.tree(m["rounding"][field],r["rounding"][field],base+"/rounding/"+field)
  for field in ["Jacobian_fit_records","probe_records"]:
   comparison.add(base+"/"+field+"/count",len(m["rounding"][field]),len(r["rounding"][field]))
   comparison.add(base+"/"+field+"/ids",[x["id"] for x in m["rounding"][field]],[x["id"] for x in r["rounding"][field]])
   for i,(a,b) in enumerate(zip(m["rounding"][field],r["rounding"][field])):
    comparison.tree(a["delta"],b["delta"],base+f"/{field}/{i}/delta")
    comparison.tree(a["pool"],b["pool"],base+f"/{field}/{i}/pool",pool=True)
    if field=="probe_records":
     for label in ["kind","point_direction","CI_classification"]:comparison.add(base+f"/{field}/{i}/"+label,a[label],b[label])
  comparison.tree(m["leave_one_trial_out"],r["leave_one_trial_out"],base+"/leave_one_trial_out")
  comparison.tree(m["supporting"],r["supporting"],base+"/supporting")
def audit_entry(run,audit,freeze_path):
 audit=Path(audit);run=Path(run)
 if audit.exists():raise FileExistsError("Unique audit directory required")
 audit.mkdir(parents=True)
 began=time.time()
 try:
  freeze,config=preflight(freeze_path,run,audit);mode=config["mode"];manifest_count=verify_main_manifest(run)
  metadata=json.loads(Path(config["metadata_path"]).read_text(encoding="utf-8"))
  targets=json.loads(Path(config["targets_path"]).read_text(encoding="utf-8"))
  supporting=json.loads(Path(config["supporting_targets_path"]).read_text(encoding="utf-8"))
  if mode=="original":validate_original_metadata(metadata)
  raw={}
  for family,k,trials in [("psychological_distress",18,11),("psychological_wellbeing",8,7)]:
   file=Path(config["input_root"])/(family+"_published_effects_source001.csv")
   rows=char_csv(file)
   if len(rows)!=k or len(set(r["study_key"] for r in rows))!=trials:raise ValueError("Complete original geometry")
   if [r["row"] for r in rows]!=[str(i) for i in range(1,k+1)]:raise ValueError("Source-row sequence")
   raw[family]=rows
  own={"mode":mode,"raw_source_records":raw,"metadata_used":metadata,
   "families":{f:reconstruct_family(rows,f,metadata,PROBE_CONTRACT) for f,rows in raw.items()}}
  pc=primary_checks(own,targets);sc=supporting_checks(own,supporting)
  descriptors=json.loads(Path(config["primary_descriptors_path"]).read_text(encoding="utf-8"))
  align_primary_display(pc,descriptors)
  serialize_full_rounding_lists(pc,own)
  write_json(audit/"INDEPENDENT_80_DIGIT_COMPUTATIONS.json",own)
  write_json(audit/"INDEPENDENT_ALL50_PRIMARY_CHECKS.json",pc)
  write_json(audit/"INDEPENDENT_ALL_SUPPORTING_SOURCE_COMPARISONS.json",sc)
  main=json.loads((run/"ALL_ORIGINAL_COMPUTATIONS.json").read_text(encoding="utf-8"))
  comparison=AuditComparison();compare_families(main,own,comparison)
  mainpc=json.loads((run/"ALL50_PRIMARY_CHECKS.json").read_text(encoding="utf-8"))
  # Declarative descriptors align IDs and labels before execution; mathematical values remain independently produced.
  compare_primary_decisions(mainpc,pc,descriptors,comparison)
  mainsc=json.loads((run/"ALL_SUPPORTING_SOURCE_COMPARISONS.json").read_text(encoding="utf-8"))
  comparison.add("supporting_complete_ids",[r["id"] for r in mainsc],[r["id"] for r in sc])
  for a,b in zip(mainsc,sc):
   comparison.add("support/"+b["id"]+"/passed",a["passes_source_display"],b["passes_source_display"])
   comparison.tree(a["actual"],b["actual"],"support/"+b["id"]+"/actual")
  summary=json.loads((run/"SUMMARY.json").read_text(encoding="utf-8"))
  comparison.add("summary/primary_gates",summary["primary_gates"],50)
  comparison.add("summary/primary_passed",summary["primary_passed"],sum(r["passed"] for r in pc))
  comparison.add("summary/all_primary_passed",summary["all_primary_passed"],all(r["passed"] for r in pc))
  comparison.add("summary/raw_effect_rows",summary["raw_effect_rows"],26)
  comparison.add("summary/all_fits_converged",summary["all_fits_converged"],True)
  rounding_flags={};loo_flags={}
  for family,target in targets["families"].items():
   r=own["families"][family]
   rounding_flags[family]={"midpoint_point_direction":direction(r["primary"]["g"]),"midpoint_CI_classification":classification(r["primary"]),
    "all_fixed_probe_point_direction_matches":direction(r["primary"]["g"])==target["point_direction"] and all(x["point_direction"]==target["point_direction"] for x in r["rounding"]["probe_records"]),
    "all_fixed_probe_CI_classification_matches":classification(r["primary"])==target["CI_classification"] and all(x["CI_classification"]==target["CI_classification"] for x in r["rounding"]["probe_records"])}
   sources=targets["all_whole_trial_leave_out_robustness_mandatory"][family]
   loo_flags[family]={"complete_source_leave_outs":set(r["leave_one_trial_out"])==set(trial_key(x["removed_trial_literal"]) for x in sources),
    "all_point_directions_match":all(r["leave_one_trial_out"][trial_key(x["removed_trial_literal"])]["point_direction"]==x["point_direction"] for x in sources),
    "all_CI_classifications_match":all(r["leave_one_trial_out"][trial_key(x["removed_trial_literal"])]["CI_classification"]==x["CI_classification"] for x in sources)}
  comparison.tree(summary["rounding_qualitative_stability"],rounding_flags,"summary/rounding_qualitative_stability")
  comparison.tree(summary["whole_trial_leave_out_qualitative_robustness"],loo_flags,"summary/whole_trial_leave_out_qualitative_robustness")
  write_json(audit/"ALL_INDEPENDENT_COMPARISONS.json",comparison.checks)
  failures=[x for x in comparison.checks if not x["passed"]]
  status={"status":"complete","mode":mode,"checks":len(comparison.checks),"failures":len(failures),"failed_checks":failures,
   "primary_gates":50,"primary_passed":sum(x["passed"] for x in pc),"all_primary_passed":all(x["passed"] for x in pc),
   "supporting_comparisons":len(sc),"supporting_source_passed":sum(x["passes_source_display"] is True for x in sc),
   "complete_original_outputs_verified":manifest_count,"elapsed_seconds":time.time()-began,"no_primary_rescue":True}
  write_json(audit/"AUDIT_STATUS.json",status)
  refs=[]
  for p in sorted(audit.iterdir()):
   if p.is_file():
    b=p.read_bytes();refs.append({"absolute_path":str(p.resolve()),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
  write_json(audit/"OUTPUT_MANIFEST.json",{"files":refs})
  return 0 if not failures else 2
 except BaseException as e:
  import traceback
  status={"status":"failed","error":repr(e),"traceback":traceback.format_exc(),"elapsed_seconds":time.time()-began,"original_analysis_rerun":False}
  if not (audit/"AUDIT_STATUS.json").exists():write_json(audit/"AUDIT_STATUS.json",status)
  return 2

def align_primary_display(checks,descriptors):
 template=descriptors["checks"]
 if len(template)!=50 or len(checks)!=50:raise ValueError("Fixed fifty-gate census")
 for independent,declared in zip(checks,template):
  if independent["family"]!=declared["family"]:raise ValueError("Source gate order/family changed")
  family=independent["family"];kind=independent["kind"];base=["families",family]
  if kind in ["g","CI_low","CI_high"]:expected_path=base+["primary",kind];expected_kind="pooled_"+kind
  elif kind in ["point_direction","CI_classification"]:expected_path=base;expected_kind="all_rounding_"+kind
  elif kind in ["effects","trials"]:expected_path=base+["geometry",kind];expected_kind="exact_"+kind
  elif kind.startswith("LOO_"):
   metric,key=kind[4:].split(":",1);expected_path=base+["leave_one_trial_out",key,metric]
   expected_kind=declared["kind"]
   literal=expected_kind.removeprefix("LOO_").removesuffix("_"+metric)
   if not expected_kind.endswith("_"+metric) or trial_key(literal)!=key:raise ValueError("Named LOO descriptor identity changed")
  else:raise ValueError("Unmapped complete primary gate")
  if declared["path"]!=expected_path or declared["kind"]!=expected_kind:raise ValueError("Frozen source target path changed")
  t=independent["target"];expected=declared["target"]
  if isinstance(t,dict):
   if t["midpoint"]!=expected:raise ValueError("Qualitative target changed")
  elif isinstance(t,(Decimal,int,float)):
   if D(str(t))!=D(str(expected)):raise ValueError("Numerical source target changed")
  elif t!=expected:raise ValueError("Original target changed")
  independent.update({"id":declared["id"],"kind":declared["kind"],"source":declared["source"],
   "source_literal":str(expected),"target":expected})
def serialize_full_rounding_lists(checks,result):
 # Retain prior independently computed pass decisions, assert equivalent complete-list criterion.
 for check in checks:
  if check["kind"] not in ["all_rounding_point_direction","all_rounding_CI_classification"]:continue
  r=result["families"][check["family"]]
  metric="point_direction" if check["kind"]=="all_rounding_point_direction" else "CI_classification"
  midpoint=direction(r["primary"]["g"]) if metric=="point_direction" else classification(r["primary"])
  actual={"midpoint":midpoint,"all_fixed_probes":[p[metric] for p in r["rounding"]["probe_records"]]}
  equivalent=actual["midpoint"]==check["target"] and all(x==check["target"] for x in actual["all_fixed_probes"])
  if check["passed"]!=equivalent:raise AssertionError("Serialization changed complete qualitative decision")
  check["actual"]=actual

def compare_primary_decisions(main,own,descriptors,comparison):
 comparison.add("complete50/ids",[x["id"] for x in main],[x["id"] for x in own])
 for a,b in zip(main,own):
  label="complete50/"+b["id"]
  comparison.add(label+"/family",a["family"],b["family"])
  comparison.add(label+"/kind",a["kind"],b["kind"])
  comparison.add(label+"/target",a["target"],b["target"])
  comparison.add(label+"/source",a["source"],b["source"])
  comparison.add(label+"/passed",a["passed"],b["passed"])
  comparison.tree(a["actual"],b["actual"],label+"/actual")
  if b["allowance"] is not None:comparison.tree(a["allowance"],b["allowance"],label+"/allowance")

# SOURCE-ONLY PROSPECTIVE ENGINEERING008: exact-input reuse, no scientific method changes.
from collections import OrderedDict
from copy import deepcopy
_ENGINEERING_STATE=None
_ENGINEERING_FIT_CACHE=OrderedDict()
_ENGINEERING_COUNTS={"fit_requests":0,"fit_completed":0,"fit_cache_hits":0,"fit_cache_misses":0,"evaluate_requests":0,"evaluate_cache_hits":0,"evaluate_cache_misses":0}
_ENGINEERING_FIT_LIMIT=16
_ENGINEERING_EVALUATE_LIMIT=128
_BASE_BLOCK_EVALUATE=Block.evaluate
_BASE_INDEPENDENT_FIT=fit
_BASE_AUDIT_ENTRY=audit_entry

def _engineering_tag(x):
 if isinstance(x,Decimal):
  a=x.as_tuple();return ("Decimal",a.sign,tuple(a.digits),a.exponent)
 if x is None:return ("None",)
 if isinstance(x,bool):return ("bool",x)
 if isinstance(x,int):return ("int",x)
 if isinstance(x,float):return ("float",repr(x))
 if isinstance(x,str):return ("str",x)
 if isinstance(x,tuple):return ("tuple",tuple(_engineering_tag(v) for v in x))
 if isinstance(x,list):return ("list",tuple(_engineering_tag(v) for v in x))
 if isinstance(x,dict):
  if any(not isinstance(k,str) for k in x):raise TypeError("Engineering cache requires literal string keys")
  return ("dict",tuple((k,_engineering_tag(x[k])) for k in sorted(x)))
 raise TypeError("Unsupported exact engineering key:"+type(x).__name__)

def _engineering_context_stamp():
 c=getcontext()
 return (c.prec,c.rounding,c.Emin,c.Emax,c.capitals,c.clamp,
  tuple(sorted((str(k),bool(v)) for k,v in c.traps.items())),
  tuple(sorted((str(k),bool(v)) for k,v in c.flags.items())),mp.mp.prec)

def _engineering_remember(cache,key,result,limit):
 # Caller mutations must never enter or alter a stored pure-function result.
 snapshot=deepcopy(result);cache[key]={"result":snapshot,"post_decimal_flags":dict(getcontext().flags)};cache.move_to_end(key)
 while len(cache)>limit:cache.popitem(last=False)

def _engineering_block_evaluate(self,a,b,gradient=True):
 _ENGINEERING_COUNTS["evaluate_requests"]+=1
 cache=getattr(self,"_engineering_evaluation_cache",None)
 if cache is None:
  cache=OrderedDict();self._engineering_evaluation_cache=cache
 state=(self.y,self.v,self.keys,self.X,self.groups,self.cols,self.k,self.p,self.identifiable)
 key=(_engineering_context_stamp(),_engineering_tag(state),_engineering_tag((a,b,gradient)))
 if key in cache:
  _ENGINEERING_COUNTS["evaluate_cache_hits"]+=1;cache.move_to_end(key)
  entry=cache[key]
  for signal,value in entry["post_decimal_flags"].items():getcontext().flags[signal]=value
  return deepcopy(entry["result"])
 _ENGINEERING_COUNTS["evaluate_cache_misses"]+=1
 result=_BASE_BLOCK_EVALUATE(self,a,b,gradient=gradient)
 # Cache entries are made only after the original complete function returns.
 # Cache key includes pre-flags; a hit also restores the exact saved post-flags.
 _engineering_remember(cache,key,result,_ENGINEERING_EVALUATE_LIMIT)
 return result

def _engineering_exact_payload(x):
 if isinstance(x,Decimal):return {"type":"Decimal80_exact","value":str(x)}
 if isinstance(x,tuple):return {"type":"tuple","items":[_engineering_exact_payload(v) for v in x]}
 if isinstance(x,list):return [_engineering_exact_payload(v) for v in x]
 if isinstance(x,dict):return {k:_engineering_exact_payload(v) for k,v in x.items()}
 return x

def _engineering_atomic_owned_write(path,data):
 p=Path(path);root=Path(_ENGINEERING_STATE["audit"]).resolve()
 if not p.resolve().is_relative_to(root):raise ValueError("Engineering output leaves owned audit directory")
 temporary=p.with_name(p.name+".partial")
 if temporary.exists():raise FileExistsError("Preserved incomplete engineering placeholder:"+str(temporary))
 with temporary.open("xb") as f:
  f.write(data);f.flush();os.fsync(f.fileno())
 for io_attempt in range(6):
  try:
   os.replace(temporary,p);break
  except PermissionError:
   if io_attempt==5:raise
   time.sleep(.05)

def _engineering_progress(event):
 if _ENGINEERING_STATE is None:return
 s=_ENGINEERING_STATE
 record={"schema":"P135008 operational scheduling only; no scientific estimates, categories or gates",
  "event":event,"elapsed_seconds":time.time()-s["started"],"counts":dict(_ENGINEERING_COUNTS),
  "committed_fit_capsules":s["capsules"],"source_freeze_sha256":s["freeze_sha256"],
  "auditor_sha256":s["auditor_sha256"],"automatic_resume":False}
 data=(json.dumps(record,indent=2,ensure_ascii=True)+"\n").encode("utf-8")
 _engineering_atomic_owned_write(Path(s["audit"])/"ENGINEERING_PROGRESS.json",data)

def _engineering_commit_fit(ordinal,key,result,cache_hit):
 if _ENGINEERING_STATE is None:return
 s=_ENGINEERING_STATE
 directory=Path(s["audit"])/"ENGINEERING_COMPLETED_FIT_CAPSULES"
 directory.mkdir(exist_ok=True)
 payload={"schema":"P135008 exact completed independent pure fit; prospective write-only checkpoint",
  "ordinal":ordinal,"input_signature":key,"result":_engineering_exact_payload(result),
  "cache_hit":cache_hit,"source_freeze_sha256":s["freeze_sha256"],"auditor_sha256":s["auditor_sha256"]}
 encoded=json.dumps(payload,separators=(",",":"),ensure_ascii=True).encode("utf-8")
 capsule={"payload_sha256":hashlib.sha256(encoded).hexdigest(),"payload":payload}
 data=(json.dumps(capsule,indent=2,ensure_ascii=True)+"\n").encode("utf-8")
 name="fit_%04d.json"%ordinal;path=directory/name
 if path.exists():raise FileExistsError("Completed capsule already exists:"+str(path))
 _engineering_atomic_owned_write(path,data)
 s["capsules"].append({"ordinal":ordinal,"relative_path":"ENGINEERING_COMPLETED_FIT_CAPSULES/"+name,
  "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
  "input_signature_sha256":hashlib.sha256(json.dumps(key,separators=(",",":"),ensure_ascii=True).encode("utf-8")).hexdigest()})

def _engineering_fit(rows,y=None,kind="LS",X=None,ordinary=False):
 _ENGINEERING_COUNTS["fit_requests"]+=1;ordinal=_ENGINEERING_COUNTS["fit_requests"]
 key=(_engineering_context_stamp(),_engineering_tag((rows,y,kind,X,ordinary)))
 _engineering_progress("fit_started")
 cache_hit=key in _ENGINEERING_FIT_CACHE
 if cache_hit:
  _ENGINEERING_COUNTS["fit_cache_hits"]+=1;_ENGINEERING_FIT_CACHE.move_to_end(key)
  entry=_ENGINEERING_FIT_CACHE[key]
  for signal,value in entry["post_decimal_flags"].items():getcontext().flags[signal]=value
  result=deepcopy(entry["result"])
 else:
  _ENGINEERING_COUNTS["fit_cache_misses"]+=1
  result=_BASE_INDEPENDENT_FIT(rows,y=y,kind=kind,X=X,ordinary=ordinary)
  _engineering_remember(_ENGINEERING_FIT_CACHE,key,result,_ENGINEERING_FIT_LIMIT)
 # Distinct calls retain distinct capsules and all downstream records/comparisons.
 # Failed/incomplete fits never become completed cache entries or capsules.
 _engineering_commit_fit(ordinal,key,result,cache_hit)
 _ENGINEERING_COUNTS["fit_completed"]+=1
 _engineering_progress("fit_committed")
 return result

def _engineering_audit_entry(run,audit,freeze_path):
 global _ENGINEERING_STATE
 if _ENGINEERING_STATE is not None:raise RuntimeError("One audit entry per process; no automatic restart")
 if Path(audit).exists():raise FileExistsError("Unique audit directory required")
 _ENGINEERING_STATE={"audit":str(Path(audit).resolve()),"started":time.time(),"capsules":[],
  "freeze_sha256":hashlib.sha256(Path(freeze_path).read_bytes()).hexdigest(),
  "auditor_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 try:
  code=_BASE_AUDIT_ENTRY(run,audit,freeze_path)
  # The original final status and every original comparison remain authoritative.
  # No post-return file update: the original OUTPUT_MANIFEST has already frozen outputs.
  return code
 finally:
  _ENGINEERING_FIT_CACHE.clear()
# No checkpoint reader, automatic restart, fit selection or primary-code import exists.
# Explicit replay of any capsule requires a separate reviewed source/authority amendment.
Block.evaluate=_engineering_block_evaluate
fit=_engineering_fit
audit_entry=_engineering_audit_entry


# SOURCE-ONLY CONTINUATION015: complete original chronological prefix replay.
_CONTINUATION_MANIFEST=None
_CONTINUATION_REPLAY_RECEIPTS=[]
_CONTINUATION_NEW_CALLS=0
_BASE_CONTINUATION_WRITE_JSON=write_json

def _continuation_json_bytes(x):
 return json.dumps(x,separators=(",",":"),ensure_ascii=True).encode("utf-8")

def _continuation_restore_payload(x):
 if isinstance(x,list):return [_continuation_restore_payload(v) for v in x]
 if isinstance(x,dict):
  if set(x)=={"type","value"} and x["type"]=="Decimal80_exact":
   if not isinstance(x["value"],str):raise TypeError("Exact Decimal string required")
   value=Decimal(x["value"])
   if not value.is_finite():raise ValueError("Nonfinite completed Decimal")
   if str(value)!=x["value"]:raise ValueError("Decimal textual roundtrip changed")
   return value
  if set(x)=={"type","items"} and x["type"]=="tuple":
   if not isinstance(x["items"],list):raise TypeError("Exact tuple items required")
   return tuple(_continuation_restore_payload(v) for v in x["items"])
  return {k:_continuation_restore_payload(v) for k,v in x.items()}
 return x

def _continuation_verified_capsule(record):
 p=Path(record["absolute_path"]).resolve();data=p.read_bytes()
 if len(data)!=record["bytes"] or hashlib.sha256(data).hexdigest()!=record["sha256"]:
  raise ValueError("Immutable chronological prefix whole-file mismatch")
 outer=json.loads(data)
 if set(outer)!={"payload_sha256","payload"}:raise ValueError("Capsule outer schema")
 payload=outer["payload"]
 if hashlib.sha256(_continuation_json_bytes(payload)).hexdigest()!=outer["payload_sha256"]:
  raise ValueError("Immutable nested payload mismatch")
 if payload["ordinal"]!=record["ordinal"]:raise ValueError("Immutable prefix ordinal")
 if payload["source_freeze_sha256"]!=_CONTINUATION_MANIFEST["original_freeze_sha256"]:
  raise ValueError("Immutable original source-freeze mismatch")
 if payload["auditor_sha256"]!=_CONTINUATION_MANIFEST["original_auditor_sha256"]:
  raise ValueError("Immutable original auditor mismatch")
 return payload

def _continuation_normalize_preflags(saved):
 # Historical POST flags were not recorded and are NOT recovered/inferred.
 # Restore only each next call's actually recorded PRE sticky flags.
 # The byte-identical arithmetic never reads flags. Numeric precision/traps match.
 current=json.loads(_continuation_json_bytes(_engineering_context_stamp()))
 if current[:7]+current[8:]!=saved[:7]+saved[8:]:
  raise ValueError("Non-flag Decimal/mpmath context differs")
 wanted=dict(saved[7]);signals={str(k):k for k in getcontext().flags}
 if set(wanted)!=set(signals):raise ValueError("Decimal signal census differs")
 if not _CONTINUATION_REPLAY_RECEIPTS:
  if current[7]!=saved[7]:raise ValueError("First original PRE flags differ")
 else:
  for name,signal in signals.items():
   if getcontext().flags[signal] and not wanted[name]:
    raise ValueError("Unexpected newly set flag cannot silently clear")
  for name,signal in signals.items():getcontext().flags[signal]=wanted[name]

def _continuation_fit(rows,y=None,kind="LS",X=None,ordinary=False):
 global _CONTINUATION_NEW_CALLS
 ordinal=_ENGINEERING_COUNTS["fit_requests"]+1
 if ordinal>410:raise ValueError("Unexpected fit beyond unchanged410")
 count=_CONTINUATION_MANIFEST["completed_prefix_count"]
 if ordinal>count:
  _CONTINUATION_NEW_CALLS+=1
  result=_engineering_fit(rows,y=y,kind=kind,X=X,ordinary=ordinary)
 else:
  record=_CONTINUATION_MANIFEST["completed_prefix"][ordinal-1]
  payload=_continuation_verified_capsule(record);saved=payload["input_signature"]
  _continuation_normalize_preflags(saved[0])
  key=(_engineering_context_stamp(),_engineering_tag((rows,y,kind,X,ordinary)))
  if _continuation_json_bytes(key)!=_continuation_json_bytes(saved):
   raise ValueError("Fixed chronological call arguments/context differ")
  result=_continuation_restore_payload(payload["result"])
  if _continuation_json_bytes(_engineering_exact_payload(result))!=_continuation_json_bytes(payload["result"]):
   raise ValueError("Exact numerical payload roundtrip differs")
  _ENGINEERING_COUNTS["fit_requests"]+=1
  _engineering_progress("replay_fit_started")
  # Lost historical cache and POST flag state are not seeded or invented.
  _engineering_commit_fit(ordinal,key,result,False)
  _ENGINEERING_COUNTS["fit_completed"]+=1
  _CONTINUATION_REPLAY_RECEIPTS.append({
   "ordinal":ordinal,"prior_capsule":record,
   "exact_input_context_signature_verified":True,
   "input_signature_sha256":hashlib.sha256(_continuation_json_bytes(saved)).hexdigest(),
   "numeric_payload_sha256":hashlib.sha256(_continuation_json_bytes(payload["result"])).hexdigest(),
   "numeric_payload_roundtrip_exact":True,"historical_post_flags_recovered":False,
   "recorded_next_PRE_flag_boundary_normalization_disclosed":True})
  _engineering_progress("replay_fit_committed")
 if ordinal==410:_continuation_validate_completed_census(write_receipt=True)
 return result

def _continuation_validate_completed_census(write_receipt=False):
 m=_CONTINUATION_MANIFEST
 if m is None:raise ValueError("No fixed chronological prefix")
 if [r["ordinal"] for r in _CONTINUATION_REPLAY_RECEIPTS]!=list(range(1,130)):
  raise ValueError("Every chronological129 prefix fit must replay")
 if _CONTINUATION_NEW_CALLS!=281:raise ValueError("All281 remaining fit calls required")
 if _ENGINEERING_COUNTS["fit_requests"]!=410 or _ENGINEERING_COUNTS["fit_completed"]!=410:
  raise ValueError("Complete410 call/completion census required")
 if len(_ENGINEERING_STATE["capsules"])!=410:raise ValueError("All410 distinct capsules required")
 if write_receipt:
  write_json(Path(_ENGINEERING_STATE["audit"])/"CONTINUATION_COMPLETE410_CALL_IDENTITY_RECEIPT015.json",{
   "status":"complete_fixed410","prefix_replayed":129,"new_completed_calls":281,
   "fixed_order":"distress226 then wellbeing184; original013 generating call order unchanged",
   "all_ordinals":list(range(1,411)),"prefix_receipts":_CONTINUATION_REPLAY_RECEIPTS,
   "historical_post_flags_recovered":False,
   "semantic_boundary":"Exact historical PRE flags, precision/traps and numeric payload; byte-identical arithmetic never reads sticky flags; no exact unobserved POST-state claim.",
   "remaining_all26724_comparisons_required":True,"no_primary_rescue":True})

def _continuation_write_json(path,obj):
 if Path(path).name=="AUDIT_STATUS.json" and isinstance(obj,dict) and obj.get("status")=="complete":
  _continuation_validate_completed_census()
  if obj.get("checks")!=26724:raise ValueError("All unchanged26724 comparisons required")
 return _BASE_CONTINUATION_WRITE_JSON(path,obj)

def _continuation_audit_entry(run,audit,freeze_path):
 global _CONTINUATION_MANIFEST
 if _CONTINUATION_MANIFEST is not None:raise RuntimeError("No automatic continuation retry")
 f=json.loads(Path(freeze_path).read_text(encoding="utf-8"))
 if f["config"]["mode"]!="original":raise ValueError("This fixed129-prefix source is original-only")
 spec=f["config"]["continuation"]
 if spec["approved_execution"] is not True:raise ValueError("Separate root continuation approval required")
 if spec["shared_seconds"]!=10800 or spec["prior_charged_seconds"]!=4285:
  raise ValueError("Prospective aggregate time amendment/prior charges differ")
 if Path(audit).resolve()!=Path(spec["unique_audit_path"]).resolve():raise ValueError("Exact new audit path required")
 auth_path=Path(spec["authorization_path"]).resolve();auth_bytes=auth_path.read_bytes()
 if hashlib.sha256(auth_bytes).hexdigest()!=spec["authorization_sha256"]:
  raise ValueError("Separate one-shot authorization hash mismatch")
 auth=json.loads(auth_bytes)
 if auth.get("approved") is not True or auth.get("original_continuation015_authorized") is not True:
  raise ValueError("No original continuation015 authority")
 if auth.get("auditor_sha256")!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
  raise ValueError("Authorization does not pin this exact auditor")
 mpth=Path(spec["prefix_manifest_path"]).resolve();data=mpth.read_bytes()
 if hashlib.sha256(data).hexdigest()!=spec["prefix_manifest_sha256"]:raise ValueError("Fixed prefix manifest changed")
 m=json.loads(data)
 if m["completed_prefix_count"]!=129 or m["expected_fit_requests"]!=410:raise ValueError("Fixed129/410 geometry")
 if m["new_fit_ordinals"]!=list(range(130,411)):raise ValueError("Every334 remaining ordinal required")
 if [r["ordinal"] for r in m["completed_prefix"]]!=list(range(1,130)):raise ValueError("Only whole chronological prefix accepted")
 root=(Path(__file__).resolve().parent.parent/"papers/P135_young_people_chatbot_meta/audits/original002/ENGINEERING_COMPLETED_FIT_CAPSULES").resolve()
 if Path(m["prefix_root"]).resolve()!=root:raise ValueError("Exact old original002 capsule root required")
 for r in m["completed_prefix"]:
  expected=root/("fit_%04d.json"%r["ordinal"])
  if Path(r["absolute_path"]).resolve()!=expected or expected.is_symlink():raise ValueError("Unexpected old capsule identity")
 _CONTINUATION_MANIFEST=m
 # Only whole-file hashing here, no output/gate-dependent selection; decode at its exact call.
 for r in m["completed_prefix"]:
  p=Path(r["absolute_path"]);data=p.read_bytes()
  if len(data)!=r["bytes"] or hashlib.sha256(data).hexdigest()!=r["sha256"]:raise ValueError("Prior capsule bytes differ")
 return _engineering_audit_entry(run,audit,freeze_path)

fit=_continuation_fit
write_json=_continuation_write_json
audit_entry=_continuation_audit_entry

if __name__=="__main__":
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument("--audit",nargs=2,required=True,metavar=("RUN_DIR","AUDIT_DIR"))
 parser.add_argument("--freeze",required=True)
 args=parser.parse_args()
 sys.exit(audit_entry(args.audit[0],args.audit[1],args.freeze))
