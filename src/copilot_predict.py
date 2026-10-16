"""
Real-time Copilot Predictor
Called by EA: receives MTF indicators → returns P(Take) + signal
Usage: python3 copilot_predict.py --instrument BTCUSD --rsi 45.2 --atr 300.5 ...
  OR: python3 copilot_predict.py --stdin < json_data
"""
import sys, json, numpy as np, pandas as pd
from pathlib import Path

MODEL_DIR = Path('/data/LGBM_copilot/models')


def load_model_and_meta(instrument='BTCUSD'):
    """Load latest MTF model + metadata."""
    import lightgbm as lgb
    
    metas = sorted(MODEL_DIR.glob(f'{instrument}_mtf_meta_*.json'))
    models = sorted(MODEL_DIR.glob(f'{instrument}_mtf_model_*.txt'))
    
    if not metas or not models:
        raise FileNotFoundError(f"No model for {instrument}")
    
    with open(metas[-1]) as f:
        meta = json.load(f)
    model = lgb.Booster(model_file=str(models[-1]))
    
    return model, meta


def compute_features_from_ea(ea_data: dict) -> dict:
    """Compute ML features from EA MTF indicators."""
    bid = ea_data.get('bid', 0)
    ask = ea_data.get('ask', 0)
    mid = (bid + ask) / 2
    spread = ea_data.get('spread', ask - bid)
    atr = ea_data.get('atr_m15', mid * 0.003)  # fallback
    
    feat = {}
    
    # MTF distances
    for tf in ['1m_close', '5m_close', '15m_close', '30m_close']:
        if tf in ea_data and ea_data[tf] > 0:
            feat[f'dist_{tf}'] = (mid - ea_data[tf]) / (atr + 1e-10)
        else:
            feat[f'dist_{tf}'] = 0
    
    feat['atr_pct'] = atr / mid if mid > 0 else 0
    
    # RSI
    rsi = ea_data.get('rsi_m15', 50)
    feat['rsi'] = rsi / 100
    feat['rsi_oversold'] = 1 if rsi < 30 else 0
    feat['rsi_overbought'] = 1 if rsi > 70 else 0
    feat['rsi_mid_signal'] = 1 if 40 <= rsi <= 60 else 0
    
    # S/R distances
    for level in ['micro_r', 'sec_r', 'ter_r', 'micro_s', 'sec_s', 'ter_s']:
        if level in ea_data and ea_data[level] > 0:
            feat[f'dist_{level}'] = (mid - ea_data[level]) / (atr + 1e-10)
        else:
            feat[f'dist_{level}'] = 0
    
    # Position between S/R
    for prefix in ['micro', 'sec', 'ter']:
        r_val = ea_data.get(f'{prefix}_r', 0)
        s_val = ea_data.get(f'{prefix}_s', 0)
        rng = r_val - s_val
        if abs(rng) > 1e-6:
            feat[f'{prefix}_pos'] = (mid - s_val) / rng
            feat[f'{prefix}_width'] = rng / (atr + 1e-10)
        else:
            feat[f'{prefix}_pos'] = 0.5
            feat[f'{prefix}_width'] = 0
    
    feat['spread_atr'] = spread / (atr + 1e-10)
    
    # Returns (need history — use EA-provided or default 0)
    for lag in [1, 2, 3, 5, 10, 20]:
        feat[f'ret_{lag}'] = ea_data.get(f'ret_{lag}', 0)
    for lag in [5, 10, 20]:
        feat[f'rvol_{lag}'] = ea_data.get(f'rvol_{lag}', 0)
    for lag in [10, 20]:
        feat[f'pos_{lag}'] = ea_data.get(f'pos_{lag}', 0.5)
    
    feat['vol_ratio'] = ea_data.get('vol_ratio', 1.0)
    
    return feat


def predict(ea_data: dict, instrument='BTCUSD', threshold=0.52) -> dict:
    """Full prediction: side model + meta model → signal."""
    model, meta = load_model_and_meta(instrument)
    feature_names = meta['feature_names']
    
    # Compute features
    feat = compute_features_from_ea(ea_data)
    
    # Build feature vector in correct order
    X = pd.DataFrame([{fn: feat.get(fn, 0) for fn in feature_names}])
    
    # Predict
    prob_take = model.predict(X)[0]
    
    # Side model
    rsi = ea_data.get('rsi_m15', 50)
    rsi_prev = ea_data.get('rsi_m15_prev', 50)
    
    side = 0
    if rsi < 30 or (rsi < 40 and rsi_prev >= 40):
        side = 1  # Long
    elif rsi > 70 or (rsi > 60 and rsi_prev <= 60):
        side = -1  # Short
    
    # Signal
    signal = 0
    if side == 1 and prob_take > threshold:
        signal = 1  # Take Long
    elif side == -1 and prob_take > threshold:
        signal = -1  # Take Short
    
    return {
        'side': side,
        'prob_take': float(prob_take),
        'signal': signal,
        'threshold': threshold,
        'atr': ea_data.get('atr_m15', 0),
    }


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--stdin', action='store_true')
    p.add_argument('--threshold', type=float, default=0.52)
    a = p.parse_args()
    
    if a.stdin:
        ea_data = json.load(sys.stdin)
    else:
        # Demo with default values
        ea_data = {
            'bid': 86000, 'ask': 86005, 'spread': 5,
            '1m_close': 85990, '5m_close': 85950, '15m_close': 85880, '30m_close': 85800,
            'atr_m15': 300, 'rsi_m15': 35, 'rsi_m15_prev': 42,
            'micro_r': 86200, 'sec_r': 86500, 'ter_r': 87000,
            'micro_s': 85800, 'sec_s': 85500, 'ter_s': 85000,
        }
    
    result = predict(ea_data, a.instrument, a.threshold)
    print(json.dumps(result, indent=2))