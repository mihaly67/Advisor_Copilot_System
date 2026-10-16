"""
Signal Quality Templates for Scalper Copilot
Source: CSA-15 (multi-confirmation 6/8), EURUSD_Scalper (7-indicator scoring 4/7), BAKOME (ICT confluence)
Purpose: Multi-confirmation scoring, fresh trigger, cooldown — signal quality filters
"""
import numpy as np
import pandas as pd


def multi_confirmation_score(features: pd.DataFrame,
                              feature_weights: dict = None,
                              min_score: float = 0.6) -> pd.Series:
    """
    Multi-Confirmation Scoring — CSA-15 (8-point, min 6) + EURUSD (7-point, min 4)
    
    Each feature contributes 0 or 1 point (weighted). Signal only if score >= min_score.
    
    CSA-15: 8 conditions, min 6/8 = 0.75 threshold
    EURUSD: 7 indicators, min 4/7 = 0.57 threshold
    
    Default: 0.6 (between the two)
    """
    if feature_weights is None:
        # Default weights — based on advisor repo analysis
        feature_weights = {
            'fvg_bull_active': 1.0, 'fvg_bear_active': 1.0,
            'ob_bullish': 0.8, 'ob_bearish': 0.8,
            'poc_as_support': 0.9, 'poc_as_resistance': 0.9,
            'in_kill_zone': 0.7,
            'htf_bullish': 0.8, 'htf_bearish': 0.8,
            'liq_sweep_low': 0.7, 'liq_sweep_high': 0.7,
            'micro_sqz': 0.6,
        }
    
    score = pd.Series(0.0, index=features.index)
    total_weight = 0.0
    
    for feat, weight in feature_weights.items():
        if feat in features.columns:
            score += features[feat].astype(float) * weight
            total_weight += weight
    
    if total_weight > 0:
        score = score / total_weight  # normalize to [0, 1]
    
    return score


def fresh_trigger(signal: pd.Series, cooldown_bars: int = 3) -> pd.Series:
    """
    Fresh Trigger — CSA-15: Signal only on FIRST bar of new condition.
    
    Prevents signal repetition: after a signal, ignore same-direction signals
    for cooldown_bars bars.
    
    This is CRITICAL for scalping — without it, model generates the same
    signal on every bar in a trending move.
    """
    n = len(signal)
    fresh = np.zeros(n, dtype=bool)
    last_signal_bar = -cooldown_bars - 1  # allow first signal
    
    for i in range(n):
        if signal.iloc[i]:
            if (i - last_signal_bar) > cooldown_bars:
                fresh[i] = True
                last_signal_bar = i
    
    return pd.Series(fresh, index=signal.index)


def signal_cooldown(signals: pd.Series, min_bars_between: int = 5) -> pd.Series:
    """
    Signal Cooldown — CSA-15: Minimum bars between signals.
    
    After a signal, no new signals for min_bars_between bars.
    Prevents overtrading.
    """
    n = len(signals)
    filtered = np.zeros(n, dtype=bool)
    last_bar = -min_bars_between - 1
    
    for i in range(n):
        if signals.iloc[i] and (i - last_bar) >= min_bars_between:
            filtered[i] = True
            last_bar = i
    
    return pd.Series(filtered, index=signals.index)


def generate_signal_quality(model_proba: pd.Series, features: pd.DataFrame,
                            threshold: float = 0.5,
                            min_confirmation: float = 0.6,
                            cooldown: int = 3) -> pd.DataFrame:
    """
    Full signal quality pipeline:
    1. Model probability > threshold → raw signal
    2. Multi-confirmation score >= min_confirmation → confirmed
    3. Fresh trigger → no repetition
    4. Cooldown → no overtrading
    
    Returns: raw_signal, confirmed, fresh, final_signal
    """
    raw = (model_proba > threshold).astype(int)
    conf_score = multi_confirmation_score(features, min_score=min_confirmation)
    confirmed = raw & (conf_score >= min_confirmation).astype(int)
    fresh = fresh_trigger(confirmed, cooldown_bars=cooldown)
    final = signal_cooldown(fresh, min_bars_between=cooldown * 2)
    
    return pd.DataFrame({
        'raw_signal': raw,
        'confirmation_score': conf_score,
        'confirmed': confirmed,
        'fresh_signal': fresh,
        'final_signal': final,
    })

# Based on: CSA-15 (8-point min 6) + EURUSD_Scalper (7-point min 4) + BAKOME ICT confluence
