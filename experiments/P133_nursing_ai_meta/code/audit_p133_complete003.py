"""Independent80digit P133 mathematics from original source and root decision003.
Source only until exact root authorization. Never import primary implementation.
Low-rank contraction implements pinned HE/Fisher/default-stopping REML.
"""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_EVEN
import argparse
import hashlib
import json
import math
import os
import sys
sys.dont_write_bytecode = True
import time
import traceback
from datetime import datetime, timezone
import mpmath as mp

mp.mp.dps = 80
Z = mp.mpf("1.959963984540054")
THRESHOLD = mp.mpf("0.00001")
LL0_TOL = mp.mpf(2) ** (-13)
PIPELINES = (("PFT_REML","PFT","REML"), ("PAS_REML","PAS","REML"),
             ("PLOGIT_REML","PLOGIT","REML"), ("PLOGIT_DL","PLOGIT","DL"),
             ("PFT_DL","PFT","DL"), ("PRAW_DL","PRAW","DL"))
FAMILIES = ("awareness","attitude","implementation")
BACKSIZES = ("min","max","arithmetic","geometric","median")

class SourceFitStop(ArithmeticError):
    def __init__(self,message,solver):
        super().__init__(message)
        self.solver=solver

class LiteralJSON:
    """Character-level JSON reader independent of the subject parser."""
    def __init__(self,text):
        self.s=text
        self.i=0
    def ws(self):
        while self.i<len(self.s) and self.s[self.i] in " \t\r\n":
            self.i+=1
    def string(self):
        if self.s[self.i]!='"':
            raise ValueError("JSON string required")
        self.i+=1
        chars=[]
        while self.i<len(self.s):
            c=self.s[self.i]
            self.i+=1
            if c=='"':
                return "".join(chars)
            if c=="\\":
                c=self.s[self.i];self.i+=1
                if c=="u":
                    value=int(self.s[self.i:self.i+4],16);self.i+=4
                    if 0xD800<=value<=0xDBFF and self.s[self.i:self.i+2]=="\\u":
                        self.i+=2
                        value2=int(self.s[self.i:self.i+4],16);self.i+=4
                        if not 0xDC00<=value2<=0xDFFF:
                            raise ValueError("invalid surrogate pair")
                        value=0x10000+(value-0xD800)*0x400+value2-0xDC00
                    chars.append(chr(value))
                else:
                    chars.append({'"':'"',"\\":"\\","/":"/","b":"\b","f":"\f",
                                  "n":"\n","r":"\r","t":"\t"}[c])
            elif ord(c)<32:
                raise ValueError("unescaped JSON control")
            else:
                chars.append(c)
        raise ValueError("unterminated JSON string")
    def value(self):
        self.ws()
        if self.i>=len(self.s):
            raise ValueError("unexpected JSON end")
        c=self.s[self.i]
        if c=='"':
            return self.string()
        if c=="[":
            self.i+=1;ans=[];self.ws()
            if self.s[self.i]=="]":
                self.i+=1;return ans
            while True:
                ans.append(self.value());self.ws();c=self.s[self.i];self.i+=1
                if c=="]":return ans
                if c!=",":raise ValueError("JSON array delimiter")
        if c=="{":
            self.i+=1;ans={};self.ws()
            if self.s[self.i]=="}":
                self.i+=1;return ans
            while True:
                self.ws();key=self.string();self.ws()
                if self.s[self.i]!=":" or key in ans:
                    raise ValueError("JSON duplicate key or colon")
                self.i+=1;ans[key]=self.value();self.ws();c=self.s[self.i];self.i+=1
                if c=="}":return ans
                if c!=",":raise ValueError("JSON object delimiter")
        for token,value in (("true",True),("false",False),("null",None)):
            if self.s.startswith(token,self.i):
                self.i+=len(token);return value
        start=self.i
        while self.i<len(self.s) and self.s[self.i] in "-+0123456789.eE":
            self.i+=1
        token=self.s[start:self.i]
        if not token:raise ValueError("invalid JSON literal")
        return Decimal(token) if any(c in token for c in ".eE") else int(token)
    def read(self):
        ans=self.value();self.ws()
        if self.i!=len(self.s):raise ValueError("JSON trailing bytes")
        return ans

def read_literal(path):
    return LiteralJSON(Path(path).read_text(encoding="utf-8")).read()

def M(value):
    return mp.mpf(str(value))

