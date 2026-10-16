"""
Session / Kill Zone Feature Templates for Scalper Copilot
Source: advisors/mt5_mql5/BAKOMEGoldScalper (Silver Bullet), advisors/traderview_pine/CSA-15 (HTF filter)
Purpose: Time-of-day features — kill zones, session volume rank, hour encoding
"""
import numpy as np
import pandas as pd


def session_features(timestamps: pd.Series, close: pd.Series,
                      volume: pd.Series, timezone_offset: int = 0) -> pd.DataFrame:
    """
    Session / Kill Zone Features — BAKOME ICT + CSA-15
    
    Kill Zones (UTC hours, adjust with timezone_offset):
    - Asian: 00:00-08:00 (low vol, range building)
    - London Open: 08:00-09:00 (HIGH vol, breakouts)
    - London: 08:00-12:00 
    - New York Open: 13:00-16:00 (HIGH vol, reversal zone)
    - New York: 12:00-17:00
    - London/NY Overlap: 12:00-16:00 (HIGHEST vol)
    
    For BTCUSD (24/7): Kill zones still relevant for institutional activity
    """
    hours = timestamps.dt.hour + timezone_offset
    hours = hours % 24  # wrap around
    
    n = len(timestamps)
    kill_zone_london = np.zeros(n, dtype=bool)
    kill_zone_ny = np.zeros(n, dtype=bool)
    kill_zone_overlap = np.zeros(n, dtype=bool)
    session_asian = np.zeros(n, dtype=bool)
    
    for i in range(n):
        h = hours.iloc[i]
        if 8 <= h < 9:   kill_zone_london[i] = True
        if 13 <= h < 16:  kill_zone_ny[i] = True
        if 12 <= h < 16:  kill_zone_overlap[i] = True
        if 0 <= h < 8:    session_asian[i] = True
    
    # Hour encoding as sin/cos (cyclical — hour 23 is close to hour 0)
    hour_sin = np.sin(2 * np.pi * hours / 24)
    hour_cos = np.cos(2 * np.pi * hours / 24)
    
    # Day of week encoding
    dow = timestamps.dt.dayofweek
    dow_sin = np.sin(2 * np.pi * dow / 7)
    dow_cos = np.cos(2 * np.pi * dow / 7)
    is_weekend = (dow >= 5).astype(int)
    
    # Session volume rank: where does this hour's volume rank historically?
    vol_by_hour = volume.groupby(hours).transform('median')
    session_vol_rank = vol_by_hour.rank(pct=True)
    
    return pd.DataFrame({
        'kill_zone_london': kill_zone_london,
        'kill_zone_ny': kill_zone_ny,
        'kill_zone_overlap': kill_zone_overlap,
        'session_asian': session_asian,
        'hour_sin': hour_sin, 'hour_cos': hour_cos,
        'dow_sin': dow_sin, 'dow_cos': dow_cos,
        'is_weekend': is_weekend,
        'session_vol_rank': session_vol_rank,
        # Composite: in any high-vol kill zone
        'in_kill_zone': kill_zone_london | kill_zone_ny | kill_zone_overlap,
    })


def htf_trend_filter(close: pd.Series, timeframe_bars: int = 4,
                     ema_period: int = 50) -> pd.DataFrame:
    """
    Higher Timeframe Trend Filter — CSA-15
    
    Resample close to HTF (e.g., 4x = 5min→20min or 1min→4min)
    EMA on HTF → trend direction
    
    Returns: htf_bullish, htf_bearish, htf_trend_strength
    """
    # Simple HTF EMA: use rolling mean at HTF scale
    htf_ema = close.rolling(timeframe_bars * ema_period).mean()
    htf_trend = close - htf_ema
    
    # Normalize by ATR proxy
    atr_proxy = close.pct_change().rolling(20).std() * close
    htf_strength = htf_trend / atr_proxy.replace(0, np.nan)
    
    return pd.DataFrame({
        'htf_bullish': (htf_trend > 0).astype(int),
        'htf_bearish': (htf_trend < 0).astype(int),
        'htf_trend_strength': htf_strength.fillna(0),
    })

# Based on: BAKOME ICT Silver Bullet + CSA-15 HTF filter
