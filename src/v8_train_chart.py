#!/usr/bin/env python3
"""v8_train_chart.py - Train 1-5min models + chart 1 day OOS with probability"""
import sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
import plotly.graph_objects as go
import plotly.subplots as sp
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import load_ticks, make_dollar_bars, label_tbm, DATA_DIR, EXAM_DIR, DOLLAR_THR, SEED
from build_features_v8 import build_features_v8, FEATURES_V8_PRUNED
MDIR = Path('/data/LGBM_copilot/models/scalper'); MDIR.mkdir(exist_ok=True)
CDIR = Path('/data/LGBM_copilot/charts')
print('='*72); print('V8 TRAIN + CHART - 5 horizon, 1 day OOS'); print('='*72)

# Pruned features (drop kill_zone + ema_d_5 based on SHAP)
KEEP = [f for f in FEATURES_V8_PRUNED if f not in ('kill_zone','ema_d_5')]
print(f"Features: {len(KEEP)}")

# 1. LOAD TRAIN
print('\n1. Loading TRAIN...')
ticks_tr = load_ticks(str(DATA_DIR / 'BTCUSD_training_tick.csv'))
bars_tr = make_dollar_bars(ticks_tr, DOLLAR_THR)
feat_tr, cols_tr = build_features_v8(bars_tr)
avail = [c for c in KEEP if c in cols_tr]
feat_tr = feat_tr[avail]
bars_tr_al = bars_tr.loc[feat_tr.index]
print(f'   Train: {len(feat_tr):,} bars, {len(avail)} features')

# 2. LOAD EXAM (OOS)
print('\n2. Loading EXAM...')
ticks_ex = load_ticks(str(EXAM_DIR / 'BTCUSD_exam_tick.csv'), label='EXAM')
bars_ex = make_dollar_bars(ticks_ex, DOLLAR_THR)
feat_ex, cols_ex = build_features_v8(bars_ex)
feat_ex = feat_ex[[c for c in avail if c in cols_ex]]
bars_ex_al = bars_ex.loc[feat_ex.index]
print(f'   Exam: {len(feat_ex):,} bars')

# 3. TRAIN + PREDICT PER HORIZON
HORIZONS = [(60,'1min'),(120,'2min'),(180,'3min'),(240,'4min'),(300,'5min')]
LP = {'objective':'binary','metric':'auc','learning_rate':0.05,'num_leaves':31,
      'feature_fraction':0.7,'bagging_fraction':0.8,'bagging_freq':5,
      'seed':SEED,'verbose':-1,'min_data_in_leaf':50,'lambda_l1':1.0}
models = {}; preds = {}
for hsec, hname in HORIZONS:
    print(f'\n--- {hname} ---')
    y_l, _ = label_tbm(bars_tr_al, hsec, pt_m=0.5, sl_m=0.3)
    valid = (y_l != 0); X = feat_tr[valid].values; y = y_l[valid]
    ntp=(y==1).sum(); nsl=(y==-1).sum()
    print(f'   Train: {valid.sum():,} | TP={ntp:,} SL={nsl:,} ({ntp/(ntp+nsl)*100:.1f}%)')
    n=len(X); s=int(n*0.1); X_t=X[s:]; y_t=y[s:]
    tscv=TimeSeriesSplit(n_splits=5); aucs=[]
    for fold,(tr,va) in enumerate(tscv.split(X_t)):
        dtr=lgb.Dataset(X_t[tr],label=y_t[tr],feature_name=avail)
        dva=lgb.Dataset(X_t[va],label=y_t[va],feature_name=avail,reference=dtr)
        m=lgb.train(LP,dtr,300,[dva],callbacks=[lgb.early_stopping(30,verbose=False)])
        aucs.append(roc_auc_score(y_t[va],m.predict(X_t[va])))
    print(f'   AUC: {np.mean(aucs):.4f} +/- {np.std(aucs):.4f}')
    # Retrain on ALL train data
    dall=lgb.Dataset(X_t,label=y_t,feature_name=avail)
    bst=lgb.train(LP,dall,200)  # fixed rounds on full data
    models[hname]=bst
    # Save model
    bst.save_model(str(MDIR / f'v8_long_{hname}.txt'))
    # Predict on exam
    X_ex = feat_ex[avail].values
    p = bst.predict(X_ex)
    preds[hname] = pd.Series(p, index=feat_ex.index)
    print(f'   OOS predictions: {len(p):,} bars, mean={p.mean():.3f}')

