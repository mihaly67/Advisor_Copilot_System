"""
LightGBM Training with Financial ML Pipeline
Reference: meta-labeling-harness-main/meta_labeler.py

Pipeline: features + labels + sample_weights → PurgedKFold → LightGBM → OOS eval
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from cross_validation_purged import PurgedKFold, walk_forward_split


def train_meta_model(X: pd.DataFrame, y: pd.Series,
                     sample_weight: np.ndarray = None,
                     n_splits: int = 5, pct_embargo: float = 0.01,
                     t1: pd.Series = None,
                     lgbm_params: dict = None) -> dict:
    """
    Train LightGBM meta-model with PurgedKFold validation.
    
    Args:
        X: Feature DataFrame
        y: Meta-labels (0 or 1)
        sample_weight: Sample weights from compute_sample_weights
        n_splits: Number of CV folds
        pct_embargo: Embargo fraction
        t1: Label end times for purging
        lgbm_params: LightGBM parameters
        
    Returns:
        dict with 'model', 'oos_predictions', 'feature_importance', 'metrics'
    """
    if lgbm_params is None:
        lgbm_params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'n_jobs': -1,
        }
    
    # Purged K-Fold
    pkf = PurgedKFold(n_splits=n_splits, pct_embargo=pct_embargo, t1=t1)
    
    oos_predictions = pd.Series(0.0, index=X.index)
    models = []
    importances = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(pkf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        w_train = None
        if sample_weight is not None:
            w_train = sample_weight[train_idx]
        
        # Class balance
        n_pos = y_train.sum()
        n_neg = len(y_train) - n_pos
        params = lgbm_params.copy()
        if n_pos > 0:
            params['scale_pos_weight'] = n_neg / n_pos
        
        train_data = lgb.Dataset(X_train, label=y_train, weight=w_train)
        
        model = lgb.train(params, train_data, num_boost_round=500,
                         valid_sets=[lgb.Dataset(X_test, label=y_test)],
                         callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
        
        # OOS predictions
        oos_predictions.iloc[test_idx] = model.predict(X_test)
        models.append(model)
        importances.append(pd.Series(model.feature_importance('gain'), index=X.columns))
    
    # Feature importance (average across folds)
    avg_importance = pd.concat(importances, axis=1).mean(axis=1).sort_values(ascending=False)
    
    # Metrics
    from sklearn.metrics import roc_auc_score, accuracy_score
    oos_binary = (oos_predictions > 0.5).astype(int)
    mask = oos_predictions > 0  # only where we have predictions
    
    metrics = {
        'auc': roc_auc_score(y[mask], oos_predictions[mask]) if mask.sum() > 100 else 0,
        'accuracy': accuracy_score(y[mask], oos_binary[mask]),
        'take_rate': y.mean(),
        'predicted_take_rate': oos_binary.mean(),
    }
    
    return {
        'models': models,
        'oos_predictions': oos_predictions,
        'feature_importance': avg_importance,
        'metrics': metrics,
    }


if __name__ == '__main__':
    print("LightGBM meta-model trainer ready")
    print("Usage: result = train_meta_model(X, y, sample_weight, t1=t1)")
