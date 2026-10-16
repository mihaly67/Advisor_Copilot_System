"""
Model Selection Pipeline for Scalper Copilot
Source: MlFinLab (meta-labeling), EA31337 (ensemble), CSA-15 (scoring)
Purpose: Meta-labeling pipeline, ensemble voting, threshold optimization
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def meta_labeling_pipeline(side_model, size_model,
                           X: pd.DataFrame, y_side: pd.Series,
                           threshold_size: float = 0.55) -> pd.DataFrame:
    """
    Meta-Labeling Pipeline — MlFinLab AFML Ch.3
    
    Stage 1: side_model predicts direction (+1 Long / -1 Short)
    Stage 2: size_model predicts take (1) or skip (0) given direction
    
    CRITICAL: meta-labeling is SIZE FILTER, NOT direction!
    - side_model labels: +1/-1 from Triple Barrier
    - size_model labels: 1 if TP hit, 0 if SL/timeout (given side)
    - Final: trade only if side_model AND size_model agree
    
    Asymmetric barriers: profit_mult > stop_mult (e.g., 1.5σ vs 1.0σ)
    """
    # Stage 1: direction
    side_proba = side_model.predict_proba(X)[:, 1]
    side_pred = np.where(side_proba > 0.5, 1, -1)  # +1 Long, -1 Short
    
    # Stage 2: bet sizing (given direction)
    size_proba = size_model.predict_proba(X)[:, 1]
    size_pred = (size_proba > threshold_size).astype(int)  # 1=take, 0=skip
    
    # Combined: trade only if size_model says take
    final_signal = side_pred * size_pred  # +1, -1, or 0 (no trade)
    
    return pd.DataFrame({
        'side_proba': side_proba,
        'side_pred': side_pred,
        'size_proba': size_proba,
        'size_pred': size_pred,
        'final_signal': final_signal,
        'position_size': size_proba * size_pred,  # confidence-weighted sizing
    })


def ensemble_vote(predictions: list, weights: list = None,
                  min_agreement: float = 0.6) -> pd.Series:
    """
    Ensemble Voting — EA31337: multiple strategies vote independently
    
    predictions: list of pd.Series with +1/-1/0 predictions
    weights: performance-based weights (adaptive)
    min_agreement: fraction of models that must agree (EA31337 uses simple majority)
    
    Weighted vote → signal if agreement >= min_agreement
    """
    if weights is None:
        weights = [1.0] * len(predictions)
    
    vote_matrix = pd.concat(predictions, axis=1)
    n_models = len(predictions)
    
    # Weighted sum of votes
    weighted_sum = sum(w * p for w, p in zip(weights, predictions))
    total_weight = sum(weights)
    
    # Agreement: fraction of models voting same direction
    bullish_votes = sum(w * (p > 0).astype(float) for w, p in zip(weights, predictions))
    bearish_votes = sum(w * (p < 0).astype(float) for w, p in zip(weights, predictions))
    
    bullish_agreement = bullish_votes / total_weight
    bearish_agreement = bearish_votes / total_weight
    
    # Signal direction based on weighted sum
    signal = np.where(
        (weighted_sum > 0) & (bullish_agreement >= min_agreement), 1,
        np.where(
            (weighted_sum < 0) & (bearish_agreement >= min_agreement), -1, 0
        )
    )
    
    return pd.Series(signal, index=predictions[0].index)


def optimize_threshold(y_true: pd.Series, y_proba: pd.Series,
                       metric: str = 'profit',
                       thresholds: np.ndarray = None) -> dict:
    """
    Threshold Optimization for Scalper Copilot
    
    Methods:
    - 'profit': maximize OOS profit (grid search)
    - 'f1': maximize F1 score
    - 'youden': maximize (tpr - fpr) on ROC
    - 'side_aware': different threshold for long/short
    """
    if thresholds is None:
        thresholds = np.arange(0.35, 0.75, 0.01)
    
    best_thresh = 0.5
    best_score = -np.inf
    results = []
    
    for thresh in thresholds:
        y_pred = (y_proba > thresh).astype(int)
        
        if metric == 'f1':
            from sklearn.metrics import f1_score
            score = f1_score(y_true, y_pred, zero_division=0)
        elif metric == 'youden':
            from sklearn.metrics import confusion_matrix
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            score = tpr - fpr
        else:  # profit: assume 2:1 reward:risk
            from sklearn.metrics import confusion_matrix
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
            score = tp * 2 - fp  # 2R profit per TP, 1R loss per FP
        
        results.append({'threshold': thresh, 'score': score})
        if score > best_score:
            best_score = score
            best_thresh = thresh
    
    return {
        'best_threshold': best_thresh,
        'best_score': best_score,
        'all_results': results,
    }

# Based on: MlFinLab meta-labeling + EA31337 ensemble + CSA-15 scoring
