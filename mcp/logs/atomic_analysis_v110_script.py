#!/usr/bin/env python3
"""Atomi analizis v1.10 Jules CFD — minden predikcios jel darabokra szedese"""
import pandas as pd, numpy as np, joblib, warnings, os, json, lightgbm as lgb
from sklearn.model_selection import train_test_split
warnings.filterwarnings('ignore')

PROD='/data/dev/projects/z-ai-copilot/models/production_v110_jules'
PROC='/data/dev/projects/z-ai-copilot/Master_csv/processed'

m=joblib.load(os.path.join(PROD,'lgbm_v110_jules.pkl'))
feat=open(os.path.join(PROD,'features.txt')).read().strip().split('\n')
df=pd.read_csv(os.path.join(PROC,'jules_v110_labeled.csv'))
df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
df['Start_Timestamp']=pd.to_datetime(df['Start_Timestamp'])
df.sort_values('End_Timestamp',inplace=True); df.reset_index(drop=True,inplace=True)
si=int(len(df)*0.8)
tr=df.iloc[:si].copy(); oo=df.iloc[si:].copy().reset_index(drop=True)

R={}

print('='*70+'\nATOMI ANALIZIS v1.10 Jules CFD\n'+'='*70)

# 1. DOLLAR BAR MERET
sec_tr=(tr['End_Timestamp']-tr['Start_Timestamp']).dt.total_seconds()
sec_oo=(oo['End_Timestamp']-oo['Start_Timestamp']).dt.total_seconds()
R['bar_sec_tr_mean']=round(sec_tr.mean(),1); R['bar_sec_oo_mean']=round(sec_oo.mean(),1)
print(f'\n[1] DOLLAR BAR MERET')
print(f'  Train: mean={sec_tr.mean():.1f}s median={sec_tr.median():.1f}s DV=${tr["Total_Dollar_Value"].mean():,.0f}')
print(f'  OOS:   mean={sec_oo.mean():.1f}s median={sec_oo.median():.1f}s DV=${oo["Total_Dollar_Value"].mean():,.0f}')
print(f'  Jules: mean=37.6s median=21.0s DV=$630,430')

# 2. VALOSZINUSEG ELOSZLAS
X_oo=oo[feat].fillna(0).replace([np.inf,-np.inf],0)
y_oo=oo['Target_Label'].values
pr=m.predict_proba(X_oo); cl=m.classes_
i_s=list(cl).index(0); i_n=list(cl).index(1); i_l=list(cl).index(2)
pL=pr[:,i_l]; pS=pr[:,i_s]; pN=pr[:,i_n]
R['pL_zero']=int((pL==0).sum()); R['pS_zero']=int((pS==0).sum())
R['pL_mean']=round(float(pL.mean()),4); R['pS_mean']=round(float(pS.mean()),4); R['pN_mean']=round(float(pN.mean()),4)
print(f'\n[2] VALOSZINUSEG ELOSZLAS (OOS {len(oo):,})')
print(f'  P(L): min={pL.min():.4f} max={pL.max():.4f} mean={pL.mean():.4f} std={pL.std():.4f}')
print(f'  P(S): min={pS.min():.4f} max={pS.max():.4f} mean={pS.mean():.4f} std={pS.std():.4f}')
print(f'  P(N): min={pN.min():.4f} max={pN.max():.4f} mean={pN.mean():.4f} std={pN.std():.4f}')
print(f'  P(L)==0: {R["pL_zero"]} | P(S)==0: {R["pS_zero"]}')
print(f'  P(L)<0.01: {(pL<0.01).sum()} | P(S)<0.01: {(pS<0.01).sum()}')