# 4. CHART 1 DAY OOS
print(f'\n4. Generating charts (1 day)...')
# Get the LAST day in exam data
last_day = bars_ex_al.index[-1].date()
day_mask = bars_ex_al.index.map(lambda t: t.date()) == last_day
day_idx = bars_ex_al.index[day_mask]
day_bars = bars_ex_al.loc[day_idx]
print(f'   Day: {last_day}, {len(day_bars)} bars')

for hsec, hname in HORIZONS:
    p = preds[hname]
    day_p = p.reindex(day_idx).dropna()
    if len(day_p) == 0: continue
    day_b = bars_ex_al.loc[day_p.index]
    times = day_b.index; prices = day_b['close'].values; probs = day_p.values

    # --- TOP: Price + P(Long) scatter ---
    fig = sp.make_subplots(rows=2, cols=1, row_heights=[0.65, 0.35],
        shared_xaxes=True, vertical_spacing=0.03,
        subplot_titles=[f'BTCUSD V8 {hname} — {last_day}', 'P(Long) - 0.5'])

    # Price candlestick
    fig.add_trace(go.Candlestick(x=times, open=day_b['open'], high=day_b['high'],
        low=day_b['low'], close=day_b['close'], name='Price',
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
        showlegend=False), row=1, col=1)

    # P(Long) as colored scatter on price
    colors = ['#26a69a' if p > 0.55 else '#ef5350' if p < 0.45 else '#9e9e9e' for p in probs]
    fig.add_trace(go.Scatter(x=times, y=prices, mode='markers',
        marker=dict(color=colors, size=4, opacity=0.6), name='P(Long)',
        hovertemplate='Time: %{x}<br>Price: %{y:.1f}<br>P: %{text:.3f}<extra></extra>',
        text=probs, showlegend=True, legendgroup='prob'), row=1, col=1)

    # P(Long) bar chart below price
    bar_colors = ['#26a69a' if p > 0.55 else '#ef5350' if p < 0.45 else '#616161' for p in probs]
    fig.add_trace(go.Bar(x=times, y=probs - 0.5, marker_color=bar_colors,
        name='P-0.5', hovertemplate='Time: %{x}<br>P(Long): %{text:.3f}<extra></extra>',
        text=probs, showlegend=False), row=2, col=1)
    fig.add_hline(y=0, line_dash='dash', line_color='gray', line_width=1, row=2, col=1)

    # Layout
    fig.update_layout(template='plotly_dark', height=800,
        xaxis_rangeslider_visible=False,
        yaxis1_title='Price ($)', yaxis2_title='P(Long) - 0.5',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=30, t=60, b=40))
    fig.update_xaxes(type='category', row=1, col=1)
    fig.update_xaxes(type='category', row=2, col=1)

    p_out = CDIR / f'BTCUSD_v8_{hname}_{last_day}.html'
    fig.write_html(str(p_out))
    print(f'   Saved: {p_out.name}')

    # --- Probability distribution histogram ---
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(x=probs, nbinsx=50, marker_color='#42a5f5',
        opacity=0.7, name='P(Long)', hovertemplate='P: %{x:.3f}<br>Count: %{y}<extra></extra>'))
    fig2.add_vline(x=0.5, line_dash='dash', line_color='white', annotation_text='Random')
    fig2.add_vline(x=np.mean(probs), line_dash='dot', line_color='#ff9800',
        annotation_text=f'Mean={np.mean(probs):.3f}')
    n_long = (probs > 0.55).sum(); n_short = (probs < 0.45).sum(); n_neutral = len(probs) - n_long - n_short
    fig2.update_layout(template='plotly_dark', height=350,
        title=f'P(Long) Distribution — {hname} | Long:{n_long} Neutral:{n_neutral} Short:{n_short}',
        xaxis_title='P(Long)', yaxis_title='Count', margin=dict(l=50, r=20, t=50, b=40))
    p_out2 = CDIR / f'BTCUSD_v8_{hname}_{last_day}_dist.html'
    fig2.write_html(str(p_out2))
    print(f'   Saved: {p_out2.name}')

print('\n✅ Done!')
