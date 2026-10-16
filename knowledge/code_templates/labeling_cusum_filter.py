"""
CUSUM Filter — Event Detection for Financial ML Pipeline
Reference: AFML Ch.2 / financial-ml-toolkit/pipeline/labeling_advanced.py::cusum_filter

Purpose: Detect significant price deviations → event timestamps + direction
Key insight: CUSUM direction = primary side signal!
  - DOWN event → Long candidate (contrarian: price dropped, expect bounce)
  - UP event → Short candidate (contrarian: price rose, expect reversal)
"""
import numpy as np
import pandas as pd


def cusum_filter(close: pd.Series, threshold: float = None,
                 vol_span: int = 20, vol_mult: float = 1.0) -> pd.DataFrame:
    """
    CUSUM filter for event detection.
    
    Args:
        close: Price series (pd.Series with DatetimeIndex)
        threshold: Fixed threshold (if None, uses dynamic EWMA volatility)
        vol_span: EWMA span for dynamic threshold
        vol_mult: Multiplier for dynamic threshold
        
    Returns:
        DataFrame with columns: ['timestamp', 'direction']
          direction: +1 = UP event (short candidate), -1 = DOWN event (long candidate)
    """
    # Dynamic threshold from EWMA volatility
    if threshold is None:
        daily_vol = close.pct_change().ewm(span=vol_span).std()
        threshold_series = daily_vol * vol_mult
    else:
        threshold_series = pd.Series(threshold, index=close.index)
    
    s_pos = 0.0
    s_neg = 0.0
    events = []
    
    returns = close.pct_change().dropna()
    
    for t_idx, ret in returns.items():
        thr = threshold_series.loc[t_idx] if t_idx in threshold_series.index else threshold
        
        s_pos = max(0, s_pos + ret - thr)
        s_neg = min(0, s_neg + ret + thr)
        
        if s_neg < -thr:
            # DOWN event → Long candidate
            events.append({'timestamp': t_idx, 'direction': -1, 's_neg': s_neg})
            s_neg = 0
            s_pos = 0
        elif s_pos > thr:
            # UP event → Short candidate
            events.append({'timestamp': t_idx, 'direction': 1, 's_pos': s_pos})
            s_pos = 0
            s_neg = 0
    
    return pd.DataFrame(events).set_index('timestamp')


# === INSTRUMENT PARAMS (from concept_map.json → instruments) ===
# NEVER hardcode! Read from config.
INSTRUMENT_PARAMS = {
    'BTCUSD': {'vol_span': 20, 'vol_mult': 1.0},
    'XAUUSD': {'vol_span': 20, 'vol_mult': 1.2},
}


if __name__ == '__main__':
    # Demo with synthetic data
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=1000, freq='5min')
    prices = pd.Series(60000 + np.cumsum(np.random.randn(1000) * 50), index=dates)
    
    events = cusum_filter(prices)
    print(f"Total events: {len(events)}")
    print(f"UP events (short): {(events['direction'] == 1).sum()}")
    print(f"DOWN events (long): {(events['direction'] == -1).sum()}")
    print(events.head(10))