# 3. BUCKETEK
print(f'\n[3] P(L) BUCKETEK')
for lo,hi in [(0,.1),(.1,.2),(.2,.3),(.3,.35),(.35,.4),(.4,.5),(.5,.6),(.6,1.01)]:
    cnt=((pL>=lo)&(pL<hi)).sum(); bar='█'*max(1,int(cnt/len(pL)*200))
    print(f'  [{lo:.2f}-{hi:.2f}): {cnt:5d} ({cnt/len(pL)*100:5.1f}%) {bar}')
print(f'\n  P(S) BUCKETEK')
for lo,hi in [(0,.1),(.1,.2),(.2,.3),(.3,.36),(.36,.4),(.4,.5),(.5,.6),(.6,1.01)]:
    cnt=((pS>=lo)&(pS<hi)).sum(); bar='█'*max(1,int(cnt/len(pS)*200))
    print(f'  [{lo:.2f}-{hi:.2f}): {cnt:5d} ({cnt/len(pS)*100:5.1f}%) {bar}')

# 4. THRESHOLD INTERAKCIO
sig_t=np.full(len(oo),1,dtype=int)
sig_t[(pL>.35)&(pL>pS)&(pN<.47)]=2; sig_t[(pS>.36)&(pS>pL)&(pN<.47)]=0
print(f'\n[4] THRESHOLD INTERAKCIO')
nb=(pN>=.47).sum(); cf=((pL>.35)&(pS>.36)).sum()
print(f'  Noise block (P(N)>=THN): {nb:,} ({nb/len(oo)*100:.1f}%)')
print(f'  CONFLICT (pL>THL & pS>THS): {cf:,} ({cf/len(oo)*100:.1f}%)')
print(f'  P(L)>P(S): {(pL>pS).sum():,} | P(S)>P(L): {(pS>pL).sum():,}')
R['noise_block_pct']=round(nb/len(oo)*100,1); R['conflict_pct']=round(cf/len(oo)*100,1)

# 5. JELOK LABEL-SZERINT
print(f'\n[5] JELOK LABEL-SZERINT (threshold)')
for lb,nm in [(1,'Long'),(0,'Noise'),(-1,'Short')]:
    mk=y_oo==lb
    if mk.sum()==0: continue
    pl=(sig_t[mk]==2).sum(); ps=(sig_t[mk]==0).sum(); pn=(sig_t[mk]==1).sum()
    print(f'  Actual {nm:6s} ({mk.sum():5,}): PredL={pl:4,} PredS={ps:4,} PredN={pn:5,}')

# 6. KONFUZIOS MATRIX (stability)
stoch=oo['Stoch_State_M1'].values
sig_f=sig_t.copy(); sig_f[(sig_t==2)&(stoch<0)]=1; sig_f[(sig_t==0)&(stoch>0)]=1
sig_s=np.full(len(sig_f),1,dtype=int)
for i in range(2,len(sig_f)):
    w=sig_f[i-2:i+1]
    if len(set(w))==1 and w[0]!=1: sig_s[i]=w[0]
print(f'\n[6] KONFUZIOS MATRIX (stability)')
print('           PredShort  PredNoise  PredLong')
for al,an in [(-1,'Short'),(0,'Noise'),(1,'Long')]:
    row=[f'{((y_oo==al)&(sig_s==pl)).sum():8,}' for pl in [-1,0,1]]
    print(f'  Act{an:5s} {" ".join(row)}')

# 7. DIRSWAP
ls=((y_oo==1)&(sig_s==0)).sum(); sl=((y_oo==-1)&(sig_s==2)).sum(); ts=(sig_s!=1).sum()
R['dirswap_pct']=round((ls+sl)/ts*100,1) if ts>0 else 0
print(f'\n[7] DIRSWAP: Long->Short={ls:,} Short->Long={sl:,} Total={ls+sl:,}/{ts:,} ({R["dirswap_pct"]:.1f}%)')

