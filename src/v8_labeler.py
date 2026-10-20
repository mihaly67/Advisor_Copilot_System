#!/usr/bin/env python3
"""
V8 Labeler — Jules V5 Strict Wick Triple Barrier portolva BTCUSD-re
3 osztály: 0=Noise, 1=Short, 2=Long

Jules V5 kulcs különbségek a v6 TBM-től:
  - Entry: NEXT bar Open (nincs lookahead bias)
  - Strict wick: High/Low barrier, Close helyett
  - Same-bar ambiguitás: SL nyer (worst-case)
  - EGY ciklus egyszerre vizsgálja Long és Short barrier-eket
  - EGY 3-osztályú cimke (nem 2 bináris)
"""
import numpy as np, pandas as pd


def label_strict_wick(bars, pt_m=0.5, sl_m=0.3, horizon_sec=60, min_bars=3):
    """
    Jules V5 strict wick triple barrier — BTCUSD ATR adaptáció.
    
    Args:
        bars: DataFrame [open, high, low, close, atr] with DatetimeIndex
        pt_m: PT multiplier x ATR
        sl_m: SL multiplier x ATR
        horizon_sec: max idő (sec) barrier elérésére
        min_bars: minimum lookahead bar-ok
    
    Returns:
        y: np.array int — 0=Noise, 1=Short, 2=Long
    """
    n = len(bars)
    high = bars['high'].values
    low = bars['low'].values
    close = bars['close'].values
    opens = bars['open'].values
    atr = bars['atr'].values
    
    # Bar idő (sec) a horizon-höz
    idx_vals = bars.index.values
    bar_sec = max(1.0, float(np.median(np.diff(idx_vals).astype('int64') / 1e9)))
    max_bars = max(min_bars, int(horizon_sec / bar_sec) + 1)
    
    y = np.zeros(n, dtype=int)  # default: Noise
    
    for i in range(n):
        if i + 1 >= n:
            break
        
        # Entry: NEXT bar Open (Jules V5 — no lookahead bias)
        entry = opens[i + 1]
        a = atr[i] if atr[i] > 0 else entry * 0.001
        
        # Long barriers (ATR adaptív)
        long_pt = entry + pt_m * a   # profit target
        long_sl = entry - sl_m * a   # stop loss
        
        # Short barriers (ATR adaptív)
        short_pt = entry - pt_m * a  # profit target
        short_sl = entry + sl_m * a  # stop loss
        
        hit = 0  # default: Noise
        
        for j in range(i + 1, min(i + 1 + max_bars, n)):
            curr_high = high[j]
            curr_low = low[j]
            
            # --- LONG EVALUATION (strict wick) ---
            long_pt_hit = curr_high >= long_pt
            long_sl_hit = curr_low <= long_sl
            
            # --- SHORT EVALUATION (strict wick) ---
            short_pt_hit = curr_low <= short_pt
            short_sl_hit = curr_high >= short_sl
            
            # Same-bar ambiguitás: SL nyer (worst-case) — Jules V5
            if long_pt_hit and long_sl_hit:
                long_pt_hit = False
            if short_pt_hit and short_sl_hit:
                short_pt_hit = False
            
            # Döntés logika — Jules V5
            if hit == 0:
                if long_pt_hit and not short_pt_hit:
                    hit = 2  # Long
                    break
                elif short_pt_hit and not long_pt_hit:
                    hit = 1  # Short
                    break
                elif long_sl_hit and short_sl_hit:
                    # Trapped: mindkét SL = masszív expanding wick = Noise
                    break
                elif long_sl_hit:
                    # Long halott, Short még élhet — vizsgáljuk tovább
                    pass
                elif short_sl_hit:
                    # Short halott, Long még élhet — vizsgáljuk tovább
                    pass
        
        y[i] = hit
    
    nL = (y == 2).sum(); nS = (y == 1).sum(); nN = (y == 0).sum()
    pctL = nL/n; pctS = nS/n; pctN = nN/n
    print(f"    StrictWick PT={pt_m}xSL={sl_m}x bars={max_bars}: "
          f"Long={nL:,}({pctL:.1%}) Short={nS:,}({pctS:.1%}) Noise={nN:,}({pctN:.1%})")
    return y


def audit_label_symmetry(y, name=''):
    """Ellenőrzi a tükör-problémát: P(Short) ≈ 1-P(Long)?"""
    nL = (y==2).sum(); nS = (y==1).sum(); nN = (y==0).sum(); n = len(y)
    pL = nL/n; pS = nS/n; pN = nN/n
    mirror_diff = abs(pL + pS - 1.0)
    is_mirror = mirror_diff < 0.02  # 2% küszöb
    status = 'TUKOR!' if is_mirror else 'OK'
    print(f"  {name}P(L)={pL:.3f} P(S)={pS:.3f} P(N)={pN:.3f} | "
          f"P(L)+P(S)={pL+pS:.3f} | {status}")
    return not is_mirror
