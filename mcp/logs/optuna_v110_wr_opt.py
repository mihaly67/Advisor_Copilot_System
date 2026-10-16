#!/usr/bin/env python3
"""Optuna V1.10 Jules CFD - WR-optimized tuner (300 trials)"""
import pandas as pd, numpy as np, joblib, optuna, warnings, os, json, time
warnings.filterwarnings('ignore')

PROD='/data/dev/projects/z-ai-copilot/models/production_v110_jules'
PROC='/data/dev/projects/z-ai-copilot/Master_csv/processed'

m=joblib.load(os.path.join(PROD,'lgbm_v110_jules.pkl'))
feat=open(os.path.join(PROD,'features.txt')).read().strip().split('\n')
df=pd.read_csv(os.path.join(PROC,'jules_v110_labeled.csv'))
df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
df.sort_values('End_Timestamp',inplace=True); df.reset_index(drop=True,inplace=True)
si=int(len(df)*0.8); oo=df.iloc[si:].copy().reset_index(drop=True)
X_oo=oo[feat].fillna(0).replace([np.inf,-np.inf],0)
y_oo=oo['Target_Label'].values
pr=m.predict_proba(X_oo); cl=m.classes_
i_s=list(cl).index(0); i_n=list(cl).index(1); i_l=list(cl).index(2)
pL=pr[:,i_l]; pS=pr[:,i_s]; pN=pr[:,i_n]
stoch=oo['Stoch_State_M1'].values
y3=(y_oo+1).astype(int)

def apply_filters(pL,pS,pN,stoch,thl,ths,thn,slk,ssk,sdz,sw):
    sig=np.full(len(pL),1,dtype=int)
    sig[(pL>thl)&(pL>pS)&(pN<thn)]=2
    sig[(pS>ths)&(pS>pL)&(pN<thn)]=0
    if sdz>0:
        outside_dz=np.abs(stoch)>=sdz
        sig_f=sig.copy()
        sig_f[(sig==2)&(stoch<slk)&outside_dz]=1
        sig_f[(sig==0)&(stoch>ssk)&outside_dz]=1
    else:
        sig_f=sig.copy()
        sig_f[(sig==2)&(stoch<slk)]=1
        sig_f[(sig==0)&(stoch>ssk)]=1
    if sw>=2:
        sig_s=np.full(len(sig_f),1,dtype=int)
        for i in range(sw-1,len(sig_f)):
            w=sig_f[i-sw+1:i+1]
            if len(set(w))==1 and w[0]!=1: sig_s[i]=w[0]
    else:
        sig_s=sig_f
    return sig_s

def eval_sig(sig,y3):
    has=sig!=1; t=has.sum()
    if t==0: return {'wr':0,'profit':0,'trades':0,'n_long':0,'n_short':0,'wr_l':0,'wr_s':0}
    correct=(sig[has]==y3[has])
    wins=correct.sum(); losses=t-wins
    wr=wins/t*100; profit=wins*1.5-losses*1.0
    nl=(sig==2).sum(); ns=(sig==0).sum()
    lm=sig==2; sm=sig==0
    wr_l=(y3[lm]==2).mean()*100 if lm.sum()>0 else 0
    wr_s=(y3[sm]==0).mean()*100 if sm.sum()>0 else 0
    return {'wr':round(wr,1),'profit':round(profit,1),'trades':t,'n_long':nl,'n_short':ns,'wr_l':round(wr_l,1),'wr_s':round(wr_s,1)}

# Strategy 1: Pure WR optimization (min 200 trades)
def obj_wr(trial):
    thl=trial.suggest_float('THL',0.25,0.60)
    ths=trial.suggest_float('THS',0.25,0.60)
    thn=trial.suggest_float('THN',0.25,0.65)
    slk=trial.suggest_float('slk',-0.3,0.0)
    ssk=trial.suggest_float('ssk',0.0,0.3)
    sdz=trial.suggest_float('sdz',0.0,0.4)
    sw=trial.suggest_int('sw',0,5)
    sig=apply_filters(pL,pS,pN,stoch,thl,ths,thn,slk,ssk,sdz,sw)
    r=eval_sig(sig,y3)
    if r['trades']<200: return 0
    if r['n_short']<50: return r['wr']-10
    return r['wr']

study_wr=optuna.create_study(direction='maximize',study_name='v110_wr_opt')
t0=time.time()
study_wr.optimize(obj_wr,n_trials=300,show_progress_bar=True)
elapsed=time.time()-t0

best_wr=study_wr.best_params
sig_wr=apply_filters(pL,pS,pN,stoch,best_wr['THL'],best_wr['THS'],best_wr['THN'],
    best_wr['slk'],best_wr['ssk'],best_wr['sdz'],best_wr['sw'])
r_wr=eval_sig(sig_wr,y3)

print(f'\n{"="*70}')
print(f'WR-OPTIMIZED RESULTS (300 trials, {elapsed:.0f}s)')
print(f'{"="*70}')
print(f'Best params:')
for k,v in best_wr.items():
    if isinstance(v,float): print(f'  {k}: {v:.4f}')
    else: print(f'  {k}: {v}')
print(f'\nWR={r_wr["wr"]:.1f}% Profit={r_wr["profit"]:.1f} Trades={r_wr["trades"]:,}')
print(f'Long={r_wr["n_long"]:,} (WR={r_wr["wr_l"]:.1f}%) Short={r_wr["n_short"]:,} (WR={r_wr["wr_s"]:.1f}%)')