# 8. DIRASNOISE
dn_t=((y_oo!=0)&(sig_t==1)).sum(); dn_s=((y_oo!=0)&(sig_s==1)).sum()
R['dn_thr']=round(dn_t/len(oo)*100,1); R['dn_stab']=round(dn_s/len(oo)*100,1)
print(f'\n[8] DIRASNOISE: threshold={dn_t:,}({R["dn_thr"]}%) stability={dn_s:,}({R["dn_stab"]}%)')

# 9. STOCH FILTER
lk_l=((sig_t==2)&(stoch<0)).sum(); lk_s=((sig_t==0)&(stoch>0)).sum(); tt=(sig_t!=1).sum()
print(f'\n[9] STOCH KILL: Long={lk_l:,} Short={lk_s:,} Total={lk_l+lk_s:,}/{tt:,} ({(lk_l+lk_s)/tt*100:.1f}%)')

# 10. STABILITY FILTER
tsf=(sig_f!=1).sum(); tss=(sig_s!=1).sum()
print(f'\n[10] STABILITY KILL: {tsf-tss:,}/{tsf:,} ({(tsf-tss)/tsf*100:.1f}%)')

# 11. LOOKAHEAD AUDIT
print(f'\n[11] LOOKAHEAD AUDIT')
X_tr=tr[feat].fillna(0).replace([np.inf,-np.inf],0); y_tr=(tr['Target_Label']+1).astype(int).values
for sv in [1,0,2,3]:
    Xs=X_tr.copy()
    for c in feat: Xs[c]=Xs[c].shift(sv)
    v=Xs.dropna(); yv=y_tr[v.index]
    Xt,Xv,yt,yv2=train_test_split(v,yv,test_size=0.2,shuffle=False)
    tmp=lgb.LGBMClassifier(n_estimators=100,learning_rate=0.05,num_leaves=31,verbose=-1,n_jobs=1)
    tmp.fit(Xt,yt); acc=tmp.score(Xv,yv2)
    print(f'  shift={sv}: acc={acc:.4f}')

# 12. WIN STREAKS
print(f'\n[12] WIN STREAKS (stability)')
ws=[]; c=0
for i in range(len(sig_s)):
    if sig_s[i]==1: continue
    ok=(sig_s[i]==2 and y_oo[i]==1)or(sig_s[i]==0 and y_oo[i]==-1)
    if ok: c+=1
    else:
        if c>0: ws.append(c)
        c=0
if c>0: ws.append(c)
print(f'  Streaks: {len(ws)} Max: {max(ws) if ws else 0} Mean: {np.mean(ws):.1f}' if ws else '  None')

# 13. PER-THRESHOLD WR SWEEP
print(f'\n[13] THRESHOLD WR SWEEP')
for thl,ths,thn in [(.20,.20,.60),(.25,.25,.55),(.30,.30,.50),(.35,.36,.47),(.40,.40,.40),(.45,.45,.35),(.50,.50,.30)]:
    s=np.full(len(oo),1,dtype=int)
    s[(pL>thl)&(pL>pS)&(pN<thn)]=2; s[(pS>ths)&(pS>pL)&(pN<thn)]=0
    sf=s.copy(); sf[(s==2)&(stoch<0)]=1; sf[(s==0)&(stoch>0)]=1
    ss=np.full(len(sf),1,dtype=int)
    for i in range(2,len(sf)):
        w=sf[i-2:i+1]
        if len(set(w))==1 and w[0]!=1: ss[i]=w[0]
    hs=ss!=1
    if hs.sum()>0:
        wr=(ss[hs]==y_oo_3[hs]).mean()*100
        t=hs.sum()
    else: wr=0; t=0
    print(f'  THL={thl:.2f} THS={ths:.2f} THN={thn:.2f}: WR={wr:.1f}% T={t:,}')
y_oo_3=(y_oo+1).astype(int)

# Save
with open(os.path.join(PROD,'atomic_analysis.json'),'w') as f: json.dump(R,f,indent=2,default=str)
print(f'\n✅ Saved atomic_analysis.json')
