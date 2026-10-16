"""
Volume Profile Feature Templates for Scalper Copilot
Source: advisors/traderview_pine/nq1_Scalping_Strategy — Volume Profile POC
Purpose: Volume at price → POC (Point of Control) + Value Area = structural S/R
"""
import numpy as np
import pandas as pd


def volume_profile_poc(close: pd.Series, high: pd.Series, low: pd.Series,
                       volume: pd.Series, n_rows: int = 24,
                       n_bars: int = 150) -> pd.DataFrame:
    """
    Volume Profile POC — NQ1 Scalping Strategy (Pine Script v6)
    
    Distributes volume into price rows → POC = row with max volume
    Value Area = rows containing 70% of volume around POC
    POC acts as MAGNETIC price level — price tends to mean-revert to POC
    
    Returns: poc_price, value_area_high, value_area_low, poc_distance_atr
    """
    n = len(close)
    poc_prices = np.full(n, np.nan)
    vah_prices = np.full(n, np.nan)
    val_prices = np.full(n, np.nan)
    
    for i in range(n_bars, n):
        # Determine price range from lookback window
        window_low = low.iloc[i-n_bars:i].min()
        window_high = high.iloc[i-n_bars:i].max()
        row_size = (window_high - window_low) / n_rows
        if row_size <= 0:
            continue
        
        # Distribute volume into price rows
        vol_by_row = np.zeros(n_rows)
        for j in range(i - n_bars, i):
            # Approximate: distribute bar volume centered at close
            row_idx = int((close.iloc[j] - window_low) / row_size)
            row_idx = min(max(row_idx, 0), n_rows - 1)
            vol_by_row[row_idx] += volume.iloc[j]
        
        # POC = row with maximum volume
        poc_row = np.argmax(vol_by_row)
        poc_prices[i] = window_low + poc_row * row_size
        
        # Value Area: expand from POC until 70% of total volume included
        total_vol = vol_by_row.sum()
        target_vol = total_vol * 0.70
        va_vol = vol_by_row[poc_row]
        va_low_row = poc_row
        va_high_row = poc_row
        
        while va_vol < target_vol and (va_low_row > 0 or va_high_row < n_rows - 1):
            # Expand to whichever side has more volume
            low_vol = vol_by_row[va_low_row - 1] if va_low_row > 0 else 0
            high_vol = vol_by_row[va_high_row + 1] if va_high_row < n_rows - 1 else 0
            if high_vol >= low_vol and va_high_row < n_rows - 1:
                va_high_row += 1
                va_vol += vol_by_row[va_high_row]
            elif va_low_row > 0:
                va_low_row -= 1
                va_vol += vol_by_row[va_low_row]
            else:
                break
        
        vah_prices[i] = window_low + va_high_row * row_size
        val_prices[i] = window_low + va_low_row * row_size
    
    return pd.DataFrame({
        'poc_price': poc_prices,
        'value_area_high': vah_prices,
        'value_area_low': val_prices,
    })


def volume_profile_features(close: pd.Series, high: pd.Series, low: pd.Series,
                            volume: pd.Series, atr: pd.Series,
                            n_rows: int = 24, n_bars: int = 150) -> pd.DataFrame:
    """
    Generate Volume Profile features for ML model.
    
    Key features:
    - poc_distance_atr: distance from close to POC, normalized by ATR
    - poc_as_support: close above POC (bullish)
    - poc_as_resistance: close below POC (bearish)
    - in_value_area: close within value area
    - value_area_width_atr: value area width in ATR units
    """
    vp = volume_profile_poc(close, high, low, volume, n_rows, n_bars)
    
    n = len(close)
    poc_dist = np.full(n, np.nan)
    poc_support = np.zeros(n, dtype=bool)
    poc_resistance = np.zeros(n, dtype=bool)
    in_va = np.zeros(n, dtype=bool)
    va_width = np.full(n, np.nan)
    
    for i in range(n):
        if np.isnan(vp['poc_price'].iloc[i]) or np.isnan(atr.iloc[i]) or atr.iloc[i] == 0:
            continue
        poc_dist[i] = (close.iloc[i] - vp['poc_price'].iloc[i]) / atr.iloc[i]
        poc_support[i] = close.iloc[i] > vp['poc_price'].iloc[i]
        poc_resistance[i] = close.iloc[i] < vp['poc_price'].iloc[i]
        in_va[i] = vp['value_area_low'].iloc[i] <= close.iloc[i] <= vp['value_area_high'].iloc[i]
        if not np.isnan(vp['value_area_high'].iloc[i]):
            va_width[i] = (vp['value_area_high'].iloc[i] - vp['value_area_low'].iloc[i]) / atr.iloc[i]
    
    return pd.DataFrame({
        'poc_distance_atr': poc_dist,
        'poc_as_support': poc_support,
        'poc_as_resistance': poc_resistance,
        'in_value_area': in_va,
        'value_area_width_atr': va_width,
    })

# Based on: Aksee123/nq1_Scalping_Strategy — Volume Profile POC (Pine Script v6)
