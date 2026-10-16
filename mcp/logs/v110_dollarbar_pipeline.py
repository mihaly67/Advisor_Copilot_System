#!/usr/bin/env python3
"""v110_dollarbar_pipeline.py - Dollar bar pipeline CFD-n (prado_dollar_bars.py logika)"""
import pandas as pd, numpy as np, lightgbm as lgb, joblib, os, sys, json, time, warnings
from sklearn.metrics import confusion_matrix
warnings.filterwarnings('ignore')
sys.path.insert(0, '/data/dev/projects/z-ai-copilot/src')
from prado_dollar_bars import create_dollar_bars
from v110_volbar_pipeline import compute_features, apply_triple_barrier, apply_stability, eval_detailed

BASE='/data/dev/projects/z-ai-copilot'
RAW=os.path.join(BASE,'Master_csv','raw','új')
MOD=os.path.join(BASE,'models','v110_dollarbar'); DOCS=os.path.join(BASE,'docs','v110_dollarbar')
for d in [MOD,DOCS]: os.makedirs(d,exist_ok=True)
RAW_TANITO=os.path.join(RAW,'Scalper_Copilot_MTF_Data_v2.csv')
RAW_VIZSGA=os.path.join(RAW,'Scalper_Copilot_MTF_Data_külön_vizsga.csv')

FEAT_10=['Tick_Speed','Dist_Micro_R','Dist_Micro_S','Dist_Sec_R','Dist_Sec_S',
    'Dist_Ter_R','Dist_Ter_S','Stoch_State_M1','Upper_Wick_ATR','Lower_Wick_ATR']
FEAT_18=FEAT_10+['RSI_signed','MACD_Hist_ATR','BB_ZScore','ROC_5','MFI_signed',
    'OBI_ZScore','Price_Vel_ATR','RSI_M15_signed']

def jules_threshold(probs, classes):
    i_s=list(classes).index(0); i_n=list(classes).index(1); i_l=list(classes).index(2)
    ps=probs[:,i_s]; pn=probs[:,i_n]; pl=probs[:,i_l]
    sig=np.full(len(probs),1,dtype=int)
    sig[(pl>0.350)&(pl>ps)&(pn<0.470)]=2
    sig[(ps>0.360)&(ps>pl)&(pn<0.470)]=0
    return sig,ps,pn,pl

def main():
    t0=time.time()
    print('Loading train...')
    df_tr=pd.read_csv(RAW_TANITO)
    df_tr['Timestamp']=pd.to_datetime(df_tr['Timestamp'],format='%Y.%m.%d %H:%M:%S.%f')
    print(f'  {len(df_tr):,} ticks')
    print('Loading vizsga...')
    df_vz=pd.read_csv(RAW_VIZSGA)
    df_vz['Timestamp']=pd.to_datetime(df_vz['Timestamp'],format='%Y.%m.%d %H:%M:%S.%f')
    print(f'  {len(df_vz):,} ticks')

    params={'n_estimators':781,'learning_rate':0.0142,'num_leaves':57,'max_depth':6,
        'min_child_samples':24,'colsample_bytree':0.566,'class_weight':'balanced',
        'objective':'multiclass','random_state':42,'n_jobs':-1,'verbose':-1}

    results=[]
    configs = [
        (444000, True,  10, 5, '$444K-adapt-10f-MB5'),
        (444000, True,  18, 5, '$444K-adapt-18f-MB5'),
        (444000, True,  10, 8, '$444K-adapt-10f-MB8'),
        (444000, True,  18, 8, '$444K-adapt-18f-MB8'),
        (444000, False, 10, 5, '$444K-fix-10f-MB5'),
        (444000, False, 18, 5, '$444K-fix-18f-MB5'),
        (300000, True,  10, 5, '$300K-adapt-10f-MB5'),
        (600000, True,  10, 5, '$600K-adapt-10f-MB5'),
    ]
    for thresh, adaptive, nf, mb, lbl in configs:
        t1=time.time()
        print(f'\n=== {lbl} ===')
        bars_tr = create_dollar_bars(None, threshold=thresh, adaptive=adaptive, df_input=df_tr)
        bars_vz = create_dollar_bars(None, threshold=thresh, adaptive=adaptive, df_input=df_vz)
        for b in [bars_tr, bars_vz]:
            if 'Num_Ticks' in b.columns and 'N_ticks' not in b.columns: b['N_ticks']=b['Num_Ticks']
        df_train, avail = compute_features(bars_tr, df_tr)
        df_train = apply_triple_barrier(df_train, pt=1.5, sl=1.0, max_bars=mb)
        df_train = df_train.iloc[:-mb].reset_index(drop=True)
        df_viz, _ = compute_features(bars_vz, df_vz)
        df_viz = apply_triple_barrier(df_viz, pt=1.5, sl=1.0, max_bars=mb)
        df_viz = df_viz.iloc[:-mb].reset_index(drop=True)
        si = int(len(df_train)*0.8)
        y_all = (df_train['Target_Label']+1).astype(int).values
        y_tr=y_all[:si]; y_oo=y_all[si:]
        feats = FEAT_18[:nf] if nf<=18 else FEAT_18
        feats = [f for f in feats if f in avail]
        X_tr=df_train.iloc[:si][feats].values; X_oo=df_train.iloc[si:][feats].values
        if len(np.unique(y_tr))<3: continue
        clf=lgb.LGBMClassifier(**params)
        clf.fit(X_tr,y_tr,eval_set=[(X_oo,y_oo)])
        probs=clf.predict_proba(X_oo); cl=clf.classes_
        sig,ps,pn,pl=jules_threshold(probs,cl)
        sig_f=apply_stability(sig,3)
        r_oos=eval_detailed(sig_f,y_oo,ps,pn,pl)
        fb=[f for f in feats if f in df_viz.columns]
        X_viz=df_viz[fb].replace([np.inf,-np.inf],np.nan).fillna(0).values
        y_viz=(df_viz['Target_Label']+1).astype(int).values
        pv=clf.predict_proba(X_viz)
        sv,psv,pnv,plv=jules_threshold(pv,cl)
        svf=apply_stability(sv,3)
        r_viz=eval_detailed(svf,y_viz,psv,pnv,plv)
        gap=r_oos['wr']-r_viz['wr']
        results.append({'label':lbl,'oos':r_oos,'vizsga':r_viz,'gap':round(gap,1)})
        print(f'  OOS: WR={r_oos["wr"]}% P=${r_oos["profit"]} T={r_oos["trades"]}')
        print(f'  Viz: WR={r_viz["wr"]}% P=${r_viz["profit"]} T={r_viz["trades"]}')
        print(f'  Gap: {gap:+.1f}% [{time.time()-t1:.0f}s]')

    print('\n=== SUMMARY ===')
    for r in sorted(results, key=lambda x: x['oos']['wr'], reverse=True):
        o=r['oos']; v=r['vizsga']
        print(f'  {r["label"]:<30s} OOS={o["wr"]:5.1f}% ${o["profit"]:>5.0f} T={o["trades"]:>4d} | Viz={v["wr"]:5.1f}% ${v["profit"]:>5.0f} T={v["trades"]:>4d} | Gap={r["gap"]:+.1f}%')
    best=max(results, key=lambda x: x['oos']['wr'])
    print(f'\n  BEST: {best["label"]} OOS={best["oos"]["wr"]}% Viz={best["vizsga"]["wr"]}%')
    with open(os.path.join(DOCS,'dollarbar_results.json'),'w') as f: json.dump(results,f,indent=2,default=str)
    print(f'  Total: {time.time()-t0:.0f}s')

if __name__=='__main__': main()
