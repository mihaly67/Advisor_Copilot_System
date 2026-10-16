"""
Dollar Bar Construction — AFML Ch.2
Reference: financial-ml-toolkit/pipeline/bars.py

Dollar bars: Σ(price × volume) ≥ threshold → new bar
WHY: Volatility-adaptive, reduces noise, better for ML than time bars.
"""
import numpy as np
import pandas as pd


def dollar_bars(df: pd.DataFrame, threshold: float = 500000) -> pd.DataFrame:
    """
    Construct dollar bars from tick/1-min data.
    
    Args:
        df: DataFrame with ['timestamp','open','high','low','close','volume']
        threshold: Dollar volume threshold (Σ price×volume ≥ threshold → new bar)
        
    Returns:
        DataFrame with OHLC dollar bars
    """
    # Vectorized dollar bar construction
    closes = df['close'].values
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    vols = df['volume'].values
    dollars = closes * vols
    
    # Use index as timestamp if DatetimeIndex
    if isinstance(df.index, pd.DatetimeIndex):
        timestamps = df.index
    elif 'timestamp' in df.columns:
        timestamps = pd.DatetimeIndex(df['timestamp'].values)
    else:
        timestamps = df.index
    
    bars = []
    cum_dollar = 0.0
    bar_open = bar_high = bar_low = bar_close = None
    bar_start = None
    n = len(df)
    
    for i in range(n):
        d = dollars[i]
        if bar_open is None:
            bar_open = opens[i]
            bar_high = highs[i]
            bar_low = lows[i]
            bar_close = closes[i]
            cum_dollar = d
            bar_start = timestamps[i]
            continue
        
        bar_high = max(bar_high, highs[i])
        bar_low = min(bar_low, lows[i])
        bar_close = closes[i]
        cum_dollar += d
        
        if cum_dollar >= threshold:
            bars.append({
                'timestamp': bar_start,
                'open': bar_open,
                'high': bar_high,
                'low': bar_low,
                'close': bar_close,
                'volume': cum_dollar / bar_close,
                'dollar_volume': cum_dollar,
            })
            bar_open = None
            cum_dollar = 0.0
    
    return pd.DataFrame(bars)


# === INSTRUMENT THRESHOLDS (from concept_map.json → instruments) ===
THRESHOLDS = {
    'BTCUSD': 500_000,    # 500K USD
    'XAUUSD': 5_000_000,  # 5M USD
}


if __name__ == '__main__':
    # Demo
    np.random.seed(42)
    n = 10000
    df = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='1min'),
        'open': 60000 + np.cumsum(np.random.randn(n) * 10),
        'high': 60000 + np.cumsum(np.random.randn(n) * 10) + np.abs(np.random.randn(n) * 20),
        'low': 60000 + np.cumsum(np.random.randn(n) * 10) - np.abs(np.random.randn(n) * 20),
        'close': 60000 + np.cumsum(np.random.randn(n) * 10),
        'volume': np.random.randint(10, 500, n),
    })
    
    bars = dollar_bars(df, threshold=THRESHOLDS['BTCUSD'])
    print(f"Input bars: {len(df)}, Dollar bars: {len(bars)}")
    print(f"Compression ratio: {len(df)/len(bars):.1f}x")
    print(bars.head())
