"""
Meta-Labeling Harness — Honest Take/Skip Evaluation

Source: meta-labeling-harness-main (Labelling repo)
Author: efenn-dev

KEY INSIGHT: "The trap is the post-trade judge" — a model that sees the
outcome before deciding is a NARRATOR, not a TRADER. The honest version
uses only pre-entry information (meta-labeling) and evaluates as a trader,
not a classifier.

Anti-patterns prevented:
  - AP02: Using meta-labeling for direction (it's SIZE/bet filter)
  - AP07: Look-ahead bias in features (strict pre-entry wall)
  - AP08: Single-split validation (must use purged walk-forward CV)
  - AP09: Accuracy as objective (use net P&L objective)
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


@dataclass
class DecisionRow:
    """One signal → one decision row.

    CRITICAL: context and label NEVER touch each other.
    - context: only pre-entry features (df[df.index < entry_ts])
    - label: realized forward outcome (never in context)
    """
    regime: str          # market regime at entry
    signal_direction: int  # +1 or -1
    signal_strength: float  # signal confidence
    volatility: float    # recent vol at entry
    rsi: float           # RSI at entry
    bb_width: float      # BB width at entry
    adx: float           # ADX at entry
    fwd_return_net: float  # cost-netted forward return (LABEL)
    label_decision: str    # "take" or "skip" (LABEL)


class MetaLabeler:
    """Secondary model: take/skip on fired signals.

    TWO design choices make it a TRADER not a classifier:
    1. Objective = net P&L (not accuracy)
    2. Cost-aware labels (take must clear the hurdle)
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.model = None

    def fit(self, X_train, y_train, X_val, y_val_ret, min_coverage=0.05):
        from sklearn.ensemble import HistGradientBoostingClassifier
        self.model = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.05, max_depth=4,
            min_samples_leaf=20, l2_regularization=1.0)
        self.model.fit(X_train, y_train)
        p_val = self.model.predict_proba(X_val)[:, 1]
        self.threshold, self.val_stats = self._tune_threshold(p_val, y_val_ret, min_coverage)

    def decide(self, X):
        p = self.model.predict_proba(X)[:, 1]
        return [{"decision": "take" if pi >= self.threshold else "skip",
                 "p_take": round(float(pi), 4)} for pi in p]

    @staticmethod
    def _tune_threshold(probabilities, forward_returns, min_coverage=0.05):
        """Find threshold that maximizes net P&L subject to min coverage."""
        best_th, best_pnl = 0.5, -np.inf
        n = len(probabilities)
        for th in np.arange(0.3, 0.8, 0.01):
            mask = probabilities >= th
            if mask.sum() / n < min_coverage:
                continue
            pnl = forward_returns[mask].sum()
            if pnl > best_pnl:
                best_pnl = pnl
                best_th = th
        stats = {"threshold": best_th, "net_pnl": best_pnl,
                 "coverage": (probabilities >= best_th).mean()}


class PurgedWalkForwardCV:
    """Purged + embargoed walk-forward cross-validation.

    WHY: A naive temporal split leaks because a trade's holding window
    can straddle the train/test boundary. This purges any training
    sample whose holding period reaches past the split, plus an
    embargo to kill serial-correlation leakage.
    """

    def __init__(self, n_folds: int = 5, embargo_days: int = 3):
        self.n_folds = n_folds
        self.embargo_days = embargo_days

    def split(self, X, trade_end_times=None):
        n = len(X)
        fold_size = n // self.n_folds
        for i in range(self.n_folds):
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < self.n_folds - 1 else n
            embargo_start = max(0, test_start - self.embargo_days)
            if trade_end_times is not None:
                test_times = trade_end_times[test_start:test_end]
                purge_mask = trade_end_times[:test_start] > test_times[0]
                train_end = np.searchsorted(purge_mask, True)
            else:
                train_end = embargo_start
            train_idx = np.arange(0, train_end)
            test_idx = np.arange(test_start, test_end)
            if len(train_idx) > 0 and len(test_idx) > 0:
                yield i, (train_idx, test_idx)