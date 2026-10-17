"""P161 independently derived fsum mathematics. Definitions only on import.

No primary implementation or result is imported. SciPy special distribution
tails and NumPy symmetric eigensolver are injected by an admitted caller.
"""
import math

def average(x):
    return math.fsum(x)/len(x)if x else None

def centered(x):
    m=average(x)
    return m,[v-m for v in x]if m is not None else[]

def variance(x):
    if len(x)<2:return None
    m,d=centered(x);return math.fsum(v*v for v in d)/(len(x)-1)

def deviation(x):
    v=variance(x);return math.sqrt(v)if v is not None else None

def percentile(x,q):
    if not x:return None
    y=sorted(x);z=(len(y)-1)*q;i=int(math.floor(z));f=z-i
    return y[i]if i==len(y)-1 else y[i]+f*(y[i+1]-y[i])

def descriptive(x):
    n=len(x);m,d=centered(x);v=variance(x)
    out=dict(n=n,sum=math.fsum(x),mean=m,SD=math.sqrt(v)if v is not None else None,
        minimum=min(x)if n else None,maximum=max(x)if n else None,
        skewness_raw=None,kurtosis_raw_excess=None,skewness_corrected=None,kurtosis_corrected_excess=None)
    if n and math.fsum(a*a for a in d)>0:
        m2=math.fsum(a*a for a in d)/n;m3=math.fsum(a**3 for a in d)/n;m4=math.fsum(a**4 for a in d)/n
        g1=m3/(m2**1.5);g2=m4/(m2*m2)-3
        out.update(skewness_raw=g1,kurtosis_raw_excess=g2)
        if n>2:out['skewness_corrected']=math.sqrt(n*(n-1))/(n-2)*g1
        if n>3:out['kurtosis_corrected_excess']=(n-1)/((n-2)*(n-3))*((n+1)*g2+6)
    return out

def ranks(x):
    ordered=sorted(range(len(x)),key=lambda i:x[i]);out=[None]*len(x);i=0
    while i<len(ordered):
        j=i+1
        while j<len(ordered)and x[ordered[j]]==x[ordered[i]]:j+=1
        value=(i+1+j)/2
        for k in range(i,j):out[ordered[k]]=value
        i=j
    return out

def t_tail(t,df,special):
    return min(1.,2*float(special.stdtr(df,-abs(t))))if t is not None and df>0 else None

def association(x,y,special):
    assert len(x)==len(y)
    n=len(x);mx,dx=centered(x);my,dy=centered(y)
    sx=math.fsum(v*v for v in dx);sy=math.fsum(v*v for v in dy);cross=math.fsum(a*b for a,b in zip(dx,dy))
    out=dict(n=n,mean_x=mx,mean_y=my,SSx=sx,SSy=sy,Sxy=cross,r=None,t=None,df=n-2,p=None)
    if n<3 or sx<=0 or sy<=0:return out
    r=cross/math.sqrt(sx*sy)
    if abs(r)>1:
        if abs(r)>1+2e-14:raise ArithmeticError('Correlation outside mathematical range')
        r=math.copysign(1.,r)
    out['r']=r
    if abs(r)==1:out['p']=0.;return out
    t=r*math.sqrt((n-2)/((1-r)*(1+r)));out.update(t=t,p=t_tail(t,n-2,special));return out

def correlations(x,y,special):
    rx=ranks(x);ry=ranks(y)
    return dict(pearson=association(x,y,special),spearman_asymptotic=association(rx,ry,special),
        ranks_x=rx,ranks_y=ry,spearman_exact_or_permutation=dict(status='UNESTABLISHED',value=None,
        reason='No exact permutation producer recovered; no invented Monte Carlo or91! enumeration.'))

def paired(x,y,special):
    assert len(x)==len(y)
    d=[a-b for a,b in zip(x,y)];n=len(d);m=average(d);sd=deviation(d)
    out=dict(n=n,df=n-1,differences=d,mean_difference=m,SD_difference=sd,t=None,p_two_tailed=None,Bonferroni_p=None,Cohen_d=None)
    if n>1 and sd is not None and sd>0:
        t=m*math.sqrt(n)/sd;p=t_tail(t,n-1,special)
        out.update(t=t,p_two_tailed=p,Bonferroni_p=min(1.,3*p),Cohen_d=m/sd)
    return out

