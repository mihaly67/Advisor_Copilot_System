"""
Copilot Chart — Price + Probability Window
"""
import json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

MODEL_DIR = Path('/data/LGBM_copilot/models')
DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')


def find_latest_mtf(instrument='BTCUSD'):
    models = sorted(MODEL_DIR.glob(f'{instrument}_mtf_model_*.txt'))
    metas = sorted(MODEL_DIR.glob(f'{instrument}_mtf_meta_*.json'))
    preds = sorted(MODEL_DIR.glob(f'{instrument}_mtf_preds_*.csv'))
    if not models: return None
    r = {'model_path': models[-1]}
    if metas:
        with open(metas[-1]) as f: r['meta'] = json.load(f)
    if preds: r['preds_path'] = preds[-1]
    return r


def run_chart(instrument='BTCUSD', n_bars=500, threshold=0.55):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.dates as mdates
    
    mtf = find_latest_mtf(instrument)
    if not mtf:
        print(f"No MTF model for {instrument}"); return
    
    meta = mtf.get('meta', {})
    auc = meta.get('auc', 0)
    tr = meta.get('take_rate', 0)
    nf = meta.get('n_features', 0)
    print(f"AUC={auc:.4f}, Take={tr:.2%}, Features={nf}")
    
    preds = pd.read_csv(mtf['preds_path'], index_col=0, parse_dates=True)
    preds = preds.tail(n_bars)
    
    # Load price for these timestamps
    path = DATA_DIR / instrument / f'M1_History_{instrument}.csv'
    price = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
    price.columns = [c.lower() for c in price.columns]
    if 'tickvolume' in price.columns:
        price = price.rename(columns={'tickvolume': 'volume'})
    price = price.tail(n_bars * 10)  # overlap window
    
    common = price.index.intersection(preds.index)
    if len(common) == 0:
        print("No aligned data"); return
    
    close = price.loc[common, 'close']
    p_sub = preds.loc[common]
    
    # FIGURE
    fig = plt.figure(figsize=(18, 11), facecolor='#1a1a2e')
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.12)
    
    # Price
    ax1 = fig.add_subplot(gs[0], facecolor='#16213e')
    ax1.plot(common, close, color='#00d2ff', lw=0.8, alpha=0.9, label='Close')
    
    # Signals
    long_sig = p_sub[p_sub['prob_take'] > threshold]
    short_sig = p_sub[p_sub['prob_take'] < (1-threshold)]
    li = long_sig.index.intersection(common)
    si = short_sig.index.intersection(common)
    if len(li) > 0:
        ax1.scatter(li, close.loc[li]*0.998, marker='^', color='#00ff88', s=25, alpha=0.7, label=f'Long ({len(li)})')
    if len(si) > 0:
        ax1.scatter(si, close.loc[si]*1.002, marker='v', color='#ff4444', s=25, alpha=0.7, label=f'Short ({len(si)})')
    
    ax1.set_title(f'{instrument} Copilot | AUC={auc:.4f} | Take={tr:.1%} | Thr={threshold}',
                color='white', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price', color='white')
    ax1.tick_params(colors='white')
    ax1.legend(loc='upper left', facecolor='#16213e', edgecolor='#00d2ff', labelcolor='white')
    ax1.grid(True, alpha=0.15, color='#00d2ff')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    for s in ax1.spines.values(): s.set_color('#00d2ff'); s.set_alpha(0.3)
    
    # Probability
    ax2 = fig.add_subplot(gs[1], sharex=ax1, facecolor='#16213e')
    probs = p_sub['prob_take'].values
    colors = ['#00ff88' if p > threshold else '#ff4444' if p < (1-threshold) else '#888888' for p in probs]
    ax2.bar(p_sub.index, probs, color=colors, alpha=0.7, width=0.001)
    ax2.axhline(y=threshold, color='#ffaa00', ls='--', lw=1.5, label=f'Thr={threshold}')
    ax2.axhline(y=0.5, color='#888888', ls=':', lw=1, alpha=0.5)
    ax2.set_ylabel('P(Take)', color='white')
    ax2.set_ylim(0, 1)
    ax2.tick_params(colors='white')
    ax2.legend(loc='upper left', facecolor='#16213e', edgecolor='#ffaa00', labelcolor='white')
    ax2.grid(True, alpha=0.15, color='#00d2ff')
    for s in ax2.spines.values(): s.set_color('#00d2ff'); s.set_alpha(0.3)
    
    plt.tight_layout()
    out_dir = Path('/data/LGBM_copilot/charts')
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'{instrument}_copilot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    fig.savefig(out, dpi=150, facecolor=fig.get_facecolor())
    print(f"Chart saved: {out}")
    plt.close()
    return out


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--bars', type=int, default=500)
    p.add_argument('--threshold', type=float, default=0.55)
    a = p.parse_args()
    run_chart(a.instrument, a.bars, a.threshold)