#!/usr/bin/env python3
"""shap_v8_full.py - 5-horizon analysis with pruned v8 features"""
import sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
import shap, plotly.graph_objects as go
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import load_ticks, make_dollar_bars, label_tbm, DATA_DIR, DOLLAR_THR, SEED
from build_features_v8 import build_features_v8, FEATURES_V8_PRUNED
CDIR = Path('/data/LGBM_copilot/charts'); CDIR.mkdir(exist_ok=True)
print('='*72); print('SHAP V8 FULL - 5-horizon, pruned features'); print('='*72)

# 1. LOAD
print('\n1. Loading data...')
ticks = load_ticks(str(DATA_DIR / 'BTCUSD_training_tick.csv'))
bars = make_dollar_bars(ticks, DOLLAR_THR)
print('\n2. Building v8 features...')
feat_all, feat_all_cols = build_features_v8(bars)
print(f'   {len(feat_all):,} bars, {len(feat_all_cols)} features')
pruned_avail = [c for c in FEATURES_V8_PRUNED if c in feat_all_cols]
print(f'   Pruned: {len(pruned_avail)}/{len(FEATURES_V8_PRUNED)}')
feat_df = feat_all[pruned_avail].copy()
bars_al = bars.loc[feat_df.index]

# 2. TRAIN + SHAP PER HORIZON
HORIZONS = [(60,'1min'),(120,'2min'),(180,'3min'),(240,'4min'),(300,'5min')]
LP = {'objective':'binary','metric':'auc','learning_rate':0.05,'num_leaves':31,
      'feature_fraction':0.7,'bagging_fraction':0.8,'bagging_freq':5,
      'seed':SEED,'verbose':-1,'min_data_in_leaf':50,'lambda_l1':1.0}
results = {}
for hsec, hname in HORIZONS:
    print(f'\n--- {hname} ({hsec}s) ---')
    y_l, _ = label_tbm(bars_al, hsec, pt_m=0.5, sl_m=0.3)
    valid = (y_l != 0)
    X = feat_df[valid].values; y = y_l[valid]
    ntp = (y==1).sum(); nsl = (y==-1).sum()
    print(f'   Valid: {valid.sum():,} | TP={ntp:,} SL={nsl:,} ({ntp/(ntp+nsl)*100:.1f}%)')
    n = len(X); s = int(n*0.1); X_t = X[s:]; y_t = y[s:]
    tscv = TimeSeriesSplit(n_splits=5); aucs = []; models = []
    for fold, (tr, va) in enumerate(tscv.split(X_t)):
        dtr = lgb.Dataset(X_t[tr], label=y_t[tr], feature_name=pruned_avail)
        dva = lgb.Dataset(X_t[va], label=y_t[va], feature_name=pruned_avail, reference=dtr)
        m = lgb.train(LP, dtr, 300, [dva], callbacks=[lgb.early_stopping(30, verbose=False)])
        aucs.append(roc_auc_score(y_t[va], m.predict(X_t[va]))); models.append(m)
    print(f'   AUC: {np.mean(aucs):.4f} +/- {np.std(aucs):.4f}')
    # SHAP
    bst = models[-1]
    ns = min(5000, len(X_t)); si = np.random.choice(len(X_t), ns, replace=False)
    sv = shap.TreeExplainer(bst).shap_values(X_t[si])
    if isinstance(sv, list): sv = sv[1]
    ma = np.abs(sv).mean(axis=0); sp_ = ma/ma.sum()*100
    sr = pd.DataFrame({'feature':pruned_avail,'shap_pct':sp_}).sort_values('shap_pct',ascending=False)
    results[hname] = {'auc':np.mean(aucs),'auc_std':np.std(aucs),'shap':sr,
                      'n_valid':int(valid.sum()),'tp_pct':ntp/(ntp+nsl)*100}

# 3. SUMMARY TABLE
hn_list = ['1min','2min','3min','4min','5min']
print(f"\n{'='*72}\nSUMMARY - 5 Horizon Results\n{'='*72}")
print(f"{'Horizon':>8s} {'AUC':>8s} {'Std':>8s} {'Valid':>8s} {'TP%':>8s} {'Top Feature':>20s}")
for hn in hn_list:
    r = results[hn]; top = r['shap'].iloc[0]['feature']
    print(f"{hn:>8s} {r['auc']:>8.4f} {r['auc_std']:>8.4f} {r['n_valid']:>8,} {r['tp_pct']:>7.1f}% {top:>20s}")

# 4. CROSS-HORIZON SHAP
all_feats = pruned_avail
shap_m = pd.DataFrame(index=all_feats)
for hn in hn_list:
    s = results[hn]['shap'].set_index('feature')['shap_pct']
    shap_m[hn] = s.reindex(all_feats).fillna(0)
shap_m['mean'] = shap_m[hn_list].mean(axis=1)
shap_m = shap_m.sort_values('mean', ascending=False)

