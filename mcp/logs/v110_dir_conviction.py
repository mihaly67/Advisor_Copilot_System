#!/usr/bin/env python3
"""v110_dir_conviction.py - Dir_Conviction feature (P(L) - P(S)) implementálás

Felhasználó felismerés: Ha P(Long) > P(Short) de P(Noise) > mindkettő,
az irány MINDIG ÉRVÉNYES! A P(L)-P(S) relatív helyzet prediktív
függetlenül a noise szinttől.

Implementáció:
  1. Tréning model → predict_proba → P(L), P(S), P(N)
  2. Dir_Conviction = P(L) - P(S) mint ÚJ feature
  3. Dominance = |P(L) - P(S)| mint feature
  4. Retraining 19 feature-vel
  5. Vizsga eval (kalibrált threshold)
"""
import pandas as pd, numpy as np, lightgbm as lgb, joblib, os, sys, json, time, warnings
from sklearn.metrics import confusion_matrix
warnings.filterwarnings('ignore')

BASE='/data/dev/projects/z-ai-copilot'
PROC=os.path.join(BASE,'Master_csv','processed')
MOD=os.path.join(BASE,'models','v110_vizsga')
DOCS=os.path.join(BASE,'docs','v110_vizsga')
for d in [MOD,DOCS]: os.makedirs(d,exist_ok=True)

LGBM_PARAMS={'n_estimators':781,'learning_rate':0.0142,'num_leaves':57,
    'max_depth':6,'min_child_samples':24,'colsample_bytree':0.566,
    'class_weight':'balanced','objective':'multiclass',
    'random_state':42,'n_jobs':-1,'verbose':-1}
THL=0.390; THS=0.400; THN=0.400; SW=2

FEAT_ORIG=['Tick_Speed','Dist_Micro_R','Dist_Micro_S','Dist_Sec_R','Dist_Sec_S',
    'Dist_Ter_R','Dist_Ter_S','Stoch_State_M1','Upper_Wick_ATR','Lower_Wick_ATR']
FEAT_DIR=['RSI_signed','MACD_Hist_ATR','BB_ZScore','ROC_5','MFI_signed',
    'OBI_ZScore','Price_Vel_ATR','RSI_M15_signed']

sys.path.insert(0, os.path.join(BASE, 'src'))
from v110_vizsga_eval import (compute_dir_features, apply_threshold, apply_stability,
    eval_detailed, grid_fix, build_viz, build_dollar_bars, compute_vizsga_features,
    apply_triple_barrier)

