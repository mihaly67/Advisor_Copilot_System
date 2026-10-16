"""
Triple Barrier Labeling — Meta-Labeling for Trade Filtering
Reference: AFML Ch.3 / financial-ml-toolkit/pipeline/labeling.py::get_meta_labels

Purpose: Given primary side (+1/-1), determine if trade was profitable
  label=1 → TP hit → TAKE the trade
  label=0 → SL hit or timeout → SKIP the trade
  
KEY: Meta-labeling is SIZE FILTER (0/1), NOT direction prediction!
  Prerequisite: MUST have primary side signal first (from CUSUM or strategy)
"""
import numpy as np
import pandas as pd


def get_volatility(close: pd.Series, span: int = 20) -> pd.Series:
    """EWMA volatility of returns — adaptive barrier width."""
    return close.pct_change().ewm(span=span).std()


def triple_barrier_meta(close: pd.Series, events: pd.DataFrame,
                        profit_mult: float = 1.5, stop_mult: float = 1.0,
                        max_bars: int = 20, min_ret: float = 0.0,
                        vol_span: int = 20) -> pd.DataFrame:
    """
    Side-aware Triple Barrier Method for meta-labeling.
    
    Args:
        close: Price series (DatetimeIndex)
        events: DataFrame from cusum_filter with ['direction'] column
                direction: +1 = UP event → short, -1 = DOWN event → long
        profit_mult: TP multiplier × volatility (asymmetric: > stop_mult)
        stop_mult: SL multiplier × volatility (tighter than TP)
        max_bars: Vertical barrier = max holding period in bars
        min_ret: Minimum return for label=1
        vol_span: EWMA span for volatility
        
    Returns:
        DataFrame with: ['side', 'label', 'tp_level', 'sl_level', 'touch_bar', 'return']
          side: +1 (long) or -1 (short) — from CUSUM direction
          label: 1 (take) or 0 (skip) — meta-label
    """
    vol = get_volatility(close, span=vol_span)
    results = []
    
    for event_time, event_row in events.iterrows():
        # CUSUM direction → side
        # DOWN event (-1) → Long side (+1)
        # UP event (+1) → Short side (-1)
        side = -event_row['direction']  # contrarian
        
        # Find index position
        try:
            idx_loc = close.index.get_loc(event_time)
        except KeyError:
            continue
        
        entry_price = close.iloc[idx_loc]
        current_vol = vol.iloc[idx_loc] if not pd.isna(vol.iloc[idx_loc]) else 0.01
        
        # Side-aware barriers
        if side == 1:  # Long
            tp_level = entry_price * (1 + profit_mult * current_vol)
            sl_level = entry_price * (1 - stop_mult * current_vol)
        else:  # Short
            tp_level = entry_price * (1 - profit_mult * current_vol)
            sl_level = entry_price * (1 + stop_mult * current_vol)
        
        # Path evaluation — find first barrier hit
        touch_bar = max_bars
        label = 0
        trade_return = 0.0
        
        for j in range(1, max_bars + 1):
            bar_idx = idx_loc + j
            if bar_idx >= len(close):
                break
            
            current_price = close.iloc[bar_idx]
            
            if side == 1:  # Long position
                if current_price >= tp_level:
                    touch_bar = j
                    trade_return = (current_price - entry_price) / entry_price
                    label = 1 if trade_return >= min_ret else 0
                    break
                if current_price <= sl_level:
                    touch_bar = j
                    trade_return = (current_price - entry_price) / entry_price
                    label = 0  # SL hit → skip
                    break
            else:  # Short position
                if current_price <= tp_level:
                    touch_bar = j
                    trade_return = (entry_price - current_price) / entry_price
                    label = 1 if trade_return >= min_ret else 0
                    break
                if current_price >= sl_level:
                    touch_bar = j
                    trade_return = (entry_price - current_price) / entry_price
                    label = 0  # SL hit → skip
                    break
        else:
            # Timeout — vertical barrier hit
            exit_price = close.iloc[min(idx_loc + max_bars, len(close) - 1)]
            if side == 1:
                trade_return = (exit_price - entry_price) / entry_price
            else:
                trade_return = (entry_price - exit_price) / entry_price
            label = 1 if trade_return >= min_ret else 0
        
        results.append({
            'timestamp': event_time,
            'side': side,
            'label': label,
            'tp_level': tp_level,
            'sl_level': sl_level,
            'touch_bar': touch_bar,
            'return': trade_return
        })
    
    return pd.DataFrame(results).set_index('timestamp')


# === INSTRUMENT PARAMS ===
INSTRUMENT_PARAMS = {
    'BTCUSD': {'profit_mult': 1.5, 'stop_mult': 1.0, 'max_bars': 20, 'vol_span': 20},
    'XAUUSD': {'profit_mult': 2.5, 'stop_mult': 1.5, 'max_bars': 30, 'vol_span': 20},
}


if __name__ == '__main__':
    # Demo
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=5000, freq='5min')
    prices = pd.Series(60000 + np.cumsum(np.random.randn(5000) * 50), index=dates)
    
    # Step 1: CUSUM filter
    from labeling_cusum_filter import cusum_filter
    events = cusum_filter(prices)
    print(f"Events: {len(events)}")
    
    # Step 2: Meta-labeling
    labels = triple_barrier_meta(prices, events, **INSTRUMENT_PARAMS['BTCUSD'])
    print(f"\nLabel distribution:")
    print(labels['label'].value_counts())
    print(f"\nTake rate: {(labels['label']==1).mean():.2%}")
    print(f"\nSide distribution:")
    print(labels['side'].value_counts())