def icc_absolute_two_way(matrix):
    n=len(matrix);k=2
    assert all(len(row)==k for row in matrix)
    out=dict(n=n,k=k,grand_mean=None,row_means=[],column_means=[],SS_rows=None,SS_columns=None,SS_error=None,
        df_rows=n-1,df_columns=k-1,df_error=(n-1)*(k-1),MS_rows=None,MS_columns=None,MS_error=None,single=None,average=None)
    if n<2:return out
    grand=math.fsum(v for row in matrix for v in row)/(n*k)
    rm=[math.fsum(row)/k for row in matrix];cm=[math.fsum(row[j]for row in matrix)/n for j in range(k)]
    ssr=k*math.fsum((m-grand)**2 for m in rm);ssc=n*math.fsum((m-grand)**2 for m in cm)
    sse=math.fsum((matrix[i][j]-rm[i]-cm[j]+grand)**2 for i in range(n)for j in range(k))
    msr=ssr/(n-1);msc=ssc/(k-1);mse=sse/((n-1)*(k-1))
    d1=msr+(k-1)*mse+k*(msc-mse)/n;dk=msr+(msc-mse)/n
    out.update(grand_mean=grand,row_means=rm,column_means=cm,SS_rows=ssr,SS_columns=ssc,SS_error=sse,
        MS_rows=msr,MS_columns=msc,MS_error=mse,single=(msr-mse)/d1 if d1 else None,average=(msr-mse)/dk if dk else None)
    return out

def covariance(x,y):
    if len(x)!=len(y)or len(x)<2:return None
    mx=average(x);my=average(y)
    return math.fsum((a-mx)*(b-my)for a,b in zip(x,y))/(len(x)-1)

def item_matrices(rows,case_keys,policy):
    assert len(rows)==len(case_keys)
    p=9;complete=[i for i,row in enumerate(rows)if all(v is not None for v in row)]
    original=[list(row)for row in rows];substitutions=[]
    if policy=='listwise':indices=complete;data=[list(rows[i])for i in indices];keys=[case_keys[i]for i in indices]
    elif policy=='mean_substitution':
        means=[average([row[j]for row in rows if row[j]is not None])for j in range(p)]
        data=[];keys=list(case_keys)
        for i,row in enumerate(rows):
            new=[]
            for j,v in enumerate(row):
                if v is None:substitutions.append(dict(case_key=case_keys[i],criterion1=j+1,replacement=means[j]))
                new.append(v if v is not None else means[j])
            data.append(new)
    elif policy=='pairwise':data=original;keys=list(case_keys)
    else:raise ValueError('Unfrozen matrix missingness policy')
    cov=[];corr=[];ns=[];ids=[]
    for j in range(p):
        cv=[];cr=[];nn=[];cc=[]
        for k in range(p):
            selected=[i for i,row in enumerate(data)if row[j]is not None and row[k]is not None]
            x=[data[i][j]for i in selected];y=[data[i][k]for i in selected]
            c=covariance(x,y);vx=variance(x);vy=variance(y)
            cv.append(c);cr.append(c/math.sqrt(vx*vy)if c is not None and vx is not None and vy is not None and vx>0 and vy>0 else None)
            nn.append(len(selected));cc.append([keys[i]for i in selected])
        cov.append(cv);corr.append(cr);ns.append(nn);ids.append(cc)
    return dict(policy=policy,source_rows=original,matrix_rows=data,matrix_case_keys=keys,listwise_case_keys=[case_keys[i]for i in complete],
        covariance=cov,correlation=corr,pair_N=ns,pair_case_keys=ids,substitutions=substitutions)

def alpha_from_matrix(matrix,standardized=False):
    k=len(matrix)
    if any(v is None for row in matrix for v in row):return None
    total=math.fsum(v for row in matrix for v in row)
    diagonal=math.fsum(matrix[i][i]for i in range(k))
    return k/(k-1)*(1-diagonal/total)if total else None

def alpha_variants(rows,case_keys):
    out={}
    for policy in('listwise','pairwise'):
        m=item_matrices(rows,case_keys,policy)
        out[policy]=dict(matrices=m,raw=alpha_from_matrix(m['covariance']),standardized=alpha_from_matrix(m['correlation']),
            diagnostic_only=policy=='pairwise')
    return out

