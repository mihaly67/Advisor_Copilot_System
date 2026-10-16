"""
Purged Walk-Forward Cross-Validation — AFML Ch.7-12
Reference: meta-labeling-harness-main/cross_validate.py

NEVER use sklearn KFold with financial labels — it LEAKS!
Train labels overlap test period → inflated metrics.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold


class PurgedKFold:
    """
    K-Fold with purging and embargo for financial time series.
    
    Purging: Drop train samples whose labels overlap test period.
    Embargo: Add buffer zone around test to prevent information leakage.
    """
    
    def __init__(self, n_splits: int = 5, pct_embargo: float = 0.01, 
                 t1: pd.Series = None):
        """
        Args:
            n_splits: Number of folds
            pct_embargo: Embargo as fraction of total samples
            t1: Series of label end times (barrier hit times)
        """
        self.n_splits = n_splits
        self.pct_embargo = pct_embargo
        self.t1 = t1
    
    def split(self, X, y=None, groups=None):
        """Generate train/test indices with purging and embargo."""
        indices = np.arange(len(X))
        embargo_size = int(len(X) * self.pct_embargo)
        
        kfold = KFold(n_splits=self.n_splits, shuffle=False)
        
        for train_idx, test_idx in kfold.split(indices):
            test_start = indices[test_idx[0]]
            test_end = indices[test_idx[-1]]
            
            if self.t1 is not None:
                # t1 can be datetime or integer positions
                t1_vals = self.t1.values
                if hasattr(t1_vals[0], 'astype'):  # datetime
                    # Convert t1 to integer positions by mapping to X index
                    t1_idx = np.searchsorted(X.index.values.astype('int64'),
                                            t1_vals[train_idx].astype('int64'), side='right')
                    purge_mask = t1_idx > test_start
                else:
                    purge_mask = t1_vals[train_idx] > test_start
                
                embargo_end = min(test_end + embargo_size, len(X) - 1)
                embargo_mask = indices[train_idx] > embargo_end
                keep_mask = ~purge_mask | embargo_mask
                train_idx = train_idx[keep_mask]
            
            yield train_idx, test_idx


def walk_forward_split(n_samples: int, n_splits: int = 5,
                        min_train_pct: float = 0.5,
                        pct_embargo: float = 0.01) -> list:
    """
    Walk-forward (expanding window) splits.
    Train grows, test always forward. Most realistic for production.
    
    Returns: list of (train_idx, test_idx) tuples
    """
    indices = np.arange(n_samples)
    test_size = int(n_samples * (1 - min_train_pct) / n_splits)
    splits = []
    
    start_test = int(n_samples * min_train_pct)
    
    for i in range(n_splits):
        train_end = start_test + i * test_size
        test_start = train_end
        test_end = min(test_start + test_size, n_samples - 1)
        
        if test_end <= test_start:
            break
        
        train_idx = indices[:train_end]
        test_idx = indices[test_start:test_end]
        
        splits.append((train_idx, test_idx))
    
    return splits


if __name__ == '__main__':
    # Demo
    n = 1000
    X = np.random.randn(n, 5)
    
    pkf = PurgedKFold(n_splits=5, pct_embargo=0.01)
    for i, (train, test) in enumerate(pkf.split(X)):
        print(f"Fold {i}: train={len(train)}, test={len(test)}")
    
    print("\nWalk-forward splits:")
    for i, (train, test) in enumerate(walk_forward_split(n, n_splits=5)):
        print(f"Window {i}: train={len(train)}, test={len(test)}")
