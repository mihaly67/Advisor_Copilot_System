#!/usr/bin/env python3
"""SHAP Direction vs Bar Props - highlighted comparison chart"""
import sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import lightgbm as lgb
import plotly.graph_objects as go
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import load_ticks, make_dollar_bars, build_features, DATA_DIR, DOLLAR_THR
MDIR = Path('/data/LGBM_copilot/models/scalper')
CDIR = Path('/data/LGBM_copilot/charts')

# ── Load data + SHAP (reuse from previous run) ──
print("Loading...")
tpath = DATA_DIR / 'BTCUSD_training_tick.csv'
ticks = load_ticks(str(tpath))
bars = make_dollar_bars(ticks, DOLLAR_THR)
fdf, fcols = build_features(bars)

results = {}
for side in ['long', 'short']:
    for hn in ['2min', '3min', '5min']:
        key = f'{side}_{hn}'
        mp = MDIR / f'BTCUSD_v6_{side}_{hn}_shap.txt'
        if not mp.exists(): continue
        print(f"  SHAP: {key}...")
        bst = lgb.Booster(model_file=str(mp))
        ns = min(5000, len(fdf))
        si = np.random.choice(len(fdf), ns, replace=False)
        sv = bst.predict(fdf.iloc[si], pred_contrib=True)
        if sv.ndim == 1: sv = sv.reshape(1, -1)
        nf = sv.shape[1] - 1
        msv = np.abs(sv[:, :nf]).mean(axis=0)
        fn = bst.feature_name()
        results[key] = {'fn': fn[:nf], 'sv': msv}

# Combine L+S
summary = {}
for hn in ['2min', '3min', '5min']:
    lk, sk = f'long_{hn}', f'short_{hn}'
    if lk not in results or sk not in results: continue
    lf, sf = results[lk]['fn'], results[sk]['fn']
    lv, sv = results[lk]['sv'], results[sk]['sv']
    af = list(set(lf) | set(sf))
    comb = {}
    for f in af:
        comb[f] = ((lv[lf.index(f)] if f in lf else 0) + (sv[sf.index(f)] if f in sf else 0)) / 2
    summary[hn] = comb

# ── Category grouping ──
categories = {
    'Bar shape': ['body', 'upper_wick', 'lower_wick', 'bar_range'],
    'Direction/Trend': ['ema_d_5', 'ema_d_10', 'ema_d_30', 'ema_d_60', 'ema_cross', 'dir_x_mom', 'micro_trend', 'mom_persistence', 'mean_rev'],
    'Returns': ['ret_1', 'ret_3', 'ret_5', 'ret_10', 'ret_20', 'price_accel', 'ret_x_atr'],
    'Volatility': ['rv_10', 'rv_20', 'rv_60', 'atr_pct', 'variance_ratio', 'boll_width', 'boll_pos'],
    'Volume': ['vol_ma_5', 'vol_ma_20', 'vol_rel', 'vol_imbalance'],
    'Time': ['bar_dt', 'bar_dt_rel', 'hour_sin', 'hour_cos'],
    'Oscillators': ['rsi_14', 'rsi_28'],
    'EMA slope': ['ema_s_5', 'ema_s_10', 'ema_s_30', 'ema_s_60'],
}
cat_colors = {
    'Bar shape': '#ef5350', 'Direction/Trend': '#ffd54f', 'Returns': '#42a5f5',
    'Volatility': '#ab47bc', 'Volume': '#ff9800', 'Time': '#5c6bc0',
    'Oscillators': '#66bb6a', 'EMA slope': '#26a69a',
}

# ── Build grouped bar chart ──
fig = go.Figure()
hns = ['2min', '3min', '5min']

for cat, feats in categories.items():
    vals = []
    for hn in hns:
        if hn not in summary: continue
        d = summary[hn]
        tot = sum(d.values())
        cat_val = sum(d.get(f, 0) for f in feats) / tot * 100
        vals.append(cat_val)
    fig.add_trace(go.Bar(
        name=cat, x=hns, y=vals,
        marker_color=cat_colors[cat],
        text=[f'{v:.1f}%' for v in vals],
        textposition='inside',
        textfont=dict(size=11, color='#111'),
        hovertemplate=f'{cat}: %{{y:.1f}}%<extra></extra>'
    ))

fig.update_layout(
    barmode='stack',
    title=dict(
        text='SHAP Importance kategóriánként — Hol van az IRÁNY?',
        font=dict(size=18, color='#f2f5fa')
    ),
    template='plotly_dark',
    height=600, width=900,
    paper_bgcolor='rgb(17,17,17)', plot_bgcolor='rgb(17,17,17)',
    font=dict(color='#f2f5fa'),
    yaxis=dict(title='SHAP %', ticksuffix='%'),
    xaxis=dict(title='Horizon'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
)

# Add annotation
dir_pct = {}
for hn in hns:
    if hn not in summary: continue
    d = summary[hn]; tot = sum(d.values())
    dir_pct[hn] = sum(d.get(f, 0) for f in categories['Direction/Trend']) / tot * 100
bar_pct = {}
for hn in hns:
    if hn not in summary: continue
    d = summary[hn]; tot = sum(d.values())
    bar_pct[hn] = sum(d.get(f, 0) for f in categories['Bar shape']) / tot * 100

fig.add_annotation(
    text=f"Bar shape: {bar_pct.get('2min',0):.0f}%/{bar_pct.get('3min',0):.0f}%/{bar_pct.get('5min',0):.0f}% | Direction: {dir_pct.get('2min',0):.0f}%/{dir_pct.get('3min',0):.0f}%/{dir_pct.get('5min',0):.0f}%",
    xref='paper', yref='paper', x=0.5, y=-0.15,
    showarrow=False, font=dict(size=13, color='#ffd54f')
)

out = CDIR / 'shap_direction_vs_barshape.html'
fig.write_html(str(out))
print(f"OK: {out}")

# ── Also: individual feature chart (top 15) with direction highlighted ──
fig2 = go.Figure()
hn = '2min'
d = summary[hn]
sf = sorted(d.items(), key=lambda x: x[1], reverse=True)[:20]
names = [x[0] for x in sf]; vals = [x[1] for x in sf]
tot = sum(d.values())

bar_colors = []
for n in names:
    if n in categories['Direction/Trend']:
        bar_colors.append('#ffd54f')  # yellow highlight
    elif n in categories['Bar shape']:
        bar_colors.append('#ef5350')  # red
    else:
        bar_colors.append('#546e7a')  # gray

fig2.add_trace(go.Bar(
    y=names[::-1], x=[v/tot*100 for v in vals[::-1]], orientation='h',
    marker_color=bar_colors[::-1],
    text=[f'{v/tot*100:.1f}%' for v in vals[::-1]],
    textposition='outside', textfont=dict(size=10, color='#aaa'),
))

fig2.update_layout(
    title=dict(text='SHAP Top-20 feature (2min) — Sárga=Irány, Piros=Bar shape', font=dict(size=16, color='#f2f5fa')),
    template='plotly_dark', height=600, width=900,
    paper_bgcolor='rgb(17,17,17)', plot_bgcolor='rgb(17,17,17)',
    font=dict(color='#f2f5fa'),
    xaxis=dict(title='SHAP %', ticksuffix='%'),
    margin=dict(l=120),
)

out2 = CDIR / 'shap_top20_direction_highlight.html'
fig2.write_html(str(out2))
print(f"OK: {out2}")