def native(value):
    if isinstance(value,dict):return {k:native(v)for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [native(v)for v in value]
    if isinstance(value,mp.matrix):return [[float(value[i,j])for j in range(value.cols)]for i in range(value.rows)]
    if isinstance(value,(mp.mpf,Decimal)):return float(value) if mp.isfinite(M(value)) else None
    return value

def chi_upper(x,df):
    if df<=0 or x<0:return None
    return mp.gammainc(M(df)/2,M(x)/2,mp.inf,regularized=True)

def normal_two_tail(z):
    return mp.erfc(abs(M(z))/mp.sqrt(2))

def student_two_tail(t,df):
    if df<=0:return None
    x=M(df)/(M(df)+M(t)**2)
    return mp.betainc(M(df)/2,mp.mpf(".5"),0,x,regularized=True)

_TCACHE={}
def t975(df):
    if df not in _TCACHE:
        lo,hi=mp.mpf(0),mp.mpf(64)
        if student_two_tail(hi,df)>mp.mpf(".05"):
            raise ArithmeticError("fixed Student bracket insufficient")
        for _ in range(150):
            mid=(lo+hi)/2
            if student_two_tail(mid,df)>mp.mpf(".05"):lo=mid
            else:hi=mid
        _TCACHE[df]=(lo+hi)/2
    return _TCACHE[df]

_CPCACHE={}
def beta_quantile(p,a,b):
    lo,hi=mp.mpf(0),mp.mpf(1)
    for _ in range(160):
        mid=(lo+hi)/2
        if mp.betainc(a,b,0,mid,regularized=True)<p:lo=mid
        else:hi=mid
    return (lo+hi)/2

def CP(event,N):
    key=(int(event),int(N))
    if key not in _CPCACHE:
        e,n=key
        _CPCACHE[key]=(mp.mpf(0)if e==0 else beta_quantile(mp.mpf(".025"),e,n-e+1),
                       mp.mpf(1)if e==n else beta_quantile(mp.mpf(".975"),e+1,n-e))
    return _CPCACHE[key]

def transform(event,N,scale,legacy=False):
    e,n=M(event),M(N)
    if n<=0 or e<0 or e>n:raise ValueError("invalid complete event/N source row")
    correction=mp.mpf(".5") if (e==0 or e==n) and not legacy and scale in ("PLOGIT","PRAW") else mp.mpf(0)
    if scale=="PFT":
        y=(mp.asin(mp.sqrt(e/(n+1)))+mp.asin(mp.sqrt((e+1)/(n+1))))/2
        v=1/(4*n+2)
    elif scale=="PAS":
        y=mp.asin(mp.sqrt(e/n));v=1/(4*n)
    elif scale=="PLOGIT":
        y=mp.log((e+correction)/(n-e+correction))
        v=1/(e+correction)+1/(n-e+correction)
    elif scale=="PRAW":
        y=e/n;v=(e+correction)*(n-e+correction)/(n+2*correction)**3
    else:raise ValueError("unregistered scale")
    return y,v,correction

def sample_size(rows,policy="harmonic"):
    vals=[M(r["N"])for r in rows];k=len(vals)
    if not k:raise ValueError("empty active sample size population")
    if policy=="harmonic":return k/mp.fsum(1/n for n in vals)
    if policy=="min":return min(vals)
    if policy=="max":return max(vals)
    if policy=="arithmetic":return mp.fsum(vals)/k
    if policy=="geometric":return mp.exp(mp.fsum(mp.log(n)for n in vals)/k)
    if policy=="median":
        s=sorted(vals)
        return s[k//2]if k%2 else(s[k//2-1]+s[k//2])/2
    raise ValueError("unregistered active backsize")

def inverse(y,scale,n=None):
    if y is None:return None
    y=M(y)
    if scale=="PRAW":return min(mp.mpf(1),max(mp.mpf(0),y))
    if scale=="PLOGIT":return 1/(1+mp.exp(-y))
    if scale=="PAS":
        if y<0:return mp.mpf(0)
        if y>mp.pi/2:return mp.mpf(1)
        return mp.sin(y)**2
    if scale!="PFT"or n is None:raise ValueError("PFT requires active size")
    n=M(n)
    minimum=mp.asin(mp.sqrt(1/(n+1)))/2
    maximum=(mp.asin(mp.sqrt(n/(n+1)))+mp.pi/2)/2
    if y<minimum:return mp.mpf(0)
    if y>maximum:return mp.mpf(1)
    s=mp.sin(2*y)
    radicand=1-(s+(s-1/s)/n)**2
    if radicand<0:return None
    return(1-mp.sign(mp.cos(2*y))*mp.sqrt(radicand))/2

def weighted_contract(y,v,X,tau):
    """No full k-square projection; contract diagonal minus low-rank matrix."""
    k,p=len(y),X.cols
    w=[1/(a+tau)for a in v]
    A=X.T*mp.diag(w)*X
    invA=A**-1
    has_intercept=k>0 and p>0 and all(X[i,0]==1 for i in range(k))
    anchor=y[0] if has_intercept else mp.mpf(0)
    centered=[value-anchor for value in y]
    beta_offset=invA*(X.T*mp.matrix([w[i]*centered[i]for i in range(k)]))
    beta=mp.matrix(beta_offset)
    if has_intercept:beta[0]+=anchor
    residual=[centered[i]-mp.fsum(X[i,j]*beta_offset[j]for j in range(p))for i in range(k)]
    py=[w[i]*residual[i]for i in range(k)]
    B=X.T*mp.diag([a*a for a in w])*X
    C=X.T*mp.diag([a*a*a for a in w])*X
    trP=mp.fsum(w)-mp.fsum((invA*B)[j,j]for j in range(p))
    AB=invA*B
    trPP=mp.fsum(a*a for a in w)-2*mp.fsum((invA*C)[j,j]for j in range(p))+mp.fsum((AB*AB)[j,j]for j in range(p))
    RSS=mp.fsum(w[i]*residual[i]**2 for i in range(k))
    loglike=-(k-p)*mp.log(2*mp.pi)/2-mp.fsum(mp.log(a+tau)for a in v)/2-mp.log(mp.det(A))/2-RSS/2
    return {"w":w,"cov":invA,"beta":beta,"RSS":RSS,"trP":trP,"trPP":trPP,
            "yPPy":mp.fsum(a*a for a in py),"loglike":loglike}

def independent_fit(y,v,X,method):
    k,p=len(y),X.cols
    if any(a<=0 for a in v):raise ValueError("nonpositive within variance")
    if k<=p:return mp.mpf(0),{"converged":True,"saturated":True,"iterations":0}
    center=mp.fsum(y)/k
    centered=[a-center for a in y]
    base=weighted_contract(centered,v,X,mp.mpf(0))
    if method=="DL":
        tau=max(mp.mpf(0),(base["RSS"]-(k-p))/base["trP"])
        return tau,{"converged":True,"method":"DL","iterations":0}
    if method!="REML":raise ValueError("unregistered tau method")
    XXinv=(X.T*X)**-1
    beta=XXinv*(X.T*mp.matrix(centered))
    residual=[centered[i]-mp.fsum(X[i,j]*beta[j]for j in range(p))for i in range(k)]
    trPV=mp.fsum(v)-mp.fsum((XXinv*(X.T*mp.diag(v)*X))[j,j]for j in range(p))
    he=(mp.fsum(a*a for a in residual)-trPV)/(k-p)
    tau=max(mp.mpf(0),he)
    change=THRESHOLD+1;iterations=0;trace=[];boundary_underflow=False
    while change>THRESHOLD:
        iterations+=1;old=tau
        result=weighted_contract(centered,v,X,tau)
        adj=(result["yPPy"]-result["trP"])/result["trPP"]
        halvings=0
        if tau==0 and adj<0:
            # Original IEEE float64 loop halves negative adjustment to signed zero.
            # No arbitrary-precision endless boundary loop and no optimizer change.
            x=float(adj)
            while x<0:x/=2;halvings+=1
            adj=mp.mpf(0);boundary_underflow=True
        else:
            while tau+adj<0:adj/=2;halvings+=1
        tau+=adj;change=abs(old-tau)
        trace.append({"iteration":iterations,"old_tau2":old,"adjustment":adj,"tau2":tau,
                      "change":change,"halvings":halvings})
        if iterations>100:
            raise SourceFitStop("original REML Fisher max100 nonconvergence",
                 {"method":"historical_HE_Fisher_REML","converged":False,"HE_init":he,
                  "initial":max(mp.mpf(0),he),"iterations":iterations,"trace":trace,
                  "threshold":THRESHOLD,"maxiter":100,"audit_y":y,"audit_v":v,"audit_X":X})
    final=weighted_contract(centered,v,X,tau)
    boundary_ll=base["loglike"]-final["loglike"]
    reset=boundary_ll>LL0_TOL and tau>THRESHOLD
    if reset:tau=mp.mpf(0)
    return tau,{"method":"historical_HE_Fisher_REML","converged":True,"HE_init":he,
                "iterations":iterations,"trace":trace,"ll0_minus_ll":boundary_ll,
                "ll0_reset":reset,"boundary_float64_underflow_emulated":boundary_underflow,
                "threshold":THRESHOLD,"maxiter":100,"ll0_tolerance":LL0_TOL}

def active_arrays(rows,scale,legacy=False):
    transformed=[transform(r["events"],r["N"],scale,legacy)for r in rows]
    return [a[0]for a in transformed],[a[1]for a in transformed],transformed

def pool(rows,scale,method,policy="harmonic",legacy=False):
    k=len(rows)
    y,v,transformed=active_arrays(rows,scale,legacy)
    X=mp.matrix([[1]for _ in rows])
    if k==1:
        tau=mp.mpf(0)
        solver={"method":method,"status":"singleton_tau_NA","converged":None,"iterations":[]}
    else:
        tau,solver=independent_fit(y,v,X,method)
    common=weighted_contract(y,v,X,mp.mpf(0))
    random=weighted_contract(y,v,X,tau)
    bsize=sample_size(rows,policy)if scale=="PFT"else None
    def estimate(result):
        m=result["beta"][0];se=mp.sqrt(result["cov"][0,0])
        lo,hi=m-Z*se,m+Z*se
        return {"effect":m,"SE":se,"low_effect":lo,"high_effect":hi,
                "point":m if legacy else inverse(m,scale,bsize),
                "low":lo if legacy else inverse(lo,scale,bsize),
                "high":hi if legacy else inverse(hi,scale,bsize),"weights_pct":100}
    q=common["RSS"];df=k-1
    cm,rm=estimate(common),estimate(random)
    prediction={"df":None,"SE":None,"low_effect":None,"high_effect":None,"low":None,"high":None}
    if k>(2 if legacy else 1):
        se=mp.sqrt(tau+random["cov"][0,0]);dfpi=k-(2 if legacy else 1);tc=t975(dfpi);m=random["beta"][0]
        lo,hi=m-tc*se,m+tc*se
        prediction={"df":dfpi,"SE":se,"low_effect":lo,"high_effect":hi,
                    "low":lo if legacy else inverse(lo,scale,bsize),
                    "high":hi if legacy else inverse(hi,scale,bsize)}
    if legacy and k==1:
        a,b=CP(int(rows[0]["events"]),int(rows[0]["N"]))
        for item in (cm,rm):item["low"],item["high"]=a,b
    out={"status":"ok","input_ids":[r["id"]for r in rows],"k":k,
         "total_N":sum(int(r["N"])for r in rows),"events_total":sum(int(r["events"])for r in rows),
         "scale":scale,"tau_method":method,"backsize_policy":policy,"backsize_N":bsize,
         "common":cm,"random":rm,"prediction":prediction,"Q":q if k>1 else None if legacy else mp.mpf(0),
         "Q_df":df,"heterogeneity_p":chi_upper(q,df)if k>1 else None,
         "I2_pct":100*max(mp.mpf(0),(q-df)/q)if k>1 and q>0 else mp.mpf(0)if k>1 else None,
         "tau2":tau if k>1 else None,"tau2_calc":tau,"solver":solver,"rows":[]}
    cw,rw=common["w"],random["w"]
    for i,r in enumerate(rows):
        low,high=CP(int(r["events"]),int(r["N"]))
        out["rows"].append({"id":r["id"],"canonical_index":r["canonical_index"],"events":r["events"],
           "N":r["N"],"year":r["year"],"effect":y[i],"variance":v[i],
           "increment":transformed[i][2],"proportion":M(r["events"])/M(r["N"]),
           "CI_low":low,"CI_high":high,"common_weight_pct":100*cw[i]/mp.fsum(cw),
           "random_weight_pct":100*rw[i]/mp.fsum(rw)})
    return out

def guarded_pool(rows,scale,method,policy="harmonic",legacy=False):
    try:return pool(rows,scale,method,policy,legacy)
    except Exception as e:
        payload={"status":"not_estimable","error":type(e).__name__+": "+str(e),
                 "input_ids":[r["id"]for r in rows],"k":len(rows),"scale":scale,
                 "tau_method":method,"backsize_policy":policy}
        if isinstance(e,SourceFitStop):payload["solver"]=e.solver
        return payload


def model(rows,scale,method,columns,design,legacy=False):
    y,v,tr=active_arrays(rows,scale,legacy)
    X=mp.matrix([[M(x)for x in row]for row in design])
    if X.cols!=len(columns) or X.rows!=len(rows):
        raise ValueError("complete model design dimensions")
    if len(rows)<=len(columns) or mp.det(X.T*X)==0:
        raise ArithmeticError("original complete design is rank deficient or residual df<=0")
    tau,solver=independent_fit(y,v,X,method)
    fitted=weighted_contract(y,v,X,tau)
    fixed=weighted_contract(y,v,X,mp.mpf(0))
    beta=[fitted["beta"][j]for j in range(X.cols)]
    se=[mp.sqrt(fitted["cov"][j,j])for j in range(X.cols)]
    z=[beta[j]/se[j]for j in range(X.cols)]
    return {"status":"ok","input_ids":[r["id"]for r in rows],"columns":columns,
            "scale":scale,"tau_method":method,"X":design,"y":y,"v":v,
            "increments":[a[2]for a in tr],"beta":beta,"cov":fitted["cov"],
            "SE":se,"Z":z,"p":[normal_two_tail(a)for a in z],
            "CI_low":[beta[j]-Z*se[j]for j in range(X.cols)],
            "CI_high":[beta[j]+Z*se[j]for j in range(X.cols)],
            "Q":fixed["RSS"],"Q_df":len(rows)-X.cols,
            "heterogeneity_p":chi_upper(fixed["RSS"],len(rows)-X.cols),
            "tau2":tau,"solver":solver}

def guarded_model(rows,scale,method,columns,design,legacy=False):
    try:return model(rows,scale,method,columns,design,legacy)
    except Exception as e:
        payload={"status":"not_estimable","error":type(e).__name__+": "+str(e),
                 "input_ids":[r["id"]for r in rows],"columns":columns,
                 "scale":scale,"tau_method":method}
        if isinstance(e,SourceFitStop):payload["solver"]=e.solver
        return payload

def designs(rows):
    faculty=any(r["group"]=="faculty"for r in rows)
    groupcols=["nurses"]+(["faculty"]if faculty else[])
    simultaneous=["intercept","year_minus_2020","N"]+groupcols
    full=[[1,int(r["year"])-2020,int(r["N"])]+[int(r["group"]==g)for g in groupcols]for r in rows]
    year=([[1,int(r["year"])-2020]for r in rows],["intercept","year_minus_2020"])
    n=([[1,int(r["N"])]for r in rows],["intercept","N"])
    group=([[1]+[int(r["group"]==g)for g in groupcols]for r in rows],["intercept"]+groupcols)
    countries={}
    for convention,field in (("AppendixB","country_B"),("Figure2","country_Figure2")):
        categories=sorted(set(r[field]for r in rows))
        columns=["intercept"]+["country:"+a for a in categories[1:]]
        design=[[1]+[int(r[field]==a)for a in categories[1:]]for r in rows]
        countries[convention]={"categories":categories,"reference_category":categories[0],
                              "coding":{r["id"]:r[field]for r in rows},
                              "columns":columns,"design":design}
    return full,simultaneous,{"year":year,"N":n,"group":group},countries

def Egger(rows,scale,legacy=False):
    ids=[r["id"]for r in rows]
    if len(rows)<10:
        return {"status":"not_estimable","input_ids":ids,"scale":scale,
                "k_min":10,"correct":False,"error":"Egger source k.min10"}
    try:
        y,v,tr=active_arrays(rows,scale,legacy)
        design=[[1,mp.sqrt(a)]for a in v]
        X=mp.matrix(design)
        fit=weighted_contract(y,v,X,mp.mpf(0))
        df=len(rows)-2;dispersion=fit["RSS"]/df
        cov=fit["cov"]*dispersion
        bias,limit=fit["beta"][1],fit["beta"][0]
        bse,lse=mp.sqrt(cov[1,1]),mp.sqrt(cov[0,0])
        stat=bias/bse;t=t975(df)
        return {"status":"ok","input_ids":ids,"scale":scale,"k_min":10,
                "correct":False,"y":y,"v":v,"X":design,"df":df,
                "dispersion":dispersion,"cov":cov,"bias_SND_intercept":bias,
                "bias_SE":bse,"weighted_limit_intercept":limit,"weighted_limit_SE":lse,
                "weighted_limit_low":limit-t*lse,"weighted_limit_high":limit+t*lse,
                "statistic":stat,"p":student_two_tail(stat,df),
                "source_label_warning":"Printed beta0 label retained; compare fixed Egger bias, also report limit intercept; no outcome-selected naming"}
    except Exception as e:
        return {"status":"not_estimable","input_ids":ids,"scale":scale,
                "k_min":10,"correct":False,"error":type(e).__name__+": "+str(e)}

def between(groups,rows):
    output={"status":"ok"}
    for label in ("common","random"):
        estimates=[g[label]["effect"]for g in groups.values()if g.get("status")=="ok"]
        variances=[g[label]["SE"]**2 for g in groups.values()if g.get("status")=="ok"]
        if len(estimates)!=len(groups)or len(estimates)<2:
            return {"status":"not_estimable","error":"complete group pool unavailable","input_ids":[r["id"]for r in rows]}
        w=[1/a for a in variances]
        m=mp.fsum(w[i]*estimates[i]for i in range(len(w)))/mp.fsum(w)
        q=mp.fsum(w[i]*(estimates[i]-m)**2 for i in range(len(w)))
        df=len(w)-1
        output[label]={"Q":q,"df":df,"p":chi_upper(q,df)}
    output["interpretation"]="Separate-tau meta subgroup Q from transformed group estimates/SEs"
    return output

def shared_between(rows,scale,pooled,legacy=False):
    if pooled.get("status")!="ok":
        return {"status":"not_estimable","error":"complete family tau unavailable","input_ids":[r["id"]for r in rows]}
    try:
        y,v,tr=active_arrays(rows,scale,legacy)
        tau=pooled["tau2_calc"];w=[1/(a+tau)for a in v]
        fullmean=mp.fsum(w[i]*y[i]for i in range(len(rows)))/mp.fsum(w)
        q=mp.mpf(0);groups=sorted(set(r["group"]for r in rows))
        for g in groups:
            ix=[i for i,r in enumerate(rows)if r["group"]==g]
            weight=mp.fsum(w[i]for i in ix)
            mean=mp.fsum(w[i]*y[i]for i in ix)/weight
            q+=weight*(mean-fullmean)**2
        df=len(groups)-1
        return {"status":"ok","Q":q,"df":df,"p":chi_upper(q,df),
                "interpretation":"Original prospective RAWDL001 shared full-family tau between test"}
    except Exception as e:
        return {"status":"not_estimable","error":type(e).__name__+": "+str(e),"input_ids":[r["id"]for r in rows]}

def funnel(rows,scale,pooled,legacy=False):
    if pooled.get("status")!="ok":
        return {"status":"not_estimable","input_ids":[r["id"]for r in rows]}
    y,v,tr=active_arrays(rows,scale,legacy);center=pooled["random"]["effect"]
    z99=mp.mpf("2.5758293035489004")
    pairs=[]
    for r,a,b in zip(rows,y,v):
        se=mp.sqrt(b)
        pairs.append({"id":r["id"],"effect":a,"SE":se,
                      "envelope95_low":center-Z*se,"envelope95_high":center+Z*se,
                      "envelope99_low":center-z99*se,"envelope99_high":center+z99*se})
    return {"status":"ok","input_ids":[r["id"]for r in rows],"scale":scale,
            "center":center,"pairs":pairs,"source_target_absent":True}

def full_family(rows,scale,method,legacy=False,loo=False):
    pooled=guarded_pool(rows,scale,method,legacy=legacy)
    groups={}
    for group in ("students","nurses","faculty"):
        active=[r for r in rows if r["group"]==group]
        if active:groups[group]=guarded_pool(active,scale,method,legacy=legacy)
    design,cols,univariates,countries=designs(rows)
    out={"pooled":pooled,"groups":groups,
         "between":between(groups,rows),"legacy_shared_between":shared_between(rows,scale,pooled,legacy)if legacy else None,
         "simultaneous":guarded_model(rows,scale,method,cols,design,legacy),
         "univariate":{},"country":{},"Egger":Egger(rows,scale,legacy),
         "funnel":funnel(rows,scale,pooled,legacy)}
    for name,(X,columns)in univariates.items():
        out["univariate"][name]=guarded_model(rows,scale,method,columns,X,legacy)
    for name,d in countries.items():
        out["country"][name]=guarded_model(rows,scale,method,d["columns"],d["design"],legacy)
        out["country"][name]["categories"]=d["categories"]
        out["country"][name]["reference_category"]=d["reference_category"]
        out["country"][name]["coding"]=d["coding"]
    if loo:
        out["LOO"]={}
        for excluded in rows:
            remaining=[r for r in rows if r["id"]!=excluded["id"]]
            if legacy:
                view=full_family(remaining,scale,method,legacy=True,loo=False)
            else:view={"pooled":guarded_pool(remaining,scale,method)}
            view["excluded_id"]=excluded["id"]
            view["remaining_input_ids"]=[r["id"]for r in remaining]
            out["LOO"][excluded["id"]]=view
    return out

def backsize_pool(pooled,rows,policy):
    """Hold complete PFT transformed fit fixed; change only inverse sample size."""
    if pooled.get("status")!="ok":return dict(pooled)
    n=sample_size(rows,policy)
    output=dict(pooled);output["backsize_N"]=n;output["backsize_policy"]=policy
    for label in ("common","random"):
        d=dict(pooled[label])
        d["point"]=inverse(d["effect"],"PFT",n)
        d["low"]=inverse(d["low_effect"],"PFT",n)
        d["high"]=inverse(d["high_effect"],"PFT",n)
        output[label]=d
    d=dict(pooled["prediction"])
    d["low"]=inverse(d["low_effect"],"PFT",n);d["high"]=inverse(d["high_effect"],"PFT",n)
    output["prediction"]=d
    return output

def calculate_all(rows,progress):
    result={"schema":"P133_candidate004","pipelines":{},"backsize_views":{},"legacy_RAWDL001":{},
            "architecture_GLMM":{"status":"source_architecture_only","model":"PLOGIT/GLMM/ML",
            "individual_common_weights":None,"individual_random_weights":None,
            "default_prediction":False,"numeric_fit":False,"not_a_primary_rescue":True}}
    for identifier,scale,method in PIPELINES:
        families={}
        for family in FAMILIES:
            active=[r for r in rows if r["family"]==family]
            families[family]=full_family(active,scale,method,loo=True)
            progress("pipeline_family_complete",{"pipeline":identifier,"family":family})
        result["pipelines"][identifier]={"scale":scale,"tau_method":method,"families":families}
    source=result["pipelines"]["PFT_REML"]["families"]
    for policy in BACKSIZES:
        families={}
        for family in FAMILIES:
            active=[r for r in rows if r["family"]==family];original=source[family]
            d={"pooled":backsize_pool(original["pooled"],active,policy),"groups":{},"LOO":{}}
            for group,g in original["groups"].items():
                group_rows=[r for r in active if r["group"]==group]
                d["groups"][group]=backsize_pool(g,group_rows,policy)
            for identifier,view in original["LOO"].items():
                rest=[r for r in active if r["id"]!=identifier]
                d["LOO"][identifier]={"excluded_id":identifier,
                    "remaining_input_ids":[r["id"]for r in rest],
                    "pooled":backsize_pool(view["pooled"],rest,policy)}
            families[family]=d
        result["backsize_views"][policy]={"families":families}
        progress("backsize_policy_complete",{"policy":policy})
    for family in FAMILIES:
        active=[r for r in rows if r["family"]==family]
        result["legacy_RAWDL001"][family]=full_family(active,"PRAW","DL",legacy=True,loo=True)
        progress("legacy_family_complete",{"family":family})
    return result

def canonical_original(forest,metadata,appraisals,conflicts):
    records={int(r["canonical_index"]):r for r in metadata["records"]}
    overrides={int(r["appendixB_canonical_index"]):r["country_literal"]
               for r in appraisals["records"]}
    rows=[]
    for r in forest["rows"]:
        index=int(r["appendixB_canonical_index"]);meta=records[index]
        tokens=meta["primary_country_tokens"]
        country=" + ".join(tokens)if tokens else"NOT_SPECIFIED"
        rows.append({"id":r["family"]+".row%02d"%int(r["forest_row"]),
            "family":r["family"],"forest_row":int(r["forest_row"]),
            "canonical_index":index,"study_literal":r["study_literal"],
            "year":int(r["year_literal"]),"events":int(r["events_literal"]),
            "N":int(r["N_literal"]),"group":meta["primary_group"],
            "country_B":country,"country_Figure2":overrides.get(index,country)})
    return {"rows":rows,"metadata":metadata,
            "appraisals":appraisals,"conflicts":conflicts}

def independent_census(canonical):
    rows=canonical["rows"];ids=[r["id"]for r in rows]
    expected=[f+".row%02d"%i for f,k in zip(FAMILIES,(15,16,12))for i in range(1,k+1)]
    if ids!=expected or len(set(ids))!=43:
        raise ValueError("whole43 original identity/order census")
    if set(int(r["canonical_index"])for r in rows)!=set(range(1,19)):
        raise ValueError("whole18 original study census")
    counts={"awareness":{"students":7,"nurses":7,"faculty":1},
            "attitude":{"students":9,"nurses":7},
            "implementation":{"students":6,"nurses":5,"faculty":1}}
    for family,want in counts.items():
        actual={}
        for r in rows:
            if r["family"]==family:
                actual[r["group"]]=actual.get(r["group"],0)+1
        if actual!=want:raise ValueError("fixed source group census")
    if len(canonical["metadata"]["records"])!=18 or len(canonical["appraisals"]["records"])!=16:
        raise ValueError("whole18 metadata/all16 Figure2 judgments")
    if len(canonical["appraisals"]["separate_figure3"])<3:
        raise ValueError("both complete Figure3 appraisal panels")
    if len(canonical["conflicts"])!=23:
        raise ValueError("whole original23 source conflict/gap contexts")
    for r in rows:
        if not(0<=r["events"]<=r["N"]and r["N"]>0):
            raise ValueError("invalid whole raw event/N input")
    return {"rows":43,"studies":18,"groups":counts,"metadata":18,
            "Figure2":16,"Figure3":2,"source_conflicts":23}

def dict_path(d,keys):
    for key in keys:
        if not isinstance(d,dict)or key not in d:return None
        d=d[key]
    return d

def output_values(result,targets):
    primary={};support={}
    families=result["pipelines"]["PFT_REML"]["families"]
    for d in targets["primary_output_gates"]:
        parts=d["id"].split(".");family=parts[0];record=families[family]
        if parts[1].startswith("row"):
            rowid=family+"."+parts[1]
            rows=record["pooled"].get("rows",[])
            matched=[r for r in rows if r["id"]==rowid]
            value=matched[0].get(parts[2])if len(matched)==1 else None
        else:
            parts=parts[2:]
            # Frozen footer gate IDs use semantic keys, not array positions.
            value=dict_path(record["pooled"],parts)
        primary[d["id"]]=value
    regressions={"awareness":{3:"year_minus_2020",4:"N",5:"nurses",6:"faculty"},
                 "attitude":{8:"year_minus_2020",9:"N",10:"nurses"},
                 "implementation":{12:"year_minus_2020",13:"N",14:"nurses"}}
    subgroups={"awareness":{3:"students",4:"nurses",5:"faculty"},
               "attitude":{7:"students",8:"nurses"},
               "implementation":{10:"students",11:"nurses"}}
    fields={"estimate":"beta","SE":"SE","Z":"Z","p":"p","CI_low":"CI_low","CI_high":"CI_high"}
    for d in targets["supporting_literal_gates"]:
        family,kind,*rest=d["id"].split(".");record=families[family];value=None
        if kind=="T5":
            rowno=int(rest[0][3:]);field=rest[1]
            modelrecord=record["simultaneous"];name=regressions[family][rowno]
            if modelrecord.get("status")=="ok"and name in modelrecord["columns"]:
                index=modelrecord["columns"].index(name);value=modelrecord[fields[field]][index]
        elif kind=="T6"and rest[0]=="between":
            value=dict_path(record["between"],["random",rest[1]])
        elif kind=="T6":
            group=subgroups[family][int(rest[0][3:])];p=record["groups"].get(group,{})
            field=rest[1]
            if field=="N_studies":value=p.get("k")
            elif field=="I2_percent":value=p.get("I2_pct")
            elif field=="tau2":value=p.get("tau2")
            else:value=dict_path(p,["random",{"CI_low":"low","CI_high":"high"}.get(field,field)])
        elif kind=="Egger":
            value=record["Egger"].get("bias_SND_intercept"if rest[0]=="intercept"else"p")
        else:raise ValueError("unmapped supporting source identity "+d["id"])
        support[d["id"]]=value
    if len(primary)!=263 or len(support)!=114:
        raise ValueError("whole377 output map census")
    result["primary_output_values"]=primary;result["supporting_output_values"]=support
    return primary,support

def source_display(value,d):
    if d.get("typed_value")is None and not d.get("comparison_kind")and d["literal"].strip() in ("\u2013","\u2014","NA","N/A","-"):
        return value is None,None if value is None else str(float(value))
    if value is None:return False,None
    literal=d["literal"].strip()
    if literal.startswith("<"):
        limit=Decimal(literal[1:].strip())
        return Decimal(str(float(value)))>=0 and Decimal(str(float(value)))<limit,str(float(value))
    if d["decimal_places"]is None:
        target=d.get("typed_value")
        return value==target,str(value)
    quantum=Decimal(10)**(-int(d["decimal_places"]))
    formatted=Decimal(str(float(value))).quantize(quantum,rounding=ROUND_HALF_EVEN)
    target=Decimal(str(d["typed_value"]))
    return formatted==target,str(formatted)

def all_source_comparisons(canonical,result,targets):
    raw={r["id"]:r for r in canonical["rows"]}
    primary,support=output_values(result,targets)
    comparisons=[]
    contradictions=set(targets["contradictory_support_cell_ids"])
    for section in ("input_gates","primary_output_gates","supporting_literal_gates"):
        for d in targets[section]:
            if section=="input_gates":
                rowid,field=d["id"].rsplit(".",1);value=raw[rowid][field]
            else:value=(primary if section=="primary_output_gates"else support)[d["id"]]
            passed,formatted=source_display(value,d)
            comparisons.append({"id":d["id"],"role":d["role"],
                "source_literal":d["literal"],"source":d["source"],"value":value,
                "decimal_places":d["decimal_places"],"source_star":d.get("star"),
                "joint_source_contradiction":d.get("joint_source_contradiction"),
                "passed":bool(passed),"formatted":formatted})
            if d.get("star")is not None:
                comparisons[-1]["computed_significance_p_lt_05"]=(bool(value<mp.mpf(".05"))if value is not None and d["id"].endswith(".p")else None)
    if len(comparisons)!=506 or len({d["id"]for d in comparisons})!=506:
        raise ValueError("whole506 immutable source comparisons")
    return comparisons

def source_claims(result,comparisons,canonical,census):
    f=result["pipelines"]["PFT_REML"]["families"]
    outputgates=[r for r in comparisons if r["role"]=="PRIMARY_FOREST_OUTPUT"]
    primary1=all(r["passed"]for r in outputgates)and len(outputgates)==263
    p=[f[a]["pooled"].get("heterogeneity_p")for a in FAMILIES]
    primary2=all(a is not None and 0<=a<mp.mpf(".0001")and a<mp.mpf(".05")for a in p)
    a,b,c=[f[name]["pooled"]for name in FAMILIES]
    vals=[dict_path(b,["random","point"]),dict_path(a,["random","point"]),
          c.get("I2_pct"),a.get("I2_pct"),b.get("I2_pct")]
    primary3=all(v is not None for v in vals)and vals[0]<vals[1]and vals[2]>vals[3]and vals[2]>vals[4]
    mod=True
    columns={"awareness":["year_minus_2020","N","nurses","faculty"],
             "attitude":["year_minus_2020","N","nurses"],
             "implementation":["year_minus_2020","N","nurses"]}
    for family,names in columns.items():
        m=f[family]["simultaneous"]
        if m.get("status")!="ok":mod=False;continue
        for name in names:
            pvalue=m["p"][m["columns"].index(name)]
            mod=mod and (pvalue<mp.mpf(".05")if family=="attitude"and name=="year_minus_2020"else pvalue>=mp.mpf(".05"))
    sub=True
    for family in FAMILIES:
        groups=f[family]["groups"];btest=dict_path(f[family]["between"],["random","p"])
        values=[dict_path(groups.get(g,{}),["random","point"])for g in("students","nurses")]
        ok=all(v is not None for v in values)and values[0]>values[1]
        if family=="awareness":
            fac=dict_path(groups.get("faculty",{}),["random","point"])
            ok=ok and fac is not None and fac>values[1]
        ok=ok and btest is not None and (btest>=mp.mpf(".05")if family=="attitude"else btest<mp.mpf(".05"))
        sub=sub and ok
    egger=all(f[name]["Egger"].get("p")is not None and f[name]["Egger"]["p"]>=mp.mpf(".05")for name in FAMILIES)
    return {"CL01":{"role":"PRIMARY","passed":bool(primary1)},
            "CL02":{"role":"PRIMARY","passed":bool(primary2)},
            "CL03":{"role":"PRIMARY","passed":bool(primary3)},
            "CL04":{"role":"SUPPORTING","passed":bool(mod)},
            "CL05":{"role":"SUPPORTING","passed":bool(sub)},
            "CL06":{"role":"SUPPORTING","passed":bool(egger),"absence_of_bias_not_established":True},
            "CL07":{"role":"MANDATORY_DIAGNOSTIC_CENSUS","passed":True},
            "CL08":{"role":"MANDATORY_SOURCE_REPORT","passed":len(canonical["conflicts"])==23},
            "CL09":{"role":"MANDATORY_INPUT_CENSUS","passed":census["rows"]==43 and census["studies"]==18}}

def public_source_claims(claims):
    if claims is None:return None
    output=[]
    for key in("CL01","CL02","CL03"):
        output.append({"id":key,"role":"PRIMARY","passed":claims[key]["passed"]})
    output[0]["source_abstract_upper80_conflict"]="Canonical Figure4 upper81 remains primary, abstract80 mandatory conflictC11"
    for key,role,report in (
        ("CL04","SUPPORTING","All10 moderator literal cells/slopes and all unprinted coefficients retain actual p/sign/NA"),
        ("CL05","SUPPORTING","All7 printed plus8actualgroups and both between tests; inconsistent Ns/CI preserved"),
        ("CL06","SUPPORTING","All3 fixed Egger bias/p, limit intercept also present; nonsignificance does not establish absence"),
        ("CL07","COMPLETE_CONTROL","All43LOO/country3x2/full variants/backsize5/funnels/legacy_RAWDL001 retained"),
        ("CL08","MANDATORY_LIMITATION","All23sourceconflicts/18source appraisals/full-paper and author-settings/event coding gaps retained"),
        ("CL09","EXACT_CENSUS","Canonical all43/18 plus exact129input/377output/audit/closure required")):
        output.append({"id":key,"role":role,"report":report})
    return output

def source_wrapper(canonical,result,comparisons,targets,mode):
    if mode=="fixture":
        return {"status":"unrelated_fixture_no_original_source_fit_comparisons",
            "expected_input_IDs":[d["id"]for d in targets["input_gates"]],
            "expected_primary_IDs":[d["id"]for d in targets["primary_output_gates"]],
            "expected_support_IDs":[d["id"]for d in targets["supporting_literal_gates"]],
            "scientific_credit":False}
    raw={r["id"]:r for r in canonical["rows"]}
    input_values={}
    for d in targets["input_gates"]:
        identifier,field=d["id"].rsplit(".",1);input_values[d["id"]]=raw[identifier][field]
    return {"input_values":input_values,"primary_output_values":result["primary_output_values"],
        "supporting_output_values":result["supporting_output_values"],"comparisons":comparisons,
        "input_pass":all(d["passed"]for d in comparisons[:129]),
        "primary263_pass":all(d["passed"]for d in comparisons[129:392]),
        "supporting114_pass":all(d["passed"]for d in comparisons[392:]),
        "supporting_never_rescues":True}

def audit_source_wrapper(audit,expected,actual,mode):
    if mode=="fixture":
        audit.compare("source_comparisons",expected,actual);return
    if not isinstance(actual,dict):
        audit.record("source_comparisons","complete dictionary",actual,False,"exact");return
    audit.record("source_comparisons/__keys__",sorted(expected),sorted(actual),
                 set(expected)==set(actual),"exact_expected_field_set")
    for key in expected:
        if key!="comparisons":
            audit.compare("source_comparisons/"+key,expected[key],actual.get(key))
    records=actual.get("comparisons")
    if not isinstance(records,list):
        audit.record("source_comparisons/records","array",records,False,"exact");return
    audit.record("source_comparisons/census",506,len(records),len(records)==506,"exact")
    for index,e in enumerate(expected["comparisons"]):
        prefix="source_comparisons/"+e["id"]
        if index>=len(records):
            audit.record(prefix,e,None,False,"missing_required_record");continue
        a=records[index]
        if not isinstance(a,dict):
            audit.record(prefix,"object",a,False,"exact");continue
        audit.record(prefix+"/__keys__",sorted(e),sorted(a),set(e)==set(a),"exact_expected_field_set")
        for key,value in e.items():
            if key=="formatted"and e["source_literal"].strip().startswith("<")and value is not None:
                # Unrounded p text is diagnostic, not a printed precision target.
                # Numeric p and strict source decision are independently checked above.
                try:audit.compare(prefix+"/formatted_diagnostic_numeric",M(value),M(a.get(key)))
                except Exception as exc:audit.record(prefix+"/formatted",value,a.get(key),False,"diagnostic_number",str(exc))
            else:audit.compare(prefix+"/"+key,value,a.get(key))

def sha256_file(path):
    digest=hashlib.sha256()
    with Path(path).open("rb")as stream:
        while True:
            block=stream.read(1024*1024)
            if not block:break
            digest.update(block)
    return digest.hexdigest()

def write_json(path,value):
    with Path(path).open("x",encoding="utf-8",newline="\n")as stream:
        json.dump(native(value),stream,ensure_ascii=True,indent=2,allow_nan=False)
        stream.write("\n")

class WholeAudit:
    """Expected independent tree determines coverage; never subject census."""
    def __init__(self,path):
        self.stream=Path(path).open("x",encoding="utf-8",newline="\n")
        self.count=0;self.failures=0;self.failure_paths=[]
        self.family_counts={}
    def record(self,key,expected,actual,passed,kind,reason=None):
        self.count+=1
        family=key.split("/",2)[1]if"/"in key else key.split(".",1)[0]
        tally=self.family_counts.setdefault(family,{"checks":0,"failures":0})
        tally["checks"]+=1
        if not passed:
            self.failures+=1;tally["failures"]+=1
            self.failure_paths.append(key)
        item={"key":key,"kind":kind,"expected":native(expected),
              "actual":native(actual),"passed":bool(passed)}
        if reason:item["reason"]=reason
        self.stream.write(json.dumps(item,ensure_ascii=True,allow_nan=False,separators=(",",":"))+"\n")
    def compare(self,key,expected,actual):
        if isinstance(expected,mp.matrix):
            expected=[[expected[i,j]for j in range(expected.cols)]for i in range(expected.rows)]
        if isinstance(expected,dict):
            if not isinstance(actual,dict):
                self.record(key,sorted(expected),actual,False,"dictionary");return
            # Source labels/errors/trace are separately evidenced, not numerical tree exemptions.
            excluded={"solver","error"}
            ekeys=set(expected)-excluded;akeys=set(actual)-excluded
            self.record(key+"/__keys__",sorted(ekeys),sorted(akeys),ekeys==akeys,"exact_expected_field_set")
            for name in sorted(ekeys):
                if name not in actual:
                    self.record(key+"/"+name,expected[name],None,False,"missing_required_field")
                else:self.compare(key+"/"+name,expected[name],actual[name])
            if"error"in expected:
                self.record(key+"/error_present",True,isinstance(actual.get("error"),str)and bool(actual["error"]),
                            isinstance(actual.get("error"),str)and bool(actual["error"]),"retained_implementation_specific_error")
            if"solver"in expected:self.solver(key+"/solver",expected,actual)
            return
        if isinstance(expected,(list,tuple)):
            if not isinstance(actual,list):
                self.record(key,len(expected),actual,False,"array");return
            self.record(key+"/__length__",len(expected),len(actual),len(expected)==len(actual),"exact_expected_array_length")
            for i,e in enumerate(expected):
                if i>=len(actual):self.record(key+"/%d"%i,e,None,False,"missing_array_value")
                else:self.compare(key+"/%d"%i,e,actual[i])
            return
        if expected is None or isinstance(expected,(str,bool)):
            self.record(key,expected,actual,expected==actual and type(expected)==type(actual),"exact");return
        if isinstance(expected,int)and not isinstance(expected,bool):
            passed=(not isinstance(actual,bool))and isinstance(actual,(int,Decimal))and actual==expected
            self.record(key,expected,actual,passed,"exact_integer");return
        if isinstance(actual,bool)or not isinstance(actual,(int,float,Decimal,mp.mpf)):
            self.record(key,expected,actual,False,"numeric_type");return
        e,a=M(expected),M(actual)
        tolerance=mp.mpf("1e-10")+mp.mpf("1e-10")*abs(e)
        passed=mp.isfinite(e)and mp.isfinite(a)and abs(e-a)<=tolerance
        self.record(key,e,a,passed,"fixed_1e-10_abs_plus_1e-10_rel")
    def solver(self,key,expected_pool,actual_pool):
        own=expected_pool.get("solver")
        subject=actual_pool.get("solver")
        self.record(key+"/__present__",True,isinstance(subject,dict),isinstance(subject,dict),"solver_evidence")
        if not isinstance(subject,dict):return
        if expected_pool.get("k")==1:
            # Non-attempted singleton heterogeneity is explicitly NA, never convergence=True.
            self.record(key+"/singleton_k",1,actual_pool.get("k"),actual_pool.get("k")==1,"exact_singleton_identity_count")
            self.compare(key+"/singleton_descriptor",own,subject)
            for field in ("Q","Q_df","heterogeneity_p","I2_pct","tau2","tau2_calc","prediction"):
                self.compare(key+"/singleton_semantics/"+field,expected_pool[field],actual_pool.get(field))
            self.record(key+"/singleton_calc_tau_exact_zero",True,actual_pool.get("tau2_calc")==0,actual_pool.get("tau2_calc")==0,"source_singleton_no_heterogeneity_estimate")
            return
        source_converged=bool(own.get("converged"))
        self.record(key+"/converged",source_converged,subject.get("converged"),subject.get("converged")==source_converged,"source_convergence")
        # Independent exact default process was reconstructed; final tau comparison above is mandatory.
        # Subject trace is validated separately against original equations, not compared byte-for-byte.
        if expected_pool.get("k")==1 or own.get("saturated"):return
        if expected_pool.get("tau_method")=="DL":return
        if expected_pool.get("status")=="not_estimable"and not source_converged:
            y=own["audit_y"];v=own["audit_v"];X=own["audit_X"]
        elif"rows"in actual_pool:
            rows=actual_pool["rows"]
            try:
                y=[M(r["effect"])for r in rows];v=[M(r["variance"])for r in rows]
                X=mp.matrix([[1]for _ in rows])
            except Exception as e:
                self.record(key+"/trace_inputs",True,str(e),False,"solver_evidence");return
        else:
            try:
                y=[M(a)for a in actual_pool["y"]];v=[M(a)for a in actual_pool["v"]]
                X=mp.matrix([[M(a)for a in row]for row in actual_pool["X"]])
            except Exception as e:
                self.record(key+"/trace_inputs",True,str(e),False,"solver_evidence");return
        center=mp.fsum(y)/len(y);yc=[a-center for a in y]
        XXinv=(X.T*X)**-1;b=XXinv*(X.T*mp.matrix(yc))
        residual=[yc[i]-mp.fsum(X[i,j]*b[j]for j in range(X.cols))for i in range(len(yc))]
        trPV=mp.fsum(v)-mp.fsum((XXinv*(X.T*mp.diag(v)*X))[j,j]for j in range(X.cols))
        he=(mp.fsum(a*a for a in residual)-trPV)/(len(y)-X.cols)
        self.compare(key+"/HE_source_equation",he,subject.get("HE"))
        self.compare(key+"/initial_source_equation",max(mp.mpf(0),he),subject.get("initial"))
        trace=subject.get("iterations")
        if not isinstance(trace,list):
            self.record(key+"/trace_type","array",trace,False,"solver_evidence");return
        self.record(key+"/trace_length_cap",True,0<len(trace)<=(100 if source_converged else 101),0<len(trace)<=(100 if source_converged else 101),"max100_or_retained_iteration101_failure")
        previous=M(subject["initial"])
        lastchange=None
        for i,t in enumerate(trace):
            prefix=key+"/iterations/%d"%i
            if not isinstance(t,dict):
                self.record(prefix,"object",t,False,"solver_evidence");continue
            self.compare(prefix+"/old_tau2_continuity",previous,t.get("old_tau2"))
            old=M(t["old_tau2"]);q=weighted_contract(yc,v,X,old)
            update=(q["yPPy"]-q["trP"])/q["trPP"]
            halvings=0
            if old==0 and update<0:
                x=float(update)
                while x<0:x/=2;halvings+=1
                update=mp.mpf(0)
            else:
                while old+update<0:update/=2;halvings+=1
            self.compare(prefix+"/update_source_equation",update,t.get("update"))
            nexttau=old+update
            self.compare(prefix+"/new_tau2_source_equation",nexttau,t.get("new_tau2"))
            change=abs(nexttau-old)
            self.compare(prefix+"/change_source_equation",change,t.get("change"))
            self.record(prefix+"/nonnegative",True,nexttau>=0,nexttau>=0,"source_tau_boundary")
            if i<len(trace)-1:
                self.record(prefix+"/fixed_continue",True,M(t["change"])>THRESHOLD,M(t["change"])>THRESHOLD,"source_default_stopping")
            previous=M(t["new_tau2"]);lastchange=M(t["change"])
        if not source_converged:
            self.record(key+"/retained_nonconvergence",101,len(trace),len(trace)==101,"source_max100_overflow")
            return
        self.record(key+"/fixed_final_stop",True,lastchange is not None and lastchange<=THRESHOLD,
                    lastchange is not None and lastchange<=THRESHOLD,"source_default_stopping")
        base=weighted_contract(yc,v,X,mp.mpf(0))
        final=weighted_contract(yc,v,X,previous)
        reset=base["loglike"]-final["loglike"]>LL0_TOL and previous>THRESHOLD
        self.record(key+"/boundary_reset",bool(reset),subject.get("boundary_ll0_reset"),
                    subject.get("boundary_ll0_reset")==bool(reset),"source_boundary_likelihood")
        self.compare(key+"/final_source_tau",mp.mpf(0)if reset else previous,actual_pool.get("tau2_calc",actual_pool.get("tau2")))
    def close(self):
        self.stream.flush();self.stream.close()
        return {"checks":self.count,"failures":self.failures,"family_counts":self.family_counts,
                "failure_paths":self.failure_paths}

def verify_freeze(freeze):
    failures=[]
    for d in freeze["files"]:
        path=Path(d["absolute_path"])
        if not path.is_file()or path.stat().st_size!=d["bytes"]or sha256_file(path)!=d["sha256"]:
            failures.append(d["absolute_path"])
    if failures:raise RuntimeError("immutable source/runtime/code hash preflight: "+repr(failures))
    return len(freeze["files"])

def authorization_preflight(args,freeze):
    auth=read_literal(args.authorization)
    if auth.get("execution_authorized")is not True or auth.get("mode")!=args.mode:
        raise RuntimeError("exact one-shot root authorization absent or wrong mode")
    checks={"audit_freeze_sha256":sha256_file(args.freeze),
            "auditor_sha256":sha256_file(__file__),
            "run_absolute_path":str(Path(args.run).resolve()),
            "audit_absolute_path":str(Path(args.audit).resolve())}
    for key,value in checks.items():
        if auth.get(key)!=value:raise RuntimeError("root authorization mismatch "+key)
    if freeze["config"]["mode"]!=args.mode:raise RuntimeError("frozen input mode mismatch")
    if Path(args.audit).exists():raise RuntimeError("unique audit path already exists; no retry/resume")
    return auth

def reconstruct_inputs(config):
    forest=read_literal(config["raw_path"])
    metadata=read_literal(config["metadata_path"])
    appraisals=read_literal(config["appraisals_path"])
    conflicts=read_literal(config["conflicts_path"])
    if config["raw_format"]=="forest_original":
        canonical=canonical_original(forest,metadata,appraisals,conflicts)
    elif config["raw_format"]=="canonical_fixture":
        # Fixture raw event/N/year values only; geometry and source identities remain frozen.
        required={"id","family","forest_row","canonical_index","study_literal",
                  "year","events","N","group","country_B","country_Figure2"}
        rows=[]
        for row in forest["rows"]:
            if set(row)!=required:raise ValueError("fixture exact independent raw fields")
            rows.append(dict(row))
        canonical={"rows":rows,"metadata":metadata,"appraisals":appraisals,"conflicts":conflicts}
    else:raise RuntimeError("unregistered raw input format")
    return canonical

def independent_engineering(result):
    """Every unrelated declarative43 predicate; not original source target fitting."""
    records=[];extra={}
    def add(identifier,passed,observed=None,expected=None):
        records.append({"id":identifier,"passed":bool(passed),"observed":observed,
                        "expected":expected,"scientific_credit":False})
    for text,expected in zip(("1.245","1.255","-1.245","-1.255"),("1.24","1.26","-1.24","-1.26")):
        got=str(Decimal(text).quantize(Decimal(".01"),rounding=ROUND_HALF_EVEN))
        add("half_even_"+text,got==expected,got,expected)
    for value,expected in zip((0.0,0.00009999,0.0001,-0.0001),(True,True,False,False)):
        got=Decimal(str(value))>=0 and Decimal(str(value))<Decimal(".0001")
        add("strict_inequality_"+str(value),got==expected,bool(got),expected)
    row={"id":"edge.singleton","canonical_index":1,"events":11,"N":37,"year":2013,
         "family":"awareness","forest_row":1,"group":"students",
         "country_B":"FAKE_A","country_Figure2":"FAKE_A"}
    single=guarded_pool([row],"PFT","REML");extra["singleton"]=single
    add("singleton_no_deletion",single.get("status")=="ok"and single["input_ids"]==[row["id"]]and single["k"]==1)
    add("singleton_heterogeneity_NA",single.get("status")=="ok"and single["Q"]==0 and single["Q_df"]==0 and all(single[key]is None for key in("tau2","I2_pct","heterogeneity_p")))
    add("singleton_PI_NA",single.get("status")=="ok"and all(single["prediction"][key]is None for key in("df","SE","low_effect","high_effect","low","high")))
    legacy=guarded_pool([row],"PRAW","DL",legacy=True);extra["legacy_singleton"]=legacy
    a,b=CP(11,37)
    add("legacy_singleton_CP",legacy.get("status")=="ok"and legacy["Q"]is None and legacy["random"]["low"]==a and legacy["random"]["high"]==b)
    identical=[dict(row,id="edge.homogeneous.%d"%i)for i in range(4)]
    extra["homogeneous"]={}
    for scale in("PFT","PAS","PLOGIT","PRAW"):
        for method in("REML","DL"):
            identifier="homogeneous_"+scale+"_"+method
            p=guarded_pool(identical,scale,method)
            extra["homogeneous"][identifier]=p
            passed=p.get("status")=="ok"and p["Q"]==0 and p["tau2"]==0 and p["I2_pct"]==0
            add(identifier,passed,p.get("tau2"),0)
    extra["boundaries"]={}
    for index,event in enumerate((0,37)):
        edge=dict(row,id="edge.zero"if index==0 else"edge.all",events=event)
        a,b=CP(event,37);value=a if index==0 else b
        add("CP_boundary_%d"%index,value==index,value,index)
        for scale in("PFT","PAS","PLOGIT"):
            try:
                y,v,c=transform(event,37,scale);passed=mp.isfinite(y)and mp.isfinite(v)and v>0
                extra["boundaries"]["%d_%s"%(index,scale)]={"effect":y,"variance":v,"increment":c}
            except Exception as e:
                passed=False;extra["boundaries"]["%d_%s"%(index,scale)]={"error":str(e)}
            add("finite_boundary_%d_%s"%(index,scale),passed)
        p=guarded_pool([edge],"PRAW","DL",legacy=True)
        extra["boundaries"]["%d_legacy"%index]=p
        add("legacy_boundary_explicit_failure_%d"%index,p.get("status")=="not_estimable"and p.get("input_ids")==[edge["id"]])
    rank=guarded_model(identical,"PFT","REML",["intercept","duplicate"],[[1,1]for _ in identical])
    saturated=guarded_model(identical,"PFT","REML",["one","two","three","four"],
                           [[int(i==j)for j in range(4)]for i in range(4)])
    extra["rank_deficient"]=rank;extra["saturated"]=saturated
    add("fixed_rank_failure",rank.get("status")=="not_estimable"and rank.get("input_ids")==[r["id"]for r in identical]and rank.get("columns")==["intercept","duplicate"])
    add("saturated_failure",saturated.get("status")=="not_estimable"and saturated.get("input_ids")==[r["id"]for r in identical])
    n=mp.mpf(37)
    minimum=mp.asin(mp.sqrt(1/(n+1)))/2
    maximum=(mp.asin(mp.sqrt(n/(n+1)))+mp.pi/2)/2
    add("Miller_below_min",inverse(minimum-mp.mpf(".000001"),"PFT",n)==0)
    add("Miller_above_max",inverse(maximum+mp.mpf(".000001"),"PFT",n)==1)
    add("complete_six_pipeline_census",set(result["pipelines"])==set(p[0]for p in PIPELINES))
    expected={"full":3,"groups":8,"LOO":43,"simultaneous":3,"univariate":9,"country":6,"Egger":3}
    for identifier,scale,method in PIPELINES:
        f=result["pipelines"][identifier]["families"]
        observed={"full":len(f),"groups":sum(len(d["groups"])for d in f.values()),
          "LOO":sum(len(d["LOO"])for d in f.values()),"simultaneous":sum("simultaneous"in d for d in f.values()),
          "univariate":sum(len(d["univariate"])for d in f.values()),
          "country":sum(len(d["country"])for d in f.values()),"Egger":sum("Egger"in d for d in f.values())}
        add("pipeline_census_"+identifier,observed==expected,observed)
    bcount=sum(1+len(f["groups"])+len(f["LOO"])for p in result["backsize_views"].values()for f in p["families"].values())
    add("all_backsize_views",bcount==270)
    add("all_legacy_nested_LOO",len(result["legacy_RAWDL001"])==3 and sum(len(f["LOO"])for f in result["legacy_RAWDL001"].values())==43)
    if len(records)!=43:raise RuntimeError("whole unrelated engineering43 census")
    wrapper={"checks":records,"all_pass":all(d["passed"]for d in records),
             "strict_failures_retained":True,
             "scope":"Unrelated engineering fixture; final complete independent comparison required; no original target matching/scientific credit"}
    return wrapper,extra

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("fixture","original"),required=True)
    parser.add_argument("--run",required=True)
    parser.add_argument("--audit",required=True)
    parser.add_argument("--freeze",required=True)
    parser.add_argument("--authorization",required=True)
    args=parser.parse_args()
    freeze=read_literal(args.freeze);authorization_preflight(args,freeze)
    verified=verify_freeze(freeze)
    destination=Path(args.audit);destination.mkdir()
    started=time.monotonic();startutc=datetime.now(timezone.utc).isoformat()
    def progress(phase,detail):
        with(destination/"phase_events.jsonl").open("a",encoding="utf-8",newline="\n")as stream:
            stream.write(json.dumps({"utc":datetime.now(timezone.utc).isoformat(),"phase":phase,
                                    "elapsed":time.monotonic()-started,"detail":detail},ensure_ascii=True)+"\n")
        progresspath=destination/"progress.json"
        temporary=destination/"progress.tmp"
        temporary.write_text(json.dumps({"phase":phase,"detail":detail,
                            "elapsed":time.monotonic()-started},ensure_ascii=True),encoding="utf-8")
        os.replace(temporary,progresspath)
    try:
        config=freeze["config"]
        canonical=reconstruct_inputs(config);census=independent_census(canonical)
        targets=read_literal(config["targets_path"])
        canonical["gates"]=targets
        if args.mode=="fixture":
            canonical["fixture"]={"unrelated":True,"recipe":"N=103+7*canonical_index+3*family_index;events=17+(29*index+13*family_index)mod(N-33);year=2011+indexmod7",
                "RNG":"none","original_numeric_fields_used":False,"not_scientific_credit":True}
            for r in canonical["rows"]:
                index=r["canonical_index"];familyindex=FAMILIES.index(r["family"])
                n=103+7*index+3*familyindex;e=17+(29*index+13*familyindex)%(n-33);year=2011+index%7
                if(r["N"],r["events"],r["year"])!=(n,e,year):raise ValueError("exact unrelated fixture recipe")
        if len(targets["input_gates"])!=129 or len(targets["primary_output_gates"])!=263 or len(targets["supporting_literal_gates"])!=114:
            raise ValueError("prospective complete506 target source census")
        progress("independent_complete_input_reconstruction",census)
        result=calculate_all(canonical["rows"],progress)
        if args.mode=="fixture":
            engineering,edge_records=independent_engineering(result)
            result["engineering_checks"]=engineering
            write_json(destination/"INDEPENDENT_ALL43_ENGINEERING_EDGE_RECORDS.json",edge_records)
        result["mode"]=args.mode
        structural={}
        for identifier,_,_ in PIPELINES:
            families=result["pipelines"][identifier]["families"]
            structural[identifier]={"full":len(families),
                "groups":sum(len(v["groups"])for v in families.values()),
                "LOO":sum(len(v["LOO"])for v in families.values()),
                "simultaneous":len(families),
                "univariate":sum(len(v["univariate"])for v in families.values()),
                "country":sum(len(v["country"])for v in families.values()),
                "Egger":len(families)}
        result["structural_census"]={"pipelines":structural,
            "backsize_pool_views":sum(1+len(v["groups"])+len(v["LOO"])for p in result["backsize_views"].values()for v in p["families"].values()),
            "legacy_full":len(result["legacy_RAWDL001"]),
            "legacy_nested_LOO":sum(len(v["LOO"])for v in result["legacy_RAWDL001"].values()),
            "scientific_pass_decided_by_audit_and_root_only":True}
        if args.mode=="fixture":result["fixture"]=canonical["fixture"]
        output_values(result,targets)
        comparisons=all_source_comparisons(canonical,result,targets)if args.mode=="original"else[]
        independent_claims=source_claims(result,comparisons,canonical,census)if args.mode=="original"else None
        result["source_claims"]=public_source_claims(independent_claims)
        wrapper=source_wrapper(canonical,result,comparisons,targets,args.mode)
        write_json(destination/"INDEPENDENT_CANONICAL_INPUT.json",canonical)
        write_json(destination/"INDEPENDENT_COMPLETE_RESULT.json",result)
        write_json(destination/"INDEPENDENT_ALL506_SOURCE_COMPARISONS.json",wrapper)
        write_json(destination/"INDEPENDENT_SUPPORTING_CLAIM_DIAGNOSTICS.json",independent_claims)
        progress("independent_complete_before_subject_numeric_read",{"pipeline_count":6,"LOO":258,
                 "backsize_views":270,"legacy_nested_LOO":43,"source_comparisons":506})
        # Numerical subject outputs opened only after complete independent reconstruction.
        subject=read_literal(Path(args.run)/"result.json")
        subject_input=read_literal(Path(args.run)/"canonical_input.json")
        subject_gates=read_literal(Path(args.run)/"gate_comparisons.json")
        audit=WholeAudit(destination/"ALL_INDEPENDENT_CHECKS.jsonl")
        audit.compare("canonical_input",canonical,subject_input)
        for key in("schema","mode","structural_census","architecture_GLMM","pipelines","backsize_views","legacy_RAWDL001",
                   "primary_output_values","supporting_output_values"):
            audit.compare(key,result[key],subject.get(key))
        audit.record("result/__complete_top_keys__",sorted(result),sorted(subject),set(result)==set(subject),"complete_public_top_field_set")
        if args.mode=="fixture":
            audit.compare("fixture",result["fixture"],subject.get("fixture"))
            audit.compare("engineering_checks",result["engineering_checks"],subject.get("engineering_checks"))
        # Original whole506 source comparisons or exact unrelated fixture ID-only wrapper.
        audit_source_wrapper(audit,wrapper,subject_gates,args.mode)
        audit.compare("source_claims",result["source_claims"],subject.get("source_claims"))
        summary=audit.close()
        source_primary=[d for d in comparisons if d["role"]in("PRIMARY_EXACT_INPUT","PRIMARY_FOREST_OUTPUT")]
        summary.update({"status":"PASS"if summary["failures"]==0 else"FAIL",
             "start_utc":startutc,"end_utc":datetime.now(timezone.utc).isoformat(),
             "elapsed":time.monotonic()-started,"source_freeze_files_verified":verified,
             "mode":args.mode,"decimal_digits":80,"numeric_absolute":1e-10,"numeric_relative":1e-10,
             "source_primary_count":len(source_primary),"source_primary_passes":sum(d["passed"]for d in source_primary)if args.mode=="original"else None,
             "source_support_count":114,"source_support_passes":sum(d["passed"]for d in comparisons[-114:])if args.mode=="original"else None,
             "source_failed_all_primary_has_no_rescue":not all(d["passed"]for d in source_primary)if args.mode=="original"else None,
             "input_census":census,"complete_pipeline_count":6,"complete_canonical_LOO":258,
             "complete_backsize_views":270,"legacy_full_families":3,"legacy_nested_LOO":43,
             "independence":"Original auditor001/002 mathematics independently derived without primary-source access. Source-only adapter/status repair003 reviewer read both frozen sources after failed fixture026; mathematical solver and fixed tolerance preserved. No primary mathematics imported. Subject numerical outputs opened only after all independent calculations.",
             "native_closure":"External root guardian/collector must separately retain actual native exits, final peaks and all creation-matched owned absences."})
        write_json(destination/"AUDIT_STATUS.json",summary)
        progress("audit_complete",{"checks":summary["checks"],"failures":summary["failures"]})
        files=[]
        for path in sorted(destination.iterdir()):
            if path.is_file():
                files.append({"absolute_path":str(path.resolve()),"bytes":path.stat().st_size,
                              "sha256":sha256_file(path)})
        write_json(destination/"AUDIT_MANIFEST.json",{"utc":datetime.now(timezone.utc).isoformat(),"files":files,
            "input_freeze":{"absolute_path":str(Path(args.freeze).resolve()),"sha256":sha256_file(args.freeze)}})
        return 0 if summary["failures"]==0 else 2
    except Exception as e:
        write_json(destination/"AUDIT_STOP.json",{"status":"FAILED_OR_STOPPED_NO_RETRY",
           "error":type(e).__name__+": "+str(e),"traceback":traceback.format_exc(),
           "start_utc":startutc,"end_utc":datetime.now(timezone.utc).isoformat(),
           "elapsed":time.monotonic()-started,"preserved_all_previous_outputs":True})
        return 3

if __name__=="__main__":
    raise SystemExit(main())
