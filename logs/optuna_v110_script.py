#!/usr/bin/env python3
"""Optuna V1.10 Jules CFD - Threshold + Stoch + Stability hyperparameter tuner"""
import pandas as pd, numpy as np, joblib, optuna, warnings, os, json, time
warnings.filterwarnings('ignore')

PROD='/data/dev/projects/z-ai-copilot/models/production_v110_jules'
PROC='/data/dev/projects/z-ai-copilot/Master_csv/processed'

print('='*70)
print('OPTUNA V1.10 JULES CFD - THRESHOLD TUNER')
print('='*70)

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
n_oo=len(oo)

print(f'OOS: {n_oo:,} bars')
print(f'Labels: Long={(y_oo==1).sum():,} Noise={(y_oo==0).sum():,} Short={(y_oo==-1).sum():,}')

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

def eval_sig(sig,y,pt=1.5,sl=1.0):
    profit=0.0; wins=0; losses=0; nl=0; ns=0
    for i in range(len(sig)):
        if sig[i]==2:
            nl+=1
            if y[i]==1: profit+=pt; wins+=1
            else: profit-=sl; losses+=1
        elif sig[i]==0:
            ns+=1
            if y[i]==-1: profit+=pt; wins+=1
            else: profit-=sl; losses+=1
    t=wins+losses; wr=wins/t*100 if t>0 else 0
    return {'wr':round(wr,1),'profit':round(profit,1),'trades':t,'wins':wins,'losses':losses,'n_long':nl,'n_short':ns}

def objective(trial):
    thl=trial.suggest_float('THL',0.25,0.55)
    ths=trial.suggest_float('THS',0.25,0.55)
    thn=trial.suggest_float('THN',0.30,0.60)
    slk=trial.suggest_float('stoch_long_kill',-0.3,0.0)
    ssk=trial.suggest_float('stoch_short_kill',0.0,0.3)
    sdz=trial.suggest_float('stoch_deadzone',0.0,0.3)
    sw=trial.suggest_int('stability_window',0,5)
    sig=apply_filters(pL,pS,pN,stoch,thl,ths,thn,slk,ssk,sdz,sw)
    r=eval_sig(sig,y_oo)
    if r['trades']<50: return -1000
    if r['n_short']<10: return r['profit']-500
    return r['profit']

study=optuna.create_study(direction='maximize',study_name='v110_jules_cfd')
print('\nRunning Optuna (100 trials)...')
t0=time.time()
study.optimize(objective,n_trials=100,show_progress_bar=True)
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
r_best=eval_sig(sig_best,y_oo)

print(f'\nBest result:')
print(f'  WR={r_best["wr"]:.1f}% Profit={r_best["profit"]:.1f} Trades={r_best["trades"]:,}')
print(f'  Long={r_best["n_long"]:,} Short={r_best["n_short"]:,}')

print(f'\nKonfuzios matrix (best):')
print('           PredShort  PredNoise  PredLong')
for al,an in [(-1,'Short'),(0,'Noise'),(1,'Long')]:
    row=[f'{((y_oo==al)&(sig_best==pl)).sum():8,}' for pl in [-1,0,1]]
    print(f'  Act{an:5s} {" ".join(row)}')

# Top 5 trials
print(f'\nTop 5 trials:')
trials_df=study.trials_dataframe()
trials_df=trials_df.sort_values('value',ascending=False).head(5)
for idx,row in trials_df.iterrows():
    print(f'  #{idx}: profit={row["value"]:.1f}')

result={'best_params':best,'best_result':r_best,'n_trials':len(study.trials),'elapsed_sec':round(elapsed)}
with open(os.path.join(PROD,'optuna_results.json'),'w') as f:
    json.dump(result,f,indent=2,default=str)
print(f'\nSaved: {PROD}/optuna_results.json')
