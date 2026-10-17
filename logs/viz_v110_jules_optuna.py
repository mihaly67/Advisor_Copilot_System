#!/usr/bin/env python3
"""viz_v110_jules_optuna.py — VIZ_STANDARD 10/10 compliant
Optuna Balanced config: WR=59.3% Trades=273
  THL=0.5051 THS=0.4648 THN=0.3290
  stoch_long_kill=-0.2514 stoch_short_kill=0.2732
  stoch_deadzone=0.3845 stability_window=4
"""
import pandas as pd, numpy as np, joblib, os, sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings; warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════
#  KONFIGURACIO — OPTUNA BALANCED v1.10
# ══════════════════════════════════════════════════════════
CFG = dict(
    version   = 'v1.10-Jules-Optuna-Balanced',
    model_dir = '/data/dev/projects/z-ai-copilot/models/production_v110_jules',
    model_file= 'lgbm_v110_jules.pkl',
    feat_file = 'features.txt',
    oos_csv   = '/data/dev/projects/z-ai-copilot/Master_csv/processed/jules_v110_labeled.csv',
    out_html  = '/data/dev/projects/z-ai-copilot/docs/v110/viz_v110_jules_optuna.html',
    # Optuna Balanced threshold-ok
    th_long   = 0.5051,
    th_short  = 0.4648,
    th_noise  = 0.3290,
    # Stoch filter params (Optuna)
    stoch_long_kill  = -0.2514,
    stoch_short_kill =  0.2732,
    stoch_deadzone   =  0.3845,
    stability_window =  4,
    # Idointervallum: utolso N nap
    last_n_days = 5,
)

# RODETETT SZINPALETTA (SOHA NE VALTOZD!)
PAL = dict(
    long      = '#228B22',   # ForestGreen
    short     = '#B22222',   # FireBrick
    noise     = '#888888',   # Gray
    long_lt   = '#32CD32',   # LimeGreen
    short_lt  = '#FF4444',   # Vilagos piros
    bg        = '#111111',
    paper     = '#000000',
    grid      = '#333333',
    zero      = '#444444',
    legend_bg = '#222222',
    font      = 'white',
)

def load_features(model_dir, feat_file):
    path = os.path.join(model_dir, feat_file)
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]

def predict_thr_optuna(model, X, classes, stoch, thl, ths, thn, slk, ssk, sdz, sw):
    """Threshold + Stoch(deadzone) + Stability filter"""
    pr = model.predict_proba(X)
    i0 = list(classes).index(0)
    i1 = list(classes).index(1)
    i2 = list(classes).index(2)
    p_short = pr[:, i0]
    p_noise = pr[:, i1]
    p_long  = pr[:, i2]
    # 1. Threshold
    sig = np.full(len(X), 1, dtype=int)
    sig[(p_long  > thl) & (p_long  > p_short) & (p_noise < thn)] = 2
    sig[(p_short > ths) & (p_short > p_long)  & (p_noise < thn)] = 0
    # 2. Stoch filter with deadzone
    if sdz > 0:
        outside_dz = np.abs(stoch) >= sdz
        sig_f = sig.copy()
        sig_f[(sig==2) & (stoch < slk) & outside_dz] = 1
        sig_f[(sig==0) & (stoch > ssk) & outside_dz] = 1
    else:
        sig_f = sig.copy()
        sig_f[(sig==2) & (stoch < slk)] = 1
        sig_f[(sig==0) & (stoch > ssk)] = 1
    # 3. Stability filter
    if sw >= 2:
        sig_s = np.full(len(sig_f), 1, dtype=int)
        for i in range(sw-1, len(sig_f)):
            w = sig_f[i-sw+1:i+1]
            if len(set(w))==1 and w[0]!=1: sig_s[i] = w[0]
    else:
        sig_s = sig_f
    return sig_s, pr

