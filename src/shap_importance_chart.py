#!/usr/bin/env python3
"""SHAP Feature Importance Chart - all features, 6 models (L/S x 2/3/5min)"""
import sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import lightgbm as lgb
import plotly.graph_objects as go
import plotly.subplots as sp
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import (
    load_ticks, make_dollar_bars, build_features,
    DATA_DIR, MODEL_DIR, CHART_DIR, DOLLAR_THR
)

MDIR = Path('/data/LGBM_copilot/models/scalper')
CDIR = Path('/data/LGBM_copilot/charts')

print("Adat betoltes...")
tpath = DATA_DIR / 'BTCUSD_training_tick.csv'
ticks = load_ticks(str(tpath))
bars = make_dollar_bars(ticks, DOLLAR_THR)
fdf, fcols = build_features(bars)
print(f"  {len(fdf):,} bars, {len(fcols)} features")

# ── SHAP per model ──
results = {}
for side in ['long', 'short']:
    for hn in ['2min', '3min', '5min']:
        key = f'{side}_{hn}'
        mp = MDIR / f'BTCUSD_v6_{side}_{hn}_shap.txt'
        if not mp.exists():
            print(f"  SKIP {mp}"); continue
        print(f"  SHAP: {key}...")
        bst = lgb.Booster(model_file=str(mp))
        ns = min(5000, len(fdf))
        si = np.random.choice(len(fdf), ns, replace=False)
        Xs = fdf.iloc[si]
        sv = bst.predict(Xs, pred_contrib=True)
        if sv.ndim == 1: sv = sv.reshape(1, -1)
        nf = sv.shape[1] - 1
        msv = np.abs(sv[:, :nf]).mean(axis=0)
        fn = bst.feature_name()
        results[key] = {'fn': fn[:nf], 'sv': msv}
        print(f"    {nf} feats, top={fn[0]} ({msv[0]:.5f})")

# ── Combine L+S per horizon ──
summary = {}
for hn in ['2min', '3min', '5min']:
    lk, sk = f'long_{hn}', f'short_{hn}'
    if lk not in results or sk not in results: continue
    lf, sf = results[lk]['fn'], results[sk]['fn']
    lv, sv = results[lk]['sv'], results[sk]['sv']
    af = list(set(lf) | set(sf))
    comb = {}
    for f in af:
        comb[f] = (lv[lf.index(f)] if f in lf else 0) + (sv[sf.index(f)] if f in sf else 0)
        comb[f] /= 2
    summary[hn] = comb

# ── Color by category ──
C = {'ema':'#26a69a','vol':'#ff9800','ret':'#42a5f5','rv':'#ab47bc',
     'rsi':'#ef5350','boll':'#66bb6a','bar':'#78909c','time':'#5c6bc0','dir':'#ffd54f','other':'#bdbdbd'}
def gc(n):
    if 'ema' in n: return C['ema']
    if 'vol' in n: return C['vol']
    if n.startswith('ret'): return C['ret']
    if n.startswith('rv'): return C['rv']
    if 'rsi' in n: return C['rsi']
    if 'boll' in n: return C['boll']
    if n in ('body','bar_range','upper_wick','lower_wick','atr_pct'): return C['bar']
    if 'hour' in n or 'bar_dt' in n: return C['time']
    if 'dir' in n or 'cross' in n or 'micro' in n or 'mom' in n: return C['dir']
    return C['other']

# ── Plot 3 panels ──
print("Chart...")
fig = sp.make_subplots(rows=1, cols=3, subplot_titles=['2min','3min','5min'], horizontal_spacing=0.12)
for col, hn in enumerate(['2min','3min','5min'], 1):
    if hn not in summary: continue
    d = summary[hn]
    sf = sorted(d.items(), key=lambda x: x[1], reverse=True)
    names = [x[0] for x in sf]; vals = [x[1] for x in sf]
    bc = [gc(n) for n in names]
    fig.add_trace(go.Bar(y=names[::-1], x=vals[::-1], orientation='h',
        marker_color=bc[::-1], text=[f'{v:.4f}' for v in vals[::-1]],
        textposition='outside', textfont=dict(size=8, color='#aaa'),
        showlegend=False, hovertemplate='%{y}: %{x:.5f}<extra></extra>'
    ), row=1, col=col)

fig.update_layout(
    title=dict(text='SHAP Feature Importance - All Features (L+S avg)', font=dict(size=16, color='#f2f5fa')),
    template='plotly_dark', height=900, width=1600,
    paper_bgcolor='rgb(17,17,17)', plot_bgcolor='rgb(17,17,17)',
    font=dict(color='#f2f5fa', size=10), margin=dict(l=120, r=40, t=60, b=40),
)
for c in range(1, 4):
    fig.update_xaxes(title_text='Mean |SHAP|', row=1, col=c, gridcolor='#333')
    fig.update_yaxes(tickfont=dict(size=9), row=1, col=c)

out = CDIR / 'shap_all_features_importance.html'
fig.write_html(str(out))
print(f"OK: {out}")

# ── Text output ──
print("\n" + "="*70)
print("SHAP IMPORTANCE RANKING (L+S avg)")
print("="*70)
for hn in ['2min','3min','5min']:
    if hn not in summary: continue
    d = summary[hn]
    sf = sorted(d.items(), key=lambda x: x[1], reverse=True)
    tot = sum(v for _, v in sf)
    print(f"\n--- {hn} ---")
    for i, (n, v) in enumerate(sf):
        pct = v / tot * 100
        m = '_' if pct < 1 else 'o' if pct < 3 else 'O' if pct < 5 else 'X' if pct < 10 else '#'
        print(f"  {i+1:2d} {n:<20} {v:10.5f} {pct:5.1f}% {m}")

# ── Direction check ──
print("\n" + "="*70)
print("DIRECTION feature-k SHAP")
print("="*70)
df2 = ['ema_cross','dir_x_mom','micro_trend','mom_persistence','mean_rev','ema_d_5','ema_d_10','ema_d_30','ema_d_60']
for hn in ['2min','3min','5min']:
    if hn not in summary: continue
    d = summary[hn]; tot = sum(d.values())
    dt = sum(d.get(f,0) for f in df2)
    print(f"\n{hn}: Direction SHAP% = {dt/tot*100:.1f}%")
    for f in df2:
        v = d.get(f, 0)
        print(f"  {f:<20} {v:.5f} ({v/tot*100:.1f}%)")