print(f"\nFeature SHAP% across horizons:")
print(f"{'Feature':>25s} {'1min':>6s} {'2min':>6s} {'3min':>6s} {'4min':>6s} {'5min':>6s} {'MEAN':>6s}")
for feat, row in shap_m.iterrows():
    print(f"{feat:>25s} {row['1min']:>5.1f}% {row['2min']:>5.1f}% {row['3min']:>5.1f}% {row['4min']:>5.1f}% {row['5min']:>5.1f}% {row['mean']:>5.1f}%")

# 5. DROPPABLE
print(f"\nDroppable (mean SHAP < 0.5%):")
for feat, row in shap_m.iterrows():
    if row['mean'] < 0.5: print(f"  {feat:>25s} mean={row['mean']:.2f}%")

# 6. CORRELATION
print(f"\nCorrelation > 0.85:")
corr_m = feat_df.corr().abs(); seen = set()

# 7. PLOTLY
print(f"\n7. Generating charts...")
aucs_v = [results[h]['auc'] for h in hn_list]
stds_v = [results[h]['auc_std'] for h in hn_list]
fig = go.Figure()
fig.add_trace(go.Bar(x=hn_list, y=aucs_v, error_y=dict(type='data', array=stds_v),
    marker_color=['#26a69a','#42a5f5','#ab47bc','#ff9800','#ef5350'],
    name='AUC', text=[f'{a:.4f}' for a in aucs_v], textposition='auto'))
fig.add_hline(y=0.5, line_dash='dash', line_color='gray', annotation_text='Random')
fig.update_layout(title='Scalper V8 - AUC by Horizon (28 pruned features)',
    yaxis_title='AUC', xaxis_title='Horizon', template='plotly_dark', height=500, yaxis_range=[0.48,0.62])
fig.write_html(str(CDIR / 'shap_v8_auc_horizon.html'))

top15 = shap_m.head(15).index.tolist()
hm = shap_m.loc[top15, hn_list].values
fig2 = go.Figure(go.Heatmap(z=hm, x=hn_list, y=top15, colorscale='YlOrRd',
    text=np.round(hm,1), texttemplate='%{text}%', textfont={'size':10}))
fig2.update_layout(title='SHAP% Top 15 Features across Horizons', template='plotly_dark', height=600)
fig2.write_html(str(CDIR / 'shap_v8_heatmap.html'))
print(f"   Saved: {CDIR / 'shap_v8_auc_horizon.html'}, {CDIR / 'shap_v8_heatmap.html'}")

# 8. SAVE REPORT
out = CDIR / 'shap_v8_full_report.txt'
with open(out, 'w') as f:
    f.write(f"# SHAP V8 Full Report | {len(pruned_avail)} features | 5 horizons\n\n")
    f.write(f"{'Horizon':>8s} {'AUC':>8s} {'Std':>8s} {'Valid':>8s} {'TP%':>8s}\n")
    for hn in hn_list:
        r = results[hn]; f.write(f"{hn:>8s} {r['auc']:>8.4f} {r['auc_std']:>8.4f} {r['n_valid']:>8,} {r['tp_pct']:>7.1f}%\n")
    f.write(f"\n# Cross-horizon SHAP%\n")
    for feat, row in shap_m.iterrows():
        f.write(f"{feat:>25s} {row['1min']:>5.1f}% {row['2min']:>5.1f}% {row['3min']:>5.1f}% {row['4min']:>5.1f}% {row['5min']:>5.1f}% mean={row['mean']:>5.1f}%\n")
print(f"   Saved: {out}")

for i in range(len(pruned_avail)):
    for j in range(i+1, len(pruned_avail)):
        c = corr_m.iloc[i, j]
        if c > 0.85:
            fi, fj = pruned_avail[i], pruned_avail[j]
            mi = shap_m.loc[fi, 'mean'] if fi in shap_m.index else 0
            mj = shap_m.loc[fj, 'mean'] if fj in shap_m.index else 0
            drop = fj if mi >= mj else fi
            if drop not in seen: print(f"  {fi:>20s} <-> {fj:>20s} corr={c:.3f} DROP: {drop}"); seen.add(drop)

    bst = models[-1]
    ns = min(5000, len(X_t)); si = np.random.choice(len(X_t), ns, replace=False)
    sv = shap.TreeExplainer(bst).shap_values(X_t[si])
    if isinstance(sv, list): sv = sv[1]
    ma = np.abs(sv).mean(axis=0); sp_ = ma/ma.sum()*100
    sr = pd.DataFrame({'feature':pruned_avail,'shap_pct':sp_}).sort_values('shap_pct',ascending=False)
    results[hname] = {'auc':np.mean(aucs),'auc_std':np.std(aucs),'shap':sr,
                      'n_valid':int(valid.sum()),'tp_pct':ntp/(ntp+nsl)*100}