def build_viz(cfg, pal):
    """Fo vizualizacio epito — STANDARD 2-PANEL LAYOUT + Optuna params"""
    # Betoltes
    m = joblib.load(os.path.join(cfg['model_dir'], cfg['model_file']))
    feat = load_features(cfg['model_dir'], cfg['feat_file'])
    df = pd.read_csv(cfg['oos_csv'])
    df['End_Timestamp'] = pd.to_datetime(df['End_Timestamp'])
    df.sort_values('End_Timestamp', inplace=True); df.reset_index(drop=True, inplace=True)

    # OOS split
    si = int(len(df)*0.8)
    oos = df.iloc[si:].copy().reset_index(drop=True)
    X = oos[feat].fillna(0).replace([np.inf,-np.inf],0)
    y = oos['Target_Label'].values
    stoch = oos['Stoch_State_M1'].values

    # Predikcio
    sig, pr = predict_thr_optuna(m, X, m.classes_, stoch,
        cfg['th_long'], cfg['th_short'], cfg['th_noise'],
        cfg['stoch_long_kill'], cfg['stoch_short_kill'],
        cfg['stoch_deadzone'], cfg['stability_window'])

    # Idointervallum
    ts = oos['End_Timestamp']
    cutoff = ts.max() - pd.Timedelta(days=cfg['last_n_days'])
    mask = ts >= cutoff
    ts_v = ts[mask].values; sig_v = sig[mask]; pr_v = pr[mask]
    stoch_v = stoch[mask]; y_v = y[mask]

    # OHLC
    if 'Open' in oos.columns:
        op=oos['Open'][mask].values; hi=oos['High'][mask].values
        lo=oos['Low'][mask].values; cl=oos['Close'][mask].values
    else:
        cl=oos['Close'][mask].values; op=cl; hi=cl; lo=cl

    # Szamlalok
    i_s=list(m.classes_).index(0); i_n=list(m.classes_).index(1); i_l=list(m.classes_).index(2)
    n_long=int((sig_v==2).sum()); n_short=int((sig_v==0).sum()); n_noise=int((sig_v==1).sum())
    has=sig_v!=1; n_trades=int(has.sum())
    y3=(y_v+1).astype(int)
    acc=(sig_v[has]==y3[has]).mean()*100 if n_trades>0 else 0
    # Per-direction WR
    lm=sig_v==2; sm=sig_v==0
    wr_l=(y3[lm]==2).mean()*100 if lm.sum()>0 else 0
    wr_s=(y3[sm]==0).mean()*100 if sm.sum()>0 else 0

    # ═══ FIGURE ═══
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=[0.65, 0.35])

    # Panel 1: Candlestick
    fig.add_trace(go.Candlestick(x=ts_v, open=op, high=hi, low=lo, close=cl,
        increasing_linecolor=pal['long'], decreasing_linecolor=pal['short'],
        increasing_fillcolor=pal['long'], decreasing_fillcolor=pal['short'],
        name='OHLC'), row=1, col=1)

    # Panel 1: Predikcios markerek
    ml = sig_v == 2
    if ml.any():
        fig.add_trace(go.Scatter(x=ts_v[ml], y=cl[ml], mode='markers',
            marker=dict(color=pal['long'], size=12, symbol='triangle-up',
                        line=dict(color=pal['long_lt'], width=1)),
            name=f'Pred Long ({n_long})'), row=1, col=1)
    ms = sig_v == 0
    if ms.any():
        fig.add_trace(go.Scatter(x=ts_v[ms], y=cl[ms], mode='markers',
            marker=dict(color=pal['short'], size=12, symbol='triangle-down',
                        line=dict(color=pal['short_lt'], width=1)),
            name=f'Pred Short ({n_short})'), row=1, col=1)
    mn = sig_v == 1
    if mn.any():
        fig.add_trace(go.Scatter(x=ts_v[mn], y=cl[mn], mode='markers',
            marker=dict(color=pal['noise'], size=6, symbol='circle'),
            name=f'Pred Noise ({n_noise})'), row=1, col=1)

    # Panel 2: Valoszinuseg gorbek
    fig.add_trace(go.Scatter(x=ts_v, y=pr_v[:,i_l], mode='lines',
        line=dict(color=pal['long'], width=1.5), name='P(Long)'), row=2, col=1)
    fig.add_trace(go.Scatter(x=ts_v, y=pr_v[:,i_s], mode='lines',
        line=dict(color=pal['short'], width=1.5), name='P(Short)'), row=2, col=1)
    fig.add_trace(go.Scatter(x=ts_v, y=pr_v[:,i_n], mode='lines',
        line=dict(color=pal['noise'], width=1.5), name='P(Noise)'), row=2, col=1)

    # Panel 2: Stoch State (extra trace)
    fig.add_trace(go.Scatter(x=ts_v, y=stoch_v, mode='lines',
        line=dict(color='#FFD700', width=1, dash='dot'), name='Stoch M1'), row=2, col=1)

    # Panel 2: Threshold szintek
    fig.add_hline(y=cfg['th_long'], line=dict(color=pal['long'], dash='dash', width=2),
        annotation_text=f'THL={cfg["th_long"]:.2f}',
        annotation=dict(font=dict(color=pal['long'], size=12), xanchor='right'), row=2, col=1)
    fig.add_hline(y=cfg['th_short'], line=dict(color=pal['short'], dash='dash', width=2),
        annotation_text=f'THS={cfg["th_short"]:.2f}',
        annotation=dict(font=dict(color=pal['short'], size=12), xanchor='right'), row=2, col=1)
    fig.add_hline(y=cfg['th_noise'], line=dict(color=pal['noise'], dash='dot', width=2),
        annotation_text=f'THN={cfg["th_noise"]:.2f}',
        annotation=dict(font=dict(color=pal['noise'], size=12), xanchor='right'), row=2, col=1)

    # Stoch kill lines
    fig.add_hline(y=cfg['stoch_long_kill'], line=dict(color=pal['long'], dash='dashdot', width=1),
        annotation_text=f'SLK={cfg["stoch_long_kill"]:.2f}',
        annotation=dict(font=dict(color=pal['long'], size=10), xanchor='left'), row=2, col=1)
    fig.add_hline(y=cfg['stoch_short_kill'], line=dict(color=pal['short'], dash='dashdot', width=1),
        annotation_text=f'SSK={cfg["stoch_short_kill"]:.2f}',
        annotation=dict(font=dict(color=pal['short'], size=10), xanchor='left'), row=2, col=1)
    # Deadzone
    fig.add_hrect(y0=-cfg['stoch_deadzone'], y1=cfg['stoch_deadzone'],
        fillcolor='#FFD700', opacity=0.08, line_width=0, row=2, col=1)

    # Layout
    gc = dict(gridcolor=pal['grid'], linecolor=pal['zero'], zerolinecolor=pal['zero'])
    title = (f'Z.ai {cfg["version"]} | '
             f'L:{n_long} S:{n_short} N:{n_noise} | '
             f'WR:{acc:.1f}% L_WR:{wr_l:.1f}% S_WR:{wr_s:.1f}% | '
             f'THL={cfg["th_long"]:.2f} THS={cfg["th_short"]:.2f} THN={cfg["th_noise"]:.2f} | '
             f'DZ={cfg["stoch_deadzone"]:.2f} SW={cfg["stability_window"]}')
    fig.update_layout(height=1100, width=1400, title_text=title,
        title_font=dict(size=14, color=pal['font']),
        plot_bgcolor=pal['bg'], paper_bgcolor=pal['paper'], font=dict(color=pal['font']),
        xaxis_rangeslider_visible=False,
        xaxis=gc, xaxis2=gc, yaxis=gc, yaxis2=gc,
        legend=dict(bgcolor=pal['legend_bg'], bordercolor=pal['grid'], borderwidth=1,
            font=dict(color=pal['font'], size=11), orientation='h',
            yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=30, t=70, b=40),
        template=dict(layout=dict(xaxis=gc, yaxis=gc)))
    fig.update_yaxes(title_text='Ar', row=1, col=1)
    fig.update_yaxes(title_text='Valoszinuseg / Stoch', row=2, col=1, range=[-1, 1])

    # HTML mentes (CDN Plotly)
    out = cfg['out_html']
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.write_html(out, include_plotlyjs='cdn')
    # Post-process: JS gridcolor fix
    with open(out, 'r') as f: html = f.read()
    for old, new in [('"gridcolor":"white"', '"gridcolor":"#333333"'),
                     ('"linecolor":"white"', '"linecolor":"#444444"'),
                     ('"zerolinecolor":"white"', '"zerolinecolor":"#444444"')]:
        html = html.replace(old, new)
    with open(out, 'w') as f: f.write(html)
    sz = os.path.getsize(out) / 1024
    print(f'\n✅ Saved: {out} ({sz:.0f} KB)', flush=True)

    # Statisztikak
    print(f'\n{"="*60}')
    print(f'VIZ V1.10 OPTUNA BALANCED STATISZTIKAK')
    print(f'{"="*60}')
    print(f'OOS bars (viz): {len(ts_v):,}')
    print(f'Pred Long: {n_long} (WR={wr_l:.1f}%)')
    print(f'Pred Short: {n_short} (WR={wr_s:.1f}%)')
    print(f'Pred Noise: {n_noise}')
    print(f'Trades: {n_trades} WR: {acc:.1f}%')
    print(f'THL={cfg["th_long"]:.4f} THS={cfg["th_short"]:.4f} THN={cfg["th_noise"]:.4f}')
    print(f'SLK={cfg["stoch_long_kill"]:.4f} SSK={cfg["stoch_short_kill"]:.4f} DZ={cfg["stoch_deadzone"]:.4f} SW={cfg["stability_window"]}')
    return fig

if __name__ == '__main__':
    build_viz(CFG, PAL)
