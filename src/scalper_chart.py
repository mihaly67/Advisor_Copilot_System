"""
Scalper Chart — P(Long) + P(Short) continuous display
Top: price with colored background (green=Long, red=Short)
Bottom: P(Long) and P(Short) lines
"""
import json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')


def find_latest_scalper(instrument='BTCUSD'):
    metas = sorted(MODEL_DIR.glob(f'{instrument}_scalper_meta_*.json'))
    if not metas: return None
    with open(metas[-1]) as f: meta = json.load(f)
    preds = sorted(MODEL_DIR.glob(f'{instrument}_scalper_preds_*.csv'))
    prices = sorted(MODEL_DIR.glob(f'{instrument}_scalper_price_*.csv'))
    r = {'meta': meta}
    if preds: r['preds'] = preds[-1]
    if prices: r['price'] = prices[-1]
    return r


def run_scalper_chart(instrument='BTCUSD', n_bars=2000):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.dates as mdates
    
    s = find_latest_scalper(instrument)
    if not s: print(f"No scalper model for {instrument}"); return
    meta = s['meta']
    la = meta.get('long_auc', 0)
    sa = meta.get('short_auc', 0)
    lt = meta.get('long_thr', 0.5)
    st = meta.get('short_thr', 0.5)
    print(f"Long AUC={la:.4f}, Short AUC={sa:.4f}")
    
    preds = pd.read_csv(s['preds'], index_col=0, parse_dates=True).tail(n_bars)
    price = pd.read_csv(s['price'], index_col=0, parse_dates=True)
    price = price.reindex(preds.index).ffill().bfill()
    
    fig = plt.figure(figsize=(20, 12), facecolor='#1a1a2e')
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1.5, 0.5], hspace=0.12)
    
    # Price + signals
    ax1 = fig.add_subplot(gs[0], facecolor='#16213e')
    ax1.plot(preds.index, price.values, color='#00d2ff', lw=0.8, label='Mid')
    # Color by net signal
    net = preds['p_long'] - preds['p_short']
    for i in range(1, len(preds)):
        if net.iloc[i] > 0.05:
            ax1.axvspan(preds.index[i-1], preds.index[i], alpha=0.1, color='#00ff88')
        elif net.iloc[i] < -0.05:
            ax1.axvspan(preds.index[i-1], preds.index[i], alpha=0.1, color='#ff4444')
    # Signal markers
    long_sig = preds[preds['p_long'] > lt]
    short_sig = preds[preds['p_short'] > st]
    li = long_sig.index
    si = short_sig.index
    if len(li) > 0: ax1.scatter(li, price.loc[li]*0.9997, marker='^', color='#00ff88', s=15, alpha=0.6, label=f'Long ({len(li)})')
    if len(si) > 0: ax1.scatter(si, price.loc[si]*1.0003, marker='v', color='#ff4444', s=15, alpha=0.6, label=f'Short ({len(si)})')
    ax1.set_title(f'{instrument} Scalper | Long AUC={la:.3f} | Short AUC={sa:.3f}', color='white', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price', color='white')
    ax1.tick_params(colors='white')
    ax1.legend(loc='upper left', facecolor='#16213e', edgecolor='#00d2ff', labelcolor='white', fontsize=9)
    ax1.grid(True, alpha=0.15, color='#00d2ff')
    for sp in ax1.spines.values(): sp.set_color('#00d2ff'); sp.set_alpha(0.3)
    
    # P(Long) + P(Short)
    ax2 = fig.add_subplot(gs[1], sharex=ax1, facecolor='#16213e')
    ax2.plot(preds.index, preds['p_long'], color='#00ff88', lw=1, alpha=0.8, label=f'P(Long) thr={lt:.2f}')
    ax2.plot(preds.index, preds['p_short'], color='#ff4444', lw=1, alpha=0.8, label=f'P(Short) thr={st:.2f}')
    ax2.axhline(y=lt, color='#00ff88', ls='--', lw=0.8, alpha=0.5)
    ax2.axhline(y=st, color='#ff4444', ls='--', lw=0.8, alpha=0.5)
    ax2.fill_between(preds.index, lt, preds['p_long'], where=(preds['p_long'] > lt), color='#00ff88', alpha=0.15)
    ax2.fill_between(preds.index, st, preds['p_short'], where=(preds['p_short'] > st), color='#ff4444', alpha=0.15)
    ax2.set_ylabel('Probability', color='white')
    ax2.set_ylim(0, 1)
    ax2.tick_params(colors='white')
    ax2.legend(loc='upper left', facecolor='#16213e', edgecolor='#00d2ff', labelcolor='white', fontsize=9)
    ax2.grid(True, alpha=0.15, color='#00d2ff')
    for sp in ax2.spines.values(): sp.set_color('#00d2ff'); sp.set_alpha(0.3)
    
    # Info bar
    ax3 = fig.add_subplot(gs[2], facecolor='#1a1a2e'); ax3.axis('off')
    info = f'📊 Long signals: {len(li)} | Short signals: {len(si)} | Total: {len(preds)} | ~{meta.get("subsample",5)} ticks/sample'
    ax3.text(0.5, 0.5, info, transform=ax3.transAxes, color='#00d2ff', fontsize=12, ha='center', va='center', fontfamily='monospace')
    
    plt.tight_layout()
    out = Path('/data/LGBM_copilot/charts') / f'{instrument}_scalper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    fig.savefig(out, dpi=150, facecolor=fig.get_facecolor())
    print(f"Chart saved: {out}")
    plt.close()
    return out


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--bars', type=int, default=2000)
    a = p.parse_args()
    run_scalper_chart(a.instrument, a.bars)