print(f'\nKonfuzios matrix:')
print('           PredShort  PredNoise  PredLong')
for al,an in [(0,'Short'),(1,'Noise'),(2,'Long')]:
    row=[f'{((y3==al)&(sig_wr==pl)).sum():8,}' for pl in [0,1,2]]
    print(f'  Act{an:5s} {" ".join(row)}')

# Also: balanced WR (Long WR + Short WR)/2 with min trades
def obj_bal(trial):
    thl=trial.suggest_float('THL',0.25,0.60)
    ths=trial.suggest_float('THS',0.25,0.60)
    thn=trial.suggest_float('THN',0.25,0.65)
    slk=trial.suggest_float('slk',-0.3,0.0)
    ssk=trial.suggest_float('ssk',0.0,0.3)
    sdz=trial.suggest_float('sdz',0.0,0.4)
    sw=trial.suggest_int('sw',0,5)
    sig=apply_filters(pL,pS,pN,stoch,thl,ths,thn,slk,ssk,sdz,sw)
    r=eval_sig(sig,y3)
    if r['trades']<200: return 0
    if r['n_short']<50 or r['n_long']<50: return 0
    # Balance penalty: penalize if Long/Short ratio far from 1
    ratio=max(r['n_long'],r['n_short'])/max(min(r['n_long'],r['n_short']),1)
    bal_penalty=max(0,ratio-2)*5
    return (r['wr_l']+r['wr_s'])/2 - bal_penalty

study_bal=optuna.create_study(direction='maximize',study_name='v110_balanced')
t0=time.time()
study_bal.optimize(obj_bal,n_trials=300,show_progress_bar=True)
elapsed=time.time()-t0

best_bal=study_bal.best_params
sig_bal=apply_filters(pL,pS,pN,stoch,best_bal['THL'],best_bal['THS'],best_bal['THN'],
    best_bal['slk'],best_bal['ssk'],best_bal['sdz'],best_bal['sw'])
r_bal=eval_sig(sig_bal,y3)

print(f'\n{"="*70}')
print(f'BALANCED WR RESULTS (300 trials, {elapsed:.0f}s)')
print(f'{"="*70}')
print(f'Best params:')
for k,v in best_bal.items():
    if isinstance(v,float): print(f'  {k}: {v:.4f}')
    else: print(f'  {k}: {v}')
print(f'\nWR={r_bal["wr"]:.1f}% Profit={r_bal["profit"]:.1f} Trades={r_bal["trades"]:,}')
print(f'Long={r_bal["n_long"]:,} (WR={r_bal["wr_l"]:.1f}%) Short={r_bal["n_short"]:,} (WR={r_bal["wr_s"]:.1f}%)')
ls_ratio=r_bal['n_long']/max(r_bal['n_short'],1)
print(f'L/S ratio: {ls_ratio:.2f}')

print(f'\nKonfuzios matrix:')
print('           PredShort  PredNoise  PredLong')
for al,an in [(0,'Short'),(1,'Noise'),(2,'Long')]:
    row=[f'{((y3==al)&(sig_bal==pl)).sum():8,}' for pl in [0,1,2]]
    print(f'  Act{an:5s} {" ".join(row)}')

# Summary table
print(f'\n{"="*70}')
print(f'SUMMARY')
print(f'{"="*70}')
print(f'{"Config":<20} {"WR":>6} {"Trades":>8} {"Long":>6} {"L_WR":>6} {"Short":>6} {"S_WR":>6} {"Profit":>8}')
print(f'{"-"*70}')
# Original
sig_o=apply_filters(pL,pS,pN,stoch,0.35,0.36,0.47,0.0,0.0,0.0,3)
r_o=eval_sig(sig_o,y3)
print(f'{"Original":<20} {r_o["wr"]:>5.1f}% {r_o["trades"]:>8,} {r_o["n_long"]:>6,} {r_o["wr_l"]:>5.1f}% {r_o["n_short"]:>6,} {r_o["wr_s"]:>5.1f}% {r_o["profit"]:>8.1f}')
# Profit opt
sig_p=apply_filters(pL,pS,pN,stoch,0.3547,0.3415,0.5243,-0.0448,0.1933,0.2937,0)
r_p=eval_sig(sig_p,y3)
print(f'{"Profit-opt":<20} {r_p["wr"]:>5.1f}% {r_p["trades"]:>8,} {r_p["n_long"]:>6,} {r_p["wr_l"]:>5.1f}% {r_p["n_short"]:>6,} {r_p["wr_s"]:>5.1f}% {r_p["profit"]:>8.1f}')
print(f'{"WR-opt":<20} {r_wr["wr"]:>5.1f}% {r_wr["trades"]:>8,} {r_wr["n_long"]:>6,} {r_wr["wr_l"]:>5.1f}% {r_wr["n_short"]:>6,} {r_wr["wr_s"]:>5.1f}% {r_wr["profit"]:>8.1f}')
print(f'{"Balanced":<20} {r_bal["wr"]:>5.1f}% {r_bal["trades"]:>8,} {r_bal["n_long"]:>6,} {r_bal["wr_l"]:>5.1f}% {r_bal["n_short"]:>6,} {r_bal["wr_s"]:>5.1f}% {r_bal["profit"]:>8.1f}')

result={'wr_opt':best_wr,'wr_result':r_wr,'bal_opt':best_bal,'bal_result':r_bal}
with open(os.path.join(PROD,'optuna_results_v3.json'),'w') as f:
    json.dump(result,f,indent=2,default=str)
print(f'\nSaved: {PROD}/optuna_results_v3.json')
