"""
ICT (Inner Circle Trader) Feature Templates for Scalper Copilot
Source: advisors/mt5_mql5/BAKOMEGoldScalper — Ultimate_ICT_Gold_Scalper_v3.0.mq5
Purpose: Fair Value Gaps, Order Blocks, Liquidity Sweeps — structural S/R features
"""
import numpy as np
import pandas as pd


def detect_fvg(high: pd.Series, low: pd.Series, close: pd.Series,
               atr: pd.Series, min_size_atr: float = 0.5) -> pd.DataFrame:
    """
    Fair Value Gap (FVG) Detection — BAKOME ICT Gold Scalper
    
    Bullish FVG: low[i] > high[i-1] (gap up)
    Bearish FVG: high[i] < low[i-1] (gap down)
    Filter: gap_size >= ATR * min_size_atr
    """
    n = len(high)
    fvg_bull = np.zeros(n, dtype=bool)
    fvg_bear = np.zeros(n, dtype=bool)
    fvg_size = np.zeros(n)
    fvg_filled = np.zeros(n, dtype=bool)
    
    for i in range(1, n):
        if low.iloc[i] > high.iloc[i-1]:
            gap = low.iloc[i] - high.iloc[i-1]
            if gap >= atr.iloc[i] * min_size_atr:
                fvg_bull[i] = True
                fvg_size[i] = gap / atr.iloc[i]
        if high.iloc[i] < low.iloc[i-1]:
            gap = low.iloc[i-1] - high.iloc[i]
            if gap >= atr.iloc[i] * min_size_atr:
                fvg_bear[i] = True
                fvg_size[i] = gap / atr.iloc[i]
    
    for i in range(2, n):
        if fvg_bull[i-1] and close.iloc[i] < high.iloc[i-2]:
            fvg_filled[i-1] = True
        if fvg_bear[i-1] and close.iloc[i] > low.iloc[i-2]:
            fvg_filled[i-1] = True
    
    return pd.DataFrame({
        'fvg_bullish': fvg_bull, 'fvg_bearish': fvg_bear,
        'fvg_size_atr': fvg_size, 'fvg_filled': fvg_filled,
        'fvg_bull_active': fvg_bull & ~fvg_filled,
        'fvg_bear_active': fvg_bear & ~fvg_filled,
    })


def detect_order_blocks(open_: pd.Series, high: pd.Series, low: pd.Series,
                        close: pd.Series, volume: pd.Series,
                        atr: pd.Series, min_body_atr: float = 1.0) -> pd.DataFrame:
    """
    Order Block Detection — BAKOME ICT Gold Scalper
    
    Bullish OB: bearish candle[i-1] followed by large bullish candle[i]
    Bearish OB: bullish candle[i-1] followed by large bearish candle[i]
    """
    n = len(close)
    ob_bull = np.zeros(n, dtype=bool)
    ob_bear = np.zeros(n, dtype=bool)
    ob_bull_top = np.full(n, np.nan)
    ob_bull_bot = np.full(n, np.nan)
    ob_bear_top = np.full(n, np.nan)
    ob_bear_bot = np.full(n, np.nan)
    
    for i in range(1, n):
        prev_bearish = close.iloc[i-1] < open_.iloc[i-1]
        curr_bullish = close.iloc[i] > open_.iloc[i]
        curr_body = abs(close.iloc[i] - open_.iloc[i])
        
        if prev_bearish and curr_bullish and curr_body > atr.iloc[i] * min_body_atr:
            ob_bull[i] = True
            ob_bull_top[i] = high.iloc[i-1]
            ob_bull_bot[i] = low.iloc[i-1]
        
        prev_bullish = close.iloc[i-1] > open_.iloc[i-1]
        curr_bearish = close.iloc[i] < open_.iloc[i]
        
        if prev_bullish and curr_bearish and curr_body > atr.iloc[i] * min_body_atr:
            ob_bear[i] = True
            ob_bear_top[i] = high.iloc[i-1]
            ob_bear_bot[i] = low.iloc[i-1]
    
    return pd.DataFrame({
        'ob_bullish': ob_bull, 'ob_bearish': ob_bear,
    })



def detect_liquidity_sweeps(high: pd.Series, low: pd.Series, close: pd.Series,
                            atr: pd.Series, touch_tol_atr: float = 0.1) -> pd.DataFrame:
    """Liquidity Sweep — BAKOME ICT. Swing=2-bar pivot, Sweep=break+reverse."""
    n = len(high)
    swing_high = np.zeros(n, dtype=bool)
    swing_low = np.zeros(n, dtype=bool)
    sweep_high = np.zeros(n, dtype=bool)
    sweep_low = np.zeros(n, dtype=bool)
    for i in range(1, n - 1):
        if high.iloc[i] > high.iloc[i-1] and high.iloc[i] > high.iloc[i+1]: swing_high[i] = True
        if low.iloc[i] < low.iloc[i-1] and low.iloc[i] < low.iloc[i+1]: swing_low[i] = True
    levels = []
    for i in range(n):
        if swing_high[i] or swing_low[i]:
            is_high = swing_high[i]
            lvl_p = high.iloc[i] if is_high else low.iloc[i]
            touches = sum(1 for j in range(max(0,i-20),i)
                         if abs((high.iloc[j] if is_high else low.iloc[j]) - lvl_p) < atr.iloc[j]*touch_tol_atr)
            levels.append({'price': lvl_p, 'is_high': is_high, 'strength': touches})
    for i in range(2, n):
        for lvl in levels:
            if lvl['strength'] < 2: continue
            if lvl['is_high'] and high.iloc[i-1]>lvl['price'] and close.iloc[i]<lvl['price']: sweep_high[i]=True
            elif not lvl['is_high'] and low.iloc[i-1]<lvl['price'] and close.iloc[i]>lvl['price']: sweep_low[i]=True
    return pd.DataFrame({'liq_sweep_high': sweep_high, 'liq_sweep_low': sweep_low, 'swing_high': swing_high, 'swing_low': swing_low})


def generate_ict_features(df: pd.DataFrame, atr_period: int = 14) -> pd.DataFrame:
    """Generate all ICT features from OHLCV DataFrame."""
    atr = df['close'].rolling(atr_period).std() * np.sqrt(atr_period)
    fvg = detect_fvg(df['high'], df['low'], df['close'], atr)
    ob = detect_order_blocks(df['open'], df['high'], df['low'], df['close'], df['volume'], atr)
    liq = detect_liquidity_sweeps(df['high'], df['low'], df['close'], atr)
    return pd.concat([fvg, ob, liq], axis=1)

# Based on: BAKOME-Hub/BAKOMEGoldScalper — Ultimate_ICT_Gold_Scalper_v3.0.mq5
