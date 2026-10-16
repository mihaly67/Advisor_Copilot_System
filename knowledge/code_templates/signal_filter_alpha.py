"""
Signal Filter + Position Sizing — Alpha Filter Pipeline

Source: meta-labeling-alpha-filter (Labelling repo)
Author: Gautier Petit

KEY IDEAS:
  1. "Filter first, trade second" — predict resolution, not direction
  2. "Calibration before control" — decisions ride on calibrated probs
  3. "Stack on probabilities, not features" — convex blender
  4. "Execution hygiene" — close→next-close, asymmetric costs, vol target

Proven results (Fold-3 OOS, 2020-2024):
  - Meta-labeled: 12.17% return @ 19.51% vol, Sharpe 0.62
  - 50/50 SPY blend: 14.64% return @ 13.43% vol, Sharpe 1.09
  - Trade quality: 3612 trades, 65.75% win, PF 2.92

Anti-patterns prevented: AP02 (meta=SIZE), AP15 (overtrading)
"""
import numpy as np
import pandas as pd


def filter_signals_with_meta_model(
    signals, meta_clf, X,
    th_long=0.45, th_short=0.50, min_gap=0.10, top_k_per_day=3,
):
    """Filter candidate signals using trained meta-classifier.

    Steps: predict P(take) → side-specific threshold → min_gap → top-K/day
    """
    filtered = pd.DataFrame(0, index=signals.index, columns=signals.columns)
    stacked = signals.stack()
    entry_mask = stacked.ne(0)
    signal_idx = stacked.loc[entry_mask].index
    valid_idx = signal_idx.intersection(X.index)
    if len(valid_idx) == 0:
        return filtered
    X_valid = X.loc[valid_idx]
    probs = np.asarray(meta_clf.predict_proba(X_valid))

    for i, idx in enumerate(valid_idx):
        signal = int(stacked.loc[idx])
        p = probs[i]
        th = th_long if signal > 0 else th_short
        p_take = p[-1]
        p_competing = max(p[0], p[1])
        if p_take >= th and (p_take - p_competing) >= min_gap:
            filtered.at[idx] = signal

    # Top-K per day

def probability_weighted_sizing(
    filtered_signals, meta_clf, X, returns,
    weight_mode="margin", target_vol=0.20, vol_span=63, leverage_cap=3.0,
):
    """Compute probability-weighted position sizes.

    Weight modes:
      "prob": weight = signal * P(take)
      "margin": weight = signal * max(0, P(take) - max(P(skip), P(fade)))
      "odds": weight = signal * tanh(0.5 * logit(P(take)))
    Then: vol targeting (EWMA) -> leverage cap
    Returns: (weights_exec, net_returns)
    """
    proba = np.asarray(meta_clf.predict_proba(X))
    p_take = proba[:, -1]
    p_skip = proba[:, 0]
    p_fade = proba[:, 1] if proba.shape[1] > 2 else np.zeros_like(p_take)
    signal_values = filtered_signals.stack().reindex(X.index).fillna(0).values

    if weight_mode == "margin":
        margin = np.maximum(0.0, p_take - np.maximum(p_skip, p_fade))
        raw_w = signal_values * margin
    elif weight_mode == "odds":
        eps = 1e-6
        p = np.clip(p_take, eps, 1 - eps)
        raw_w = signal_values * np.tanh(0.5 * (np.log(p) - np.log(1 - p)))
    else:
        raw_w = signal_values * p_take

    weights = pd.Series(raw_w, index=X.index).unstack().reindex_like(filtered_signals).fillna(0)
    row_sums = weights.abs().sum(axis=1).replace(0, np.nan)
    weights = weights.div(row_sums, axis=0).fillna(0)

    if target_vol > 0:
        vol = returns.std(axis=1).ewm(span=vol_span).std() * np.sqrt(252)
        weights = weights.mul((target_vol / vol).clip(0.1, 5.0), axis=0)
    if leverage_cap > 0:
        gross = weights.abs().sum(axis=1)
        over = gross > leverage_cap
        if over.any():
            weights.loc[over] = weights.loc[over].mul(leverage_cap / gross[over], axis=0)

    return weights, (weights.shift(1) * returns).sum(axis=1)
    if top_k_per_day > 0:
        day_mask = filtered.ne(0).any(axis=1)
        for dt in filtered.index[day_mask]:
            row = filtered.loc[dt]
            cols = row.index[row != 0]
            if len(cols) > top_k_per_day:
                keep = cols[:top_k_per_day]  # simplified
                for c in cols:
                    if c not in keep:
                        filtered.at[(dt, c)] = 0
    return filtered