import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)

close = df['close'].values
pL = df['p_long_2min'].values
pS = df['p_short_2min'].values

# EREDETI signal: P(L)>P(S) → Long, P(S)>P(L) → Short
orig_sig = np.where(pL > pS, 1, -1)
# FLIP signal: P(S)>P(L) → Long, P(L)>P(S) → Short
flip_sig = np.where(pS > pL, 1, -1)

fwd = np.diff(close)  # close[i+1] - close[i]

# PnL per tick
orig_pnl_tick = orig_sig[:-1] * fwd
flip_pnl_tick = flip_sig[:-1] * fwd

# 1) Micro PnL (1 tick forward)
print('1-TICK FORWARD PnL:')
print(f'  EREDETI: {orig_pnl_tick.sum():+,.1f}  (mean/tick={orig_pnl_tick.mean():+.4f})')
print(f'  FLIP:    {flip_pnl_tick.sum():+,.1f}  (mean/tick={flip_pnl_tick.mean():+.4f})')

# 2) Multi-trend PnL: csak akkor tradelunk ha a dominancia eros
#    (|P(L)-P(S)| > 0.05)
strong = np.abs(pL[:-1] - pS[:-1]) > 0.05
print(f'\nEROS DOMINANCIA (|P(L)-P(S)|>0.05, {strong.sum():,} tick):')
print(f'  EREDETI PnL: {(orig_pnl_tick*strong).sum():+,.1f}')
print(f'  FLIP PnL:    {(flip_pnl_tick*strong).sum():+,.1f}')

# 3) Trend-szintu PnL: 10-tick es 20-tick forward
print(f'\nTREND-SZINTU PnL (N-tick forward):')
for n_fwd in [1, 2, 5, 10, 20, 50]:
    fwd_n = close[n_fwd:] - close[:-n_fwd]
    sig_orig = orig_sig[:-n_fwd]
    sig_flip = flip_sig[:-n_fwd]
    pnl_o = (sig_orig * fwd_n).sum()
    pnl_f = (sig_flip * fwd_n).sum()
    # Win rate
    wr_o = np.mean((sig_orig * fwd_n) > 0) * 100
    wr_f = np.mean((sig_flip * fwd_n) > 0) * 100
    print(f'  +{n_fwd:>2} tick: EREDETI PnL={pnl_o:>+12,.1f} WR={wr_o:.1f}%  |  FLIP PnL={pnl_f:>+12,.1f} WR={wr_f:.1f}%')

# 4) Drawdown kornyeken: bear streak kozben kumulativ PnL
print(f'\nDRAWDOWN TERUELET ELEMZES (08.21 11:55-12:15):')
sub = df.loc['2026-08-21 11:55':'2026-08-21 12:15']
sub_close = sub['close'].values
sub_pL = sub['p_long_2min'].values
sub_pS = sub['p_short_2min'].values
sub_orig = np.where(sub_pL > sub_pS, 1, -1)
sub_flip = np.where(sub_pS > sub_pL, 1, -1)
sub_fwd = np.diff(sub_close)

orig_cum = np.cumsum(sub_orig[:-1] * sub_fwd)
flip_cum = np.cumsum(sub_flip[:-1] * sub_fwd)
price_change = sub_close[-1] - sub_close[0]

print(f'  Arfolyam valtozas: {price_change:+.1f}')
print(f'  EREDETI kumulativ PnL: {orig_cum[-1]:+.1f}')
print(f'  FLIP kumulativ PnL:    {flip_cum[-1]:+.1f}')
print(f'  EREDETI max DD: {np.min(orig_cum - np.maximum.accumulate(orig_cum)):+.1f}')
print(f'  FLIP max DD:    {np.min(flip_cum - np.maximum.accumulate(flip_cum)):+.1f}')

# 5) Egesz 78 nap, trade-szintu (nem tick-szintu)
# Szamoljuk: ha tartjuk a poziciot amig a signal valtozik
# Eredeti signal
print(f'\nTRADE-SZINTU ELEMZES (78 nap):')
for label, sig in [('EREDTI', orig_sig), ('FLIP', flip_sig)]:
    # Minden signal-valtozas = uj trade
    changes = np.where(np.diff(sig) != 0)[0] + 1
    trade_starts = np.concatenate([[0], changes])
    trade_ends = np.concatenate([changes, [len(sig)]])
    
    n_trades = len(trade_starts)
    trade_pnls = []
    for t in range(n_trades - 1):
        s, e = trade_starts[t], trade_ends[t]
        direction = sig[s]
        pnl = direction * (close[min(e, len(close)-1)] - close[s])
        trade_pnls.append(pnl)
    
    trade_pnls = np.array(trade_pnls)
    wins = (trade_pnls > 0).sum()
    losses = (trade_pnls < 0).sum()
    total_pnl = trade_pnls.sum()
    avg_win = trade_pnls[trade_pnls > 0].mean() if wins > 0 else 0
    avg_loss = trade_pnls[trade_pnls < 0].mean() if losses > 0 else 0
    
    print(f'  {label}: {n_trades:,} trade, WR={wins/n_trades*100:.1f}%, PnL={total_pnl:+,.1f}')
    print(f'    avg_win={avg_win:+.2f}  avg_loss={avg_loss:+.2f}  W/L={abs(avg_win/avg_loss):.2f}')

