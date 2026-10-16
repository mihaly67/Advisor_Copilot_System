"""
Sample Weights — AFML Ch.4
Reference: financial-ml-toolkit/pipeline/sample_weights.py

MUST use with financial labels! Overlapping triple barriers create concurrent labels.
Unweighted training → biased toward overlapping samples.
"""
import numpy as np
import pandas as pd


def get_num_concurrent_events(close_index: pd.DatetimeIndex, 
                               t1: pd.Series) -> pd.Series:
    """
    Number of concurrent labels at each time point — VECTORIZED.
    Uses searchsorted for O(n log m) instead of O(n*m).
    """
    close_arr = np.array(close_index, dtype='int64')  # ns timestamps
    concurrent = np.zeros(len(close_arr), dtype=np.float64)
    
    starts = np.array(t1.index, dtype='int64')
    ends = np.array(t1.values, dtype='int64')
    
    # For each interval, add +1 to concurrent[start:end]
    # Use difference array + cumulative sum for O(n+m)
    diff = np.zeros(len(close_arr) + 1, dtype=np.float64)
    
    for s, e in zip(starts, ends):
        i_start = np.searchsorted(close_arr, s, side='left')
        i_end = np.searchsorted(close_arr, e, side='right')
        if i_start < len(diff) and i_end < len(diff):
            diff[i_start] += 1
            diff[i_end] -= 1
    
    concurrent = np.cumsum(diff[:-1])
    return pd.Series(concurrent, index=close_index)


def get_average_uniqueness(t1: pd.Series, close_index: pd.DatetimeIndex,
                           num_iterations: int = 3) -> pd.Series:
    """
    Average uniqueness of each label — VECTORIZED.
    """
    concurrent = get_num_concurrent_events(close_index, t1)
    uniqueness = pd.Series(1.0, index=t1.index)
    
    close_arr = np.array(close_index, dtype='int64')
    conc_arr = concurrent.values
    
    for _ in range(num_iterations):
        starts = np.array(t1.index, dtype='int64')
        ends = np.array(t1.values, dtype='int64')
        for i in range(len(t1)):
            i_s = np.searchsorted(close_arr, starts[i], side='left')
            i_e = np.searchsorted(close_arr, ends[i], side='right')
            if i_e > i_s:
                avg_conc = conc_arr[i_s:i_e].mean()
                uniqueness.iloc[i] = 1.0 / avg_conc if avg_conc > 0 else 0
    
    return uniqueness


def compute_sample_weights(labels_df: pd.DataFrame, close: pd.Series,
                           return_weight: bool = True,
                           time_decay: float = 0.0) -> np.ndarray:
    """
    Compute final sample weights = uniqueness × return_attribution × time_decay
    
    Args:
        labels_df: Output from triple_barrier_meta with ['label','return','timestamp'] + t1 (end time)
        close: Price series for concurrency calculation
        return_weight: If True, multiply by |return|
        time_decay: If > 0, apply exp(-decay × age) decay
        
    Returns:
        sample_weight array for model.fit(sample_weight=...)
    """
    # Uniqueness
    if 't1' in labels_df.columns:
        t1 = labels_df['t1']
    else:
        # Estimate: entry + touch_bar
        t1 = pd.Series(index=labels_df.index, dtype='datetime64[ns]')
        for i, (idx, row) in enumerate(labels_df.iterrows()):
            try:
                loc = close.index.get_loc(idx)
                end_loc = min(loc + row.get('touch_bar', 20), len(close) - 1)
                t1.iloc[i] = close.index[end_loc]
            except:
                t1.iloc[i] = idx
    
    uniqueness = get_average_uniqueness(t1, close.index)
    weights = uniqueness.values.copy()
    
    # Return attribution
    if return_weight and 'return' in labels_df.columns:
        weights *= np.abs(labels_df['return'].values)
    
    # Time decay
    if time_decay > 0:
        ages = np.arange(len(weights), 0, -1) / len(weights)
        weights *= np.exp(-time_decay * ages)
    
    # Normalize
    weights = weights / weights.mean()
    
    return weights


if __name__ == '__main__':
    print("Sample weights module ready")
    print("Usage: weights = compute_sample_weights(labels_df, close)")
    print("Then: model.fit(X, y, sample_weight=weights)")