def pca_variants(rows,case_keys,np):
    out={}
    for policy in('listwise','pairwise','mean_substitution'):
        m=item_matrices(rows,case_keys,policy)
        for kind in('correlation','covariance'):
            matrix=m[kind];values=None;percentage=None;cumulative=None;reason=None
            if any(v is None for row in matrix for v in row):reason='Undefined matrix entries/zero variance/insufficient cases'
            else:
                # Shared elementary eigensolver only; all covariance/correlation
                # matrices above are independently derived via fsum.
                eigen,_=np.linalg.eigh(np.asarray(matrix,dtype=np.float64));values=[float(v)for v in eigen[::-1]]
                trace=math.fsum(matrix[i][i]for i in range(9))
                if trace:
                    percentage=[100*v/trace for v in values];cumulative=[math.fsum(percentage[:i+1])for i in range(9)]
                else:reason='Zero matrix trace'
            out[kind+'_'+policy]=dict(matrix=matrix,missingness=m,eigenvalues_descending=values,
                explained_percent=percentage,cumulative_percent=cumulative,reason=reason,
                negative_eigenvalues_not_truncated=True,eigenvector_sign_or_identity_not_compared=True)
    return out

def bland_altman(x,y,special):
    xs=[(a+b)/2 for a,b in zip(x,y)];ys=[a-b for a,b in zip(x,y)];n=len(xs)
    mx=average(xs);my=average(ys);sd=deviation(ys)
    xss=math.fsum((v-mx)**2 for v in xs);yss=math.fsum((v-my)**2 for v in ys)
    cross=math.fsum((a-mx)*(b-my)for a,b in zip(xs,ys));slope=cross/xss if xss else None
    intercept=my-slope*mx if slope is not None else None
    fitted=[intercept+slope*a for a in xs]if slope is not None else None
    residuals=[b-f for b,f in zip(ys,fitted)]if fitted is not None else None
    sse=math.fsum(e*e for e in residuals)if residuals is not None else None
    se=math.sqrt(sse/(n-2)/xss)if n>2 and xss and sse is not None else None
    t=slope/se if se else None;p=t_tail(t,n-2,special)
    return dict(n=n,x_pair_mean=xs,y_AI_minus_human=ys,mean_bias=my,SD_difference=sd,
        LOA_lower=my-1.96*sd if sd is not None else None,LOA_upper=my+1.96*sd if sd is not None else None,
        intercept=intercept,slope=slope,fitted=fitted,residuals=residuals,SSE=sse,Sxx=xss,Syy=yss,Sxy=cross,
        slope_SE=se,slope_t=t,slope_df=n-2,slope_p=p,R2=1-sse/yss if yss and sse is not None else None)

def band(value):
    return 0 if value<50 else 1 if value<70 else 2 if value<85 else 3

def kappa_all(x,y):
    catsx=[band(v)for v in x];catsy=[band(v)for v in y];n=len(x);counts=[[0]*4 for _ in range(4)]
    for a,b in zip(catsx,catsy):counts[a][b]+=1
    row=[sum(r)for r in counts];col=[sum(counts[i][j]for i in range(4))for j in range(4)]
    out={}
    for label in('linear','quadratic','unweighted'):
        weights=[[1-abs(i-j)/3 if label=='linear'else 1-((i-j)/3)**2 if label=='quadratic'else float(i==j)for j in range(4)]for i in range(4)]
        if not n:
            out[label]=dict(coefficient=None,reason='No complete pairs');continue
        p=[[v/n for v in r]for r in counts];r=[v/n for v in row];c=[v/n for v in col]
        observed=math.fsum(weights[i][j]*p[i][j]for i in range(4)for j in range(4))
        expected=math.fsum(weights[i][j]*r[i]*c[j]for i in range(4)for j in range(4));den=1-expected
        coefficient=(observed-expected)/den if den else None
        observed_var=null_var=None
        if den:
            wr=[math.fsum(weights[i][j]*c[j]for j in range(4))for i in range(4)]
            wc=[math.fsum(weights[i][j]*r[i]for i in range(4))for j in range(4)]
            g=[[(weights[i][j]*den-(1-observed)*(wr[i]+wc[j]))/(den*den)for j in range(4)]for i in range(4)]
            g0=[[(weights[i][j]-wr[i]-wc[j])/den for j in range(4)]for i in range(4)]
            mu=math.fsum(p[i][j]*g[i][j]for i in range(4)for j in range(4))
            mu0=math.fsum(r[i]*c[j]*g0[i][j]for i in range(4)for j in range(4))
            # Multinomial delta variance is the weighted central second
            # moment of the influence values, divided by n. This equivalent
            # nonnegative form avoids subtracting two nearly equal moments;
            # no numerical threshold or published-zero substitution is used.
            observed_var=math.fsum(p[i][j]*(g[i][j]-mu)**2 for i in range(4)for j in range(4))/n
            null_var=math.fsum(r[i]*c[j]*(g0[i][j]-mu0)**2 for i in range(4)for j in range(4))/n
        obsse=math.sqrt(observed_var)if observed_var is not None else None
        nullse=math.sqrt(null_var)if null_var is not None else None
        z=coefficient/nullse if coefficient is not None and nullse else None
        out[label]=dict(coefficient=coefficient,weights=weights,observed_agreement=observed,expected_agreement=expected,
            observed_delta_variance=observed_var,observed_delta_SE=obsse,null_independence_variance=null_var,
            null_independence_SE=nullse,null_normal_z=z,null_normal_p=math.erfc(abs(z)/math.sqrt(2))if z is not None else None,
            diagnostic_not_recovered_SPSS_test=True,source_exact_weighted_SE_p_status='UNESTABLISHED',
            reason=None if coefficient is not None else'Expected agreement equals one')
    distances=[abs(a-b)for a,b in zip(catsx,catsy)]
    return dict(n=n,categories_x=catsx,categories_y=catsy,counts=counts,row_margins=row,column_margins=col,
        exact_count=distances.count(0),exactly_one_count=distances.count(1),two_or_more_count=sum(d>=2 for d in distances),
        exact_percent=100*distances.count(0)/n if n else None,exactly_one_percent=100*distances.count(1)/n if n else None,
        two_or_more_percent=100*sum(d>=2 for d in distances)/n if n else None,kappa=out)

