#!/usr/bin/env python3
"""
shap_v8_analysis.py - Train v8 features + SHAP + correlation pruning
"""
import sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import load_ticks, make_dollar_bars, label_tbm
from build_features_v8 import build_features_v8
from scalper_copilot_v6 import DATA_DIR, DOLLAR_THR, SEED

CDIR = Path('/data/LGBM_copilot/charts')
CDIR.mkdir(exist_ok=True)

print("=" * 72)
print("SHAP V8 ANALYSIS - Train + SHAP + prune redundant")
print("=" * 72)

# 1. LOAD
tpath = DATA_DIR / 'BTCUSD_training_tick.csv'
print("\n1. Loading data...")
ticks = load_ticks(str(tpath))
bars = make_dollar_bars(ticks, DOLLAR_THR)

# 2. BUILD V8 FEATURES
print("\n2. Building v8 features...")
feat_df, feat_cols = build_features_v8(bars)
print(f"   {len(feat_df):,} bars, {len(feat_cols)} features")
bars_align = bars.loc[feat_df.index]

# 3. TBM LABEL (2min)
print("\n3. TBM labeling (horizon=120s)...")
y_long, _ = label_tbm(bars_align, 120, pt_m=0.5, sl_m=0.3)
valid = (y_long != 0)
X = feat_df[valid].values
y = y_long[valid]
print(f"   Valid: {valid.sum():,} bars, TP={((y==1)).sum():,} SL={((y==-1)).sum():,}")

# 4. TRAIN
print("\n4. Training LightGBM (5-fold CV) + SHAP...")
lgb_params = {
    'objective': 'binary', 'metric': 'auc',
    'learning_rate': 0.05, 'num_leaves': 31,
    'feature_fraction': 0.7, 'bagging_fraction': 0.8,
    'bagging_freq': 5, 'seed': SEED, 'verbose': -1,
    'min_data_in_leaf': 50, 'lambda_l1': 1.0,
}
n = len(X)
train_start = int(n * 0.1)
X_train = X[train_start:]; y_train = y[train_start:]
feat_names = feat_cols

tscv = TimeSeriesSplit(n_splits=5)
aucs = []; models = []
for fold, (tr, va) in enumerate(tscv.split(X_train)):
    dtr = lgb.Dataset(X_train[tr], label=y_train[tr], feature_name=feat_names)
    dva = lgb.Dataset(X_train[va], label=y_train[va], feature_name=feat_names, reference=dtr)
    m = lgb.train(lgb_params, dtr, 300, [dva], callbacks=[lgb.early_stopping(30, verbose=False)])
    auc = roc_auc_score(y_train[va], m.predict(X_train[va]))
    aucs.append(auc); models.append(m)
    print(f"   Fold {fold+1}: AUC={auc:.4f}")
print(f"   Mean AUC: {np.mean(aucs):.4f} +/- {np.std(aucs):.4f}")

# 5. SHAP
print("\n5. SHAP feature importance...")
import shap
bst = models[-1]
ns = min(5000, len(X_train))
si = np.random.choice(len(X_train), ns, replace=False)
Xs = X_train[si]
explainer = shap.TreeExplainer(bst)
sv = explainer.shap_values(Xs)
if isinstance(sv, list): sv = sv[1]
mean_abs_shap = np.abs(sv).mean(axis=0)
shap_df = pd.DataFrame({
    'feature': feat_names, 'shap_mean_abs': mean_abs_shap,
    'shap_pct': mean_abs_shap / mean_abs_shap.sum() * 100
}).sort_values('shap_pct', ascending=False)


# 6. CORRELATION
print("\n6. Correlation analysis (flag redundant > 0.85)...")
corr_matrix = pd.DataFrame(X_train, columns=feat_names).corr().abs()
redundant = []
for i in range(len(feat_names)):
    for j in range(i+1, len(feat_names)):
        if corr_matrix.iloc[i, j] > 0.85:
            fi, fj = feat_names[i], feat_names[j]
            si_s = shap_df.loc[shap_df['feature'] == fi, 'shap_pct'].values
            sj_s = shap_df.loc[shap_df['feature'] == fj, 'shap_pct'].values
            if len(si_s) > 0 and len(sj_s) > 0:
                drop = fj if si_s[0] >= sj_s[0] else fi
                redundant.append((fi, fj, corr_matrix.iloc[i, j], drop))

seen = set()
for f1, f2, corr, drop in sorted(redundant, key=lambda x: -x[2]):
    if drop not in seen:
        print(f"   {f1:25s} <-> {f2:25s}  corr={corr:.3f}  DROP: {drop}")
        seen.add(drop)

# 7. GROUP SUMMARY
print("\n7. Feature group SHAP summary...")
groups = {
    'CUSUM': ['df_curve', 'df_curve_cont'],
    'FLOW': ['flow_delta', 'mfi_14', 'auto_corr_20'],
    'ZERO_LAG': ['nolag_slope', 'kama_dir', 'laguerre_rsi_dir', 'hull_slope_10'],
    'MOMENTUM': ['cmo_14', 'vol_adj_mom_10', 'mom_persist_20'],
    'RETURNS': ['ret_1', 'ret_3', 'ret_5', 'ret_20', 'dir_x_mom', 'ret_x_atr'],
    'EMA': ['ema_d_5', 'ema_d_60', 'price_accel', 'micro_trend'],
    'ICT': ['fvg_net', 'ob_bull_active', 'poc_dist'],
    'FLOW_STR': ['delta_force_14', 'vroc_14', 'obv_slope_14', 'vol_ma_5', 'vol_ma_20'],
    'VOL': ['atr_pct', 'rv_10', 'rv_60', 'boll_width', 'variance_ratio_1_4', 'hurst_proxy', 'ema_dist_20'],
    'TIME': ['hour_sin', 'hour_cos', 'kill_zone', 'session_vol_rank'],
    'TREND': ['trend_str_33'],
}
for grp, cols in groups.items():
    actual = [c for c in cols if c in shap_df['feature'].values]
    if not actual: continue
    pct = shap_df[shap_df['feature'].isin(actual)]['shap_pct'].sum()
    print(f"   {grp:12s}: {pct:5.1f}% SHAP ({len(actual)} feat)")

# 8. DROPPABLE
print("\n8. Droppable features (<0.5% SHAP or redundant):")
low_shap = shap_df[shap_df['shap_pct'] < 0.5]['feature'].tolist()
for f in low_shap:
    pct = shap_df.loc[shap_df['feature'] == f, 'shap_pct'].values[0]
    print(f"   {f:25s} SHAP={pct:.2f}%")
n_drop = len(low_shap) + len(seen)
print(f"\n   Total droppable: {n_drop} ({len(low_shap)} low SHAP + {len(seen)} redundant)")
print(f"   Final feature count: {len(feat_names) - n_drop}")

# 9. SAVE
out_path = Path('/data/LGBM_copilot/charts/shap_v8_report.txt')
with open(out_path, 'w') as f:
    f.write(f"# SHAP V8 Report | Features: {len(feat_names)} | AUC: {np.mean(aucs):.4f}\n\n")
    for _, row in shap_df.iterrows():
        f.write(f"{row['feature']:30s} {row['shap_pct']:6.2f}%\n")
print(f"\n9. Saved: {out_path}")

print("\n   SHAP Top 30:")
for _, row in shap_df.head(30).iterrows():
    bar = '#' * int(row['shap_pct'] * 2)
    print(f"   {row['feature']:25s} {row['shap_pct']:5.1f}% {bar}")

