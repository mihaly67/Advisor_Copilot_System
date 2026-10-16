"""
Direction Features — The 6 PRIMARY Direction-Carrying Features
Reference: digest_direction_features.md / AFML Ch.8-9

These features carry BULL/BEAR signal — use them for direction prediction.
Traditional TA (RSI/ADX/Stochastic) are NOT direction features (AUC≈0.53)!
"""
import numpy as np
import pandas as pd


def compute_all_direction_features(df: pd.DataFrame, 
                                    cusum_threshold: float = None,
                                    vol_span: int = 20) -> pd.DataFrame:
    """
    Compute all 6 direction features from OHLC+volume DataFrame.
    
    Args:
        df: DataFrame with ['open','high','low','close','volume'] columns
        cusum_threshold: CUSUM threshold (None=dynamic)
        vol_span: EWMA span for volatility
        
    Returns:
        DataFrame with direction features (all shifted by 1 to prevent leakage)
    """
    features = pd.DataFrame(index=df.index)
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    returns = close.pct_change()
    vol = returns.ewm(span=vol_span).std()
    
    # 1. DF_Curve: CUSUM direction component
    #    sign of cumulative deviation → bull/bear
    if cusum_threshold is None:
        cusum_threshold_series = vol
    else:
        cusum_threshold_series = pd.Series(cusum_threshold, index=df.index)
    
    s_pos = 0.0
    s_neg = 0.0
    df_curve = pd.Series(0.0, index=df.index)
    for i, (t_idx, ret_val) in enumerate(returns.items()):
        thr = cusum_threshold_series.iloc[i] if i < len(cusum_threshold_series) else 0.01
        s_pos = max(0, s_pos + ret_val - thr)
        s_neg = min(0, s_neg + ret_val + thr)
        if s_pos > s_neg:
            df_curve.iloc[i] = 1.0
        else:
            df_curve.iloc[i] = -1.0
    features['df_curve'] = df_curve
    
    # 2. Flow_Delta: volume × (close_position - 0.5) × 2
    #    Buy/sell pressure proxy from bar position
    close_position = (close - low) / (high - low + 1e-10)
    features['flow_delta'] = volume * (close_position - 0.5) * 2
    
    # 3. Price-Volume Correlation: rolling corr(pct_change, volume)
    #    Positive → volume confirms direction
    features['pv_corr'] = returns.rolling(20).corr(volume)
    
    # 4. Momentum Persistence: % positive returns in window
    #    > 0.5 → uptrend persistence, < 0.5 → downtrend persistence
    features['mom_persistence'] = (returns > 0).rolling(20).mean()
    
    # 5. Vol-Adjusted Momentum: momentum / volatility
    #    Risk-corrected direction signal
    momentum_10 = close.pct_change(10)
    features['vol_adj_mom'] = momentum_10 / (vol + 1e-10)
    
    # 6. Variance Ratio 1:4: trending vs mean-reversion
    #    VR > 0.25 → trending, VR < 0.25 → mean-reverting
    var_1 = returns.rolling(20).var()
    var_4 = close.pct_change(4).rolling(20).var()
    features['variance_ratio_1_4'] = var_4 / (4 * var_1 + 1e-10)
    
    # === LEAKAGE PREVENTION: shift all features by 1 ===
    features = features.shift(1)
    
    return features


def compute_boolean_features(df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """
    Boolean features for tree models (AlphaPy style).
    Trees love boolean splits → context combinations.
    """
    bool_feat = pd.DataFrame(index=df.index)
    close = df['close']
    high = df['high']
    low = df['low']
    
    bool_feat['above_ema20'] = (close > close.ewm(span=20).mean()).astype(int)
    bool_feat['above_ema50'] = (close > close.ewm(span=50).mean()).astype(int)
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).ewm(span=14).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(span=14).mean()
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    bool_feat['rsi_oversold'] = (rsi < 30).astype(int)
    bool_feat['rsi_overbought'] = (rsi > 70).astype(int)
    
    # CUSUM-based
    if 'df_curve' in features.columns:
        bool_feat['cusum_bull'] = (features['df_curve'] > 0).astype(int)
        bool_feat['cusum_bear'] = (features['df_curve'] < 0).astype(int)
    
    # Bar type
    bool_feat['bullish_bar'] = (close > df['open']).astype(int)
    
    # Vol regime
    atr = (high - low).rolling(14).mean()
    bool_feat['high_vol'] = (atr > atr.rolling(50).quantile(0.75)).astype(int)
    
    # Trending regime
    if 'variance_ratio_1_4' in features.columns:
        bool_feat['trending'] = (features['variance_ratio_1_4'] > 0.25).astype(int)
    
    # === Context Combinations ===
    bool_feat['fade_short_setup'] = (bool_feat.get('cusum_bear', 0) & bool_feat.get('rsi_oversold', 0)).astype(int)
    bool_feat['bounce_long_setup'] = (bool_feat.get('cusum_bear', 0) & bool_feat.get('above_ema20', 0)).astype(int)
    
    # LEAKAGE PREVENTION
    bool_feat = bool_feat.shift(1)
    
    return bool_feat


if __name__ == '__main__':
    # Demo
    np.random.seed(42)
    n = 2000
    dates = pd.date_range('2025-01-01', periods=n, freq='5min')
    df = pd.DataFrame({
        'open': 60000 + np.cumsum(np.random.randn(n) * 30),
        'high': 60000 + np.cumsum(np.random.randn(n) * 30) + np.abs(np.random.randn(n) * 50),
        'low': 60000 + np.cumsum(np.random.randn(n) * 30) - np.abs(np.random.randn(n) * 50),
        'close': 60000 + np.cumsum(np.random.randn(n) * 30),
        'volume': np.random.randint(100, 1000, n)
    }, index=dates)
    
    features = compute_all_direction_features(df)
    bool_features = compute_boolean_features(df, features)
    
    print("Direction features:")
    print(features.describe().round(4))
    print(f"\nBoolean features:")
    print(bool_features.sum())
