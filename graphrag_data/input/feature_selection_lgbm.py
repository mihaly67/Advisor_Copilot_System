"""
Feature Selection Pipeline — LightGBM + SHAP + Correlation Pruning

Sources:
  - lgbm-feature-selection-main (Labelling repo)
  - meta-labeling-alpha-filter (SHAP analysis module)
  - quant-ohlcv-features (540+ feature catalog)

Anti-patterns prevented:
  - AP04: Using too many noisy features (overfitting)
  - - AP05: Ignoring feature correlation (redundancy)
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
import shap


def shap_feature_importance(
    model: lgb.Booster,
    X: pd.DataFrame,
    top_k: int = 30,
    min_importance: float = 0.01,
) -> list[str]:
    """Select top-K features by mean |SHAP value|.

    Steps:
      1. Compute SHAP values with TreeExplainer (fast for LightGBM)
      2. Mean absolute SHAP per feature = global importance
      3. Drop features below min_importance threshold
      4. Return top-K feature names

    Args:
        model: Trained LightGBM Booster
        X: Feature DataFrame (validation or OOS set)
        top_k: Maximum features to keep
        min_importance: Minimum mean |SHAP| to retain

    Returns:
        List of selected feature names, sorted by importance desc
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Binary classification: shap_values is list [class0, class1]
    if isinstance(shap_values, list):
        sv = shap_values[1]  # positive class
    else:
        sv = shap_values

    mean_abs_shap = np.abs(sv).mean(axis=0)
    importance = pd.Series(mean_abs_shap, index=X.columns)
    importance = importance[importance >= min_importance]
    importance = importance.sort_values(ascending=False)

    return importance.head(top_k).index.tolist()


def correlation_pruning(
    features: list[str],
    X: pd.DataFrame,
    max_corr: float = 0.85,
) -> list[str]:
    """Remove highly correlated features (keep the one with higher variance).

    Iterative: compute correlation matrix, find most correlated pair,
    drop the one with lower variance. Repeat until no pair exceeds max_corr.

    Args:
        features: Feature names to consider
        X: Feature DataFrame
        max_corr: Maximum allowed absolute correlation

    Returns:
        Pruned feature list
    """
    remaining = list(features)
    changed = True

    while changed:
        changed = False
        if len(remaining) < 2:
            break

        corr = X[remaining].corr().abs()
        np.fill_diagonal(corr.values, 0)

        max_val = corr.max().max()
        if max_val > max_corr:
            # Find most correlated pair
            i, j = np.unravel_index(corr.values.argmax(), corr.shape)
            fi, fj = remaining[i], remaining[j]

            # Drop the one with lower variance (less informative)
            var_i = X[fi].var()
            var_j = X[fj].var()
            drop = fi if var_i <= var_j else fj
            remaining.remove(drop)
            changed = True

    return remaining


def select_features(
    model: lgb.Booster,
    X: pd.DataFrame,
    top_k: int = 30,
    min_importance: float = 0.01,
    max_corr: float = 0.85,
) -> tuple[list[str], pd.Series]:
    """Full feature selection pipeline: SHAP importance → correlation pruning.

    Usage:
        selected, importance = select_features(model, X_val, top_k=25)
        X_train_selected = X_train[selected]
        X_val_selected = X_val[selected]

    Returns:
        (selected_features, importance_series)
    """
    # Step 1: SHAP importance ranking
    important = shap_feature_importance(model, X, top_k, min_importance)
    print(f"SHAP selected {len(important)} features (from {X.shape[1]})")

    # Step 2: Correlation pruning
    selected = correlation_pruning(important, X, max_corr)
    print(f"Correlation pruning: {len(important)} → {len(selected)} features")

    # Return importance for selected features
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    if isinstance(sv, list):
        sv = sv[1]
    importance = pd.Series(np.abs(sv).mean(axis=0), index=X.columns)

    return selected, importance[selected]


def multitimeframe_feature_names(
    base_features: list[str],
    timeframes: list[str] = ["1m", "5m", "15m", "1h"],
) -> list[str]:
    """Generate multi-timeframe feature names for quant-ohlcv-features.

    quant-ohlcv-features provides 540+ indicators across 7 categories.
    This function generates the column names for multi-TF application.

    Categories (540+ total):
      momentum: 240 (RSI, MACD, Stochastic, CCI, ROC, Bias, MTM, DBCD)
      trend:    73  (EMA, SMA, DEMA, TEMA, ADX, Aroon, Ichimoku)
      volatility: 107 (BB, Keltner, Donchian, ATR, CV, UVL)
      volume:   82  (OBV, MFI, A/D, WVAD, CMF, VPVR)
      price:    19  (VWAP, typical, weighted close)
      liquidity: 8  (Amihud, market placement, illiquidity)
      composite: 11 (momentum×volatility, ADX+MTM, sentiment)

    Usage:
        all_features = multitimeframe_feature_names(
            ["rsi_14", "macd_12_26", "bb_upper_20", "obv"],
            timeframes=["1m", "5m", "15m"]
        )
        # → ["rsi_14_1m", "macd_12_26_1m", ..., "obv_15m"]
    """
    return [f"{f}_{tf}" for tf in timeframes for f in base_features]
