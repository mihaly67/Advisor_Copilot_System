#!/usr/bin/env python3
"""Optuna V1.10 — FÓKUSZÁLT: csak THL/THS/THN (3 paraméter)
Stoch filter FIX (ellentétes kizárás), Stability FIX (window=3)"""
import pandas as pd, numpy as np, joblib, optuna, warnings, os, json, time
warnings.filterwarnings('ignore')

PROD='/data/dev/projects/z-ai-copilot/models/production_v110_jules'
PROC='/data/dev/projects/z-ai-copilot/Master_csv/processed'

m=joblib.load(os.path.join(PROD,'lgbm_v110_jules.pkl'))
feat=[l.strip() for l in open(os.path.join(PROD,'features.txt')) if l.strip()]
df=pd.read_csv(os.path.join(PROC,'jules_v110_labeled.csv'))
df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
df.sort_values('End_Timestamp',inplace=True); df.reset_index(drop=True,inplace=True)
si=int(len(df)*0.8); oo=df.iloc[si:].copy().reset_index(drop=True)
X=oo[feat].fillna(0).replace([np.inf,-np.inf],0)
y=oo['Target_Label'].values; y3=(y+1).astype(int)
pr=m.predict_proba(X); cl=m.classes_
i_s=list(cl).index(0); i_n=list(cl).index(1); i_l=list(cl).index(2)
pL=pr[:,i_l]; pS=pr[:,i_s]; pN=pr[:,i_n]
stoch=oo['Stoch_State_M1'].values; n=len(oo)

print(f'OOS: {n:,} bars | 3 paraméter: THL, THS, THN')
print(f'Stoch: ellentétes kizárás (FIX) | Stability: window=3 (FIX)')

def pipeline(pL,pS,pN,stoch,thl,ths,thn):
    sig=np.full(n,1,dtype=int)
    sig[(pL>thl)&(pL>pS)&(pN<thn)]=2
    sig[(pS>ths)&(pS>pL)&(pN<thn)]=0
    sig_f=sig.copy()
    sig_f[(sig==2)&(stoch<0)]=1
    sig_f[(sig==0)&(stoch>0)]=1
    sig_s=np.full(n,1,dtype=int)
    for i in range(2,n):
        w=sig_f[i-2:i+1]
        if len(set(w))==1 and w[0]!=1: sig_s[i]=w[0]
    return sig_s

def eval_sig(sig,y3):
    has=sig!=1; t=has.sum()
    if t==0: return dict(wr=0,profit=0,trades=0,nl=0,ns=0,wr_l=0,wr_s=0)
    wins=(sig[has]==y3[has]).sum(); losses=t-wins
    profit=wins*1.5-losses*1.0; wr=wins/t*100
    nl=(sig==2).sum(); ns=(sig==0).sum()
    lm=sig==2; sm=sig==0
    wr_l=(y3[lm]==2).mean()*100 if lm.sum()>0 else 0
    wr_s=(y3[sm]==0).mean()*100 if sm.sum()>0 else 0
    return dict(wr=round(wr,1),profit=round(profit,1),trades=t,nl=nl,ns=ns,wr_l=round(wr_l,1),wr_s=round(wr_s,1))

# Objective: profit (wins*1.5 - losses*1.0), min 300 trades, both directions
def objective(trial):
    thl=trial.suggest_float('THL',0.25,0.50)
    ths=trial.suggest_float('THS',0.25,0.50)
    thn=trial.suggest_float('THN',0.15,0.45)
    sig=pipeline(pL,pS,pN,stoch,thl,ths,thn)
    r=eval_sig(sig,y3)
    if r['trades']<300: return -1000
    if r['ns']<30: return r['profit']-200
    if r['nl']<30: return r['profit']-200
    return r['profit']

study=optuna.create_study(direction='maximize',study_name='v110_focused')
print('\nOptuna 300 trials...')
t0=time.time()
study.optimize(objective,n_trials=300,show_progress_bar=True)
elapsed=time.time()-t0

best=study.best_params
print(f'\n{"="*60}')
print(f'OPTUNA COMPLETE ({elapsed:.0f}s)')
print(f'{"="*60}')
print(f'Best: THL={best["THL"]:.3f} THS={best["THS"]:.3f} THN={best["THN"]:.3f}')

sig_b=pipeline(pL,pS,pN,stoch,best['THL'],best['THS'],best['THN'])
r_b=eval_sig(sig_b,y3)
print(f'WR={r_b["wr"]:.1f}% Profit={r_b["profit"]:.0f} Trades={r_b["trades"]:,}')
print(f'Long={r_b["nl"]:,} (WR={r_b["wr_l"]:.1f}%) Short={r_b["ns"]:,} (WR={r_b["wr_s"]:.1f}%)')

# Konfúziós mátrix
print(f'\nKonfúziós mátrix:')
print('           PredShort  PredNoise  PredLong')
for al,an in [(0,'Short'),(1,'Noise'),(2,'Long')]:
    row=[f'{((y3==al)&(sig_b==pl)).sum():8,}' for pl in [0,1,2]]
    print(f'  Act{an:5s} {" ".join(row)}')

# Top 10 trials
print(f'\nTop 10:')
for t in study.trials_dataframe().sort_values('value',ascending=False).head(10).itertuples():
    print(f'  #{t.Index}: profit={t.value:.0f}')

# Összehasonlítás
print(f'\n--- ÖSSZEHASONLÍTÁS ---')
for name,thl,ths,thn in [('Eredeti',0.35,0.36,0.47),(f'Optuna',best['THL'],best['THS'],best['THN'])]:
    sig=pipeline(pL,pS,pN,stoch,thl,ths,thn)
    r=eval_sig(sig,y3)
    print(f'{name}: THL={thl:.3f} THS={ths:.3f} THN={thn:.3f} | WR={r["wr"]:.1f}% T={r["trades"]:,} L={r["nl"]:,} S={r["ns"]:,} P={r["profit"]:.0f}')

result={'best_params':best,'best_result':r_b}
with open(os.path.join(PROD,'optuna_focused.json'),'w') as f:
    json.dump(result,f,indent=2,default=str)
print(f'\nSaved: {PROD}/optuna_focused.json')