def levene(groups,special,centering):
    if centering not in('mean','median'):raise ValueError('Unfrozen Levene centering')
    centers=[average(g)if centering=='mean'else percentile(g,.5)for g in groups]
    transformed=[[abs(v-c)for v in g]for g,c in zip(groups,centers)]
    N=sum(len(g)for g in groups);k=len(groups);means=[average(g)for g in transformed]
    grand=math.fsum(v for g in transformed for v in g)/N if N else None
    ssb=math.fsum(len(g)*(m-grand)**2 for g,m in zip(transformed,means))if N else None
    ssw=math.fsum((v-m)**2 for g,m in zip(transformed,means)for v in g)if N else None
    F=(ssb/(k-1))/(ssw/(N-k))if N>k and k>1 and ssw else None
    return dict(centering=centering,centers=centers,transformed=transformed,group_N=[len(g)for g in groups],
        transformed_group_means=means,SS_between=ssb,SS_within=ssw,df1=k-1,df2=N-k,F=F,
        p=float(special.fdtrc(k-1,N-k,F))if F is not None else None,
        repeated_ratings_dependence_not_modelled=True)

def reconstructed_boxplot(x):
    q1=percentile(x,.25);med=percentile(x,.5);q3=percentile(x,.75)
    if q1 is None:return dict(values=x,reason='No finite scores')
    lower=q1-1.5*(q3-q1);upper=q3+1.5*(q3-q1);inside=[v for v in x if lower<=v<=upper]
    return dict(values=x,sorted_values=sorted(x),q1=q1,median=med,q3=q3,
        lower_fence=lower,upper_fence=upper,lower_whisker=min(inside)if inside else None,
        upper_whisker=max(inside)if inside else None,outliers=[v for v in x if v<lower or v>upper],
        conditional_reconstruction=True,rule='Linear R7 quartiles;1.5IQR nearest observed whiskers;original producer unknown')

def reconstructed_density(x):
    edges=[float(v)for v in range(0,101,5)];counts=[0]*20
    for v in x:
        if 0<=v<=100:counts[min(19,int(v//5))]+=1
        else:raise ValueError('Score outside prospectively frozen reconstruction0..100 range')
    n=len(x);sd=deviation(x);bandwidth=sd*n**(-.2)if n and sd else None
    grid=[i/4 for i in range(401)]
    density=[math.fsum(math.exp(-.5*((t-v)/bandwidth)**2)for v in x)/(n*bandwidth*math.sqrt(2*math.pi))for t in grid]if bandwidth else None
    return dict(values=x,bin_edges=edges,counts=counts,histogram_density=[c/(n*5)for c in counts]if n else None,
        KDE_grid=grid,KDE_density=density,KDE_bandwidth=bandwidth,conditional_reconstruction=True,
        rule='Fixed5point bins0..100;Gaussian Scott sampleSD*n^-1/5;401grid0..100;original producer unknown')
