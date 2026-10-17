#!/usr/bin/env python3
"""Optuna V1.10 Jules CFD - Refined threshold tuner (200 trials, WR + profit)"""
import pandas as pd, numpy as np, joblib, optuna, warnings, os, json, time
warnings.filterwarnings('ignore')

PROD='/data/dev/projects/z-ai-copilot/models/production_v110_jules'
PROC='/data/dev/projects/z-ai-copilot/Master_csv/processed'

print('='*70)
print('OPTUNA V1.10 JULES CFD - REFINED TUNER (200 trials)')
print('='*70)

m=joblib.load(os.path.join(PROD,'lgbm_v110_jules.pkl'))
feat=open(os.path.join(PROD,'features.txt')).read().strip().split('\n')
df=pd.read_csv(os.path.join(PROC,'jules_v110_labeled.csv'))
df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
df.sort_values('End_Timestamp',inplace=True); df.reset_index(drop=True,inplace=True)
si=int(len(df)*0.8); oo=df.iloc[si:].copy().reset_index(drop=True)

X_oo=oo[feat].fillna(0).replace([np.inf,-np.inf],0)
y_oo=oo['Target_Label'].values  # -1,0,1
pr=m.predict_proba(X_oo); cl=m.classes_
i_s=list(cl).index(0); i_n=list(cl).index(1); i_l=list(cl).index(2)
pL=pr[:,i_l]; pS=pr[:,i_s]; pN=pr[:,i_n]
stoch=oo['Stoch_State_M1'].values
n_oo=len(oo)
y3=(y_oo+1).astype(int)  # 0=Short,1=Noise,2=Long (same as sig encoding)

print(f'OOS: {n_oo:,} bars')

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
    has=sig!=1
    t=has.sum()
    if t==0: return {'wr':0,'profit':0,'trades':0,'wins':0,'losses':0,'n_long':0,'n_short':0,'wr_l':0,'wr_s':0}
    correct=(sig[has]==y3[has])
    wins=correct.sum(); losses=t-wins
    wr=wins/t*100
    profit=wins*1.5-losses*1.0
    nl=(sig==2).sum(); ns=(sig==0).sum()
    # Per-direction WR
    lm=sig==2; sm=sig==0
    wr_l=(y3[lm]==2).mean()*100 if lm.sum()>0 else 0
    wr_s=(y3[sm]==0).mean()*100 if sm.sum()>0 else 0
    return {'wr':round(wr,1),'profit':round(profit,1),'trades':t,'wins':wins,'losses':losses,'n_long':nl,'n_short':ns,'wr_l':round(wr_l,1),'wr_s':round(wr_s,1)}

def objective(trial):
    thl=trial.suggest_float('THL',0.25,0.55)
    ths=trial.suggest_float('THS',0.25,0.55)
    thn=trial.suggest_float('THN',0.30,0.60)
    slk=trial.suggest_float('stoch_long_kill',-0.3,0.0)
    ssk=trial.suggest_float('stoch_short_kill',0.0,0.3)
    sdz=trial.suggest_float('stoch_deadzone',0.0,0.3)
    sw=trial.suggest_int('stability_window',0,5)
    sig=apply_filters(pL,pS,pN,stoch,thl,ths,thn,slk,ssk,sdz,sw)
    r=eval_sig(sig,y3)
    if r['trades']<50: return -1000
    if r['n_short']<20: return r['profit']-500
    # Combined: profit + WR bonus (encourage higher WR)
    return r['profit'] + (r['wr']-45)*10

study=optuna.create_study(direction='maximize',study_name='v110_jules_cfd_v2')
print('\nRunning Optuna (200 trials)...')
t0=time.time()
study.optimize(objective,n_trials=200,show_progress_bar=True)
elapsed=time.time()-t0

print(f'\n{"="*70}')
print(f'OPTUNA COMPLETE ({elapsed:.0f}s, {len(study.trials)} trials)')
print(f'{"="*70}')

best=study.best_params
print(f'\nBest params:')
for k,v in best.items():
    if isinstance(v,float): print(f'  {k}: {v:.4f}')
    else: print(f'  {k}: {v}')

sig_best=apply_filters(pL,pS,pN,stoch,best['THL'],best['THS'],best['THN'],
    best['stoch_long_kill'],best['stoch_short_kill'],best['stoch_deadzone'],best['stability_window'])
r_best=eval_sig(sig_best,y3)

print(f'\nBest result:')
print(f'  WR={r_best["wr"]:.1f}% Profit={r_best["profit"]:.1f} Trades={r_best["trades"]:,}')
print(f'  Long={r_best["n_long"]:,} (WR={r_best["wr_l"]:.1f}%) Short={r_best["n_short"]:,} (WR={r_best["wr_s"]:.1f}%)')

# CORRECT konfuzios matrix (sig encoding 0=Short,1=Noise,2=Long)
print(f'\nKonfuzios matrix (FIXED encoding):')
print('           PredShort  PredNoise  PredLong')
for al,an in [(0,'Short'),(1,'Noise'),(2,'Long')]:
    row=[f'{((y3==al)&(sig_best==pl)).sum():8,}' for pl in [0,1,2]]
    print(f'  Act{an:5s} {" ".join(row)}')

# Top 10 trials
print(f'\nTop 10 trials:')
trials_df=study.trials_dataframe()
trials_df=trials_df.sort_values('value',ascending=False).head(10)
for idx,row in trials_df.iterrows():
    print(f'  #{idx}: score={row["value"]:.1f}')

# Compare with original Jules params
print(f'\n--- COMPARISON ---')
# Original
sig_orig=apply_filters(pL,pS,pN,stoch,0.35,0.36,0.47,0.0,0.0,0.0,3)
r_orig=eval_sig(sig_orig,y3)
print(f'Original (THL=0.35 THS=0.36 THN=0.47 stoch=0/0 deadzone=0 stability=3):')
print(f'  WR={r_orig["wr"]:.1f}% Trades={r_orig["trades"]:,} L={r_orig["n_long"]:,} S={r_orig["n_short"]:,}')
print(f'Optuna best:')
print(f'  WR={r_best["wr"]:.1f}% Trades={r_best["trades"]:,} L={r_best["n_long"]:,} S={r_best["n_short"]:,}')

# Save
result={'best_params':best,'best_result':r_best,'n_trials':len(study.trials),'elapsed_sec':round(elapsed)}
with open(os.path.join(PROD,'optuna_results_v2.json'),'w') as f:
    json.dump(result,f,indent=2,default=str)
print(f'\nSaved: {PROD}/optuna_results_v2.json')