def main():
    t0=time.time()
    print('='*70)
    print('  DIR_CONVICTION FEATURE STUDY')
    print('='*70)

    # Load main data
    print('\n[1] Adat betoltes...')
    df=pd.read_csv(os.path.join(PROC,'jules_v110_labeled.csv'))
    df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
    df['Start_Timestamp']=pd.to_datetime(df['Start_Timestamp'])
    df.sort_values('End_Timestamp',inplace=True); df.reset_index(drop=True,inplace=True)

    # Compute 18 features (same as leakfix)
    print('[2] 18 feature...')
    feat_orig=df[FEAT_ORIG].copy()
    feat_dir=compute_dir_features(df)
    feat_18=pd.concat([feat_orig,feat_dir],axis=1)
    feat_18=feat_18.replace([np.inf,-np.inf],np.nan).fillna(0)

    si=int(len(df)*0.8)
    y_all=(df['Target_Label']+1).astype(int).values
    y_tr=y_all[:si]; y_oo=y_all[si:]
    X_tr_18=feat_18.iloc[:si].values; X_oo_18=feat_18.iloc[si:].values

    # Step 1: Train 18feat model, get probabilities
    print('[3] 18feat model training...')
    clf_18=lgb.LGBMClassifier(**LGBM_PARAMS)
    clf_18.fit(X_tr_18,y_tr,eval_set=[(X_oo_18,y_oo)])

    # Get probabilities for train and OOS
    probs_tr=clf_18.predict_proba(X_tr_18); cl=clf_18.classes_
    probs_oo=clf_18.predict_proba(X_oo_18)
    i_s=list(cl).index(0); i_l=list(cl).index(2)
    p_l_tr=probs_tr[:,i_l]; p_s_tr=probs_tr[:,i_s]
    p_l_oo=probs_oo[:,i_l]; p_s_oo=probs_oo[:,i_s]

    # Dir_Conviction = P(L) - P(S)
    dir_conv_tr = p_l_tr - p_s_tr
    dir_conv_oo = p_l_oo - p_s_oo
    # Dominance = |P(L) - P(S)|
    dominance_tr = np.abs(dir_conv_tr)
    dominance_oo = np.abs(dir_conv_oo)

    print(f'  Dir_Conviction stats (train): mean={dir_conv_tr.mean():.4f} std={dir_conv_tr.std():.4f}')
    print(f'  Dir_Conviction stats (OOS):   mean={dir_conv_oo.mean():.4f} std={dir_conv_oo.std():.4f}')

    # Step 2: Add Dir_Conviction as feature → 19 feat
    FEAT_19 = FEAT_ORIG + FEAT_DIR + ['Dir_Conviction', 'Dominance']
    feat_19 = feat_18.copy()
    feat_19['Dir_Conviction'] = 0.0  # placeholder
    feat_19['Dominance'] = 0.0
    feat_19.iloc[:si, feat_19.columns.get_loc('Dir_Conviction')] = dir_conv_tr
    feat_19.iloc[si:, feat_19.columns.get_loc('Dir_Conviction')] = dir_conv_oo
    feat_19.iloc[:si, feat_19.columns.get_loc('Dominance')] = dominance_tr
    feat_19.iloc[si:, feat_19.columns.get_loc('Dominance')] = dominance_oo

    X_tr_19=feat_19.iloc[:si][FEAT_19].values
    X_oo_19=feat_19.iloc[si:][FEAT_19].values

    print('\n[4] 20feat model training (18 + Dir_Conviction + Dominance)...')
    clf_19=lgb.LGBMClassifier(**LGBM_PARAMS)
    clf_19.fit(X_tr_19,y_tr,eval_set=[(X_oo_19,y_oo)])
    fi=clf_19.feature_importances_
    top10=[(FEAT_19[i],round(fi[i]/fi.sum()*100,2)) for i in np.argsort(fi)[::-1][:10]]
    print('  Feature importance top 10:')
    for i,(n,v) in enumerate(top10):
        tag=' <-- CONVICTION' if n in ['Dir_Conviction','Dominance'] else (' <-- NEW' if n in FEAT_DIR else '')
        print(f'    {i+1:2d}. {n:<20s} {v:.2f}%{tag}')

    # Step 3: Evaluate both models on OOS
    print('\n[5] OOS ertekeles...')
    for name, clf, X_oo in [('18feat', clf_18, X_oo_18), ('20feat', clf_19, X_oo_19)]:
        probs=clf.predict_proba(X_oo); c=clf.classes_
        sig_t,ps,pn,pl=apply_threshold(probs,c)
        sig_f=apply_stability(sig_t)
        r=eval_detailed(sig_f,y_oo,ps,pn,pl)
        print(f'  {name}: WR={r["wr"]}% P=${r["profit"]} T={r["trades"]} Opp={r["opposite"]} ({r["swap_pct"]}%)')

    # Step 4: Vizsga eval (calibrated threshold)
    print('\n[6] Vizsga eval (calibrated threshold)...')
    RAW=os.path.join(BASE,'Master_csv','raw')
    vizsga_csv=os.path.join(RAW,'Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv')
    if not os.path.exists(vizsga_csv):
        vizsga_csv='/data/dev/projects/scalper-copilot/Master_csv/raw/Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv'
    df_viz_tick=pd.read_csv(vizsga_csv)
    df_viz_tick['Timestamp']=pd.to_datetime(df_viz_tick['Timestamp'],format='%Y.%m.%d %H:%M:%S.%f')
    
    zz_csv=os.path.join(RAW,'Master_ZigZag_GCEQ26_M1.csv')
    if not os.path.exists(zz_csv):
        zz_csv='/data/dev/projects/scalper-copilot/Master_csv/raw/Master_ZigZag_GCEQ26_M1.csv'
    df_zz=pd.read_csv(zz_csv)
    df_zz['Time']=pd.to_datetime(df_zz['Time'],format='%Y.%m.%d %H:%M:%S')
    viz_start=df_viz_tick['Timestamp'].min()-pd.Timedelta(hours=1)
    viz_end=df_viz_tick['Timestamp'].max()+pd.Timedelta(hours=1)
    df_zz_viz=df_zz[(df_zz['Time']>=viz_start)&(df_zz['Time']<=viz_end)].copy().reset_index(drop=True)

    # Calibrate threshold
    mid=(df_viz_tick['Bid']+df_viz_tick['Ask'])/2
    total_vol=df_viz_tick['Bid_Volume']+df_viz_tick['Ask_Volume']
    dollar_per_sec=(mid*total_vol).mean()
    thresh_viz=dollar_per_sec*45  # 45 sec target
    print(f'  Vizsga threshold: ${thresh_viz:,.0f}')

    db_viz=build_dollar_bars(df_viz_tick,threshold=thresh_viz)
    df_viz_feat=compute_vizsga_features(db_viz,df_zz_viz)
    df_viz_lab=apply_triple_barrier(df_viz_feat)
    df_viz_lab=df_viz_lab.iloc[:-5].reset_index(drop=True)

    X_viz_18=df_viz_lab[FEAT_ORIG+FEAT_DIR].replace([np.inf,-np.inf],np.nan).fillna(0).values
    y_viz=(df_viz_lab['Target_Label']+1).astype(int).values

    # 18feat vizsga
    probs_viz_18=clf_18.predict_proba(X_viz_18)
    sig_t,ps,pn,pl=apply_threshold(probs_viz_18,clf_18.classes_)
    sig_f=apply_stability(sig_t)
    r_viz_18=eval_detailed(sig_f,y_viz,ps,pn,pl)
    print(f'  18feat vizsga: WR={r_viz_18["wr"]}% P=${r_viz_18["profit"]} T={r_viz_18["trades"]}')

    # 20feat vizsga: need Dir_Conviction from 18feat model first
    i_s_v=list(clf_18.classes_).index(0); i_l_v=list(clf_18.classes_).index(2)
    dir_conv_viz = probs_viz_18[:,i_l_v] - probs_viz_18[:,i_s_v]
    dominance_viz = np.abs(dir_conv_viz)
    
    X_viz_20 = np.column_stack([X_viz_18, dir_conv_viz, dominance_viz])
    probs_viz_20=clf_19.predict_proba(X_viz_20)
    sig_t,ps,pn,pl=apply_threshold(probs_viz_20,clf_19.classes_)
    sig_f=apply_stability(sig_t)
    r_viz_20=eval_detailed(sig_f,y_viz,ps,pn,pl)
    print(f'  20feat vizsga: WR={r_viz_20["wr"]}% P=${r_viz_20["profit"]} T={r_viz_20["trades"]}')

    # Save
    joblib.dump(clf_19,os.path.join(MOD,'lgbm_20feat_conviction.pkl'))
    print(f'\n  Model saved: {MOD}/lgbm_20feat_conviction.pkl')
    
    results={'timestamp':time.strftime('%Y-%m-%d %H:%M:%S'),
             'oos_18feat':eval_detailed(apply_stability(apply_threshold(clf_18.predict_proba(X_oo_18),clf_18.classes_)[0]),y_oo,*apply_threshold(clf_18.predict_proba(X_oo_18),clf_18.classes_)[1:]),
             'oos_20feat':eval_detailed(apply_stability(apply_threshold(clf_19.predict_proba(X_oo_19),clf_19.classes_)[0]),y_oo,*apply_threshold(clf_19.predict_proba(X_oo_19),clf_19.classes_)[1:]),
             'vizsga_18feat':r_viz_18,'vizsga_20feat':r_viz_20,
             'feature_importance':top10}
    with open(os.path.join(DOCS,'dir_conviction_results.json'),'w') as f:
        json.dump(results,f,indent=2,default=str)

    print(f'\n{"="*70}')
    print(f'  DIR CONVICTION STUDY KESZ - {time.time()-t0:.0f}s')
    print(f'{"="*70}')

if __name__=='__main__': main()
