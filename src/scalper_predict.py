"""
Scalper Real-time Predictor — P(Long), P(Short) every tick
Called by EA: receives MTF indicators → returns P(Long), P(Short), signal
Usage: echo '{"bid":86000,"ask":86005,...}' | python3 scalper_predict.py --stdin
"""
import json, numpy as np, pandas as pd
from pathlib import Path

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')


def load_scalper_models(instrument='BTCUSD'):
    import lightgbm as lgb
    metas = sorted(MODEL_DIR.glob(f'{instrument}_scalper_meta_*.json'))
    longs = sorted(MODEL_DIR.glob(f'{instrument}_scalper_long_*.txt'))
    shorts = sorted(MODEL_DIR.glob(f'{instrument}_scalper_short_*.txt'))
    if not metas or not longs or not shorts:
        raise FileNotFoundError(f"No scalper models for {instrument}")
    with open(metas[-1]) as f: meta = json.load(f)
    long_model = lgb.Booster(model_file=str(longs[-1]))
    short_model = lgb.Booster(model_file=str(shorts[-1]))
    return long_model, short_model, meta


def compute_features_from_ea(ea: dict) -> dict:
    """Compute features from EA MTF tick data."""
    bid = ea.get('bid', 0)
    ask = ea.get('ask', 0)
    mid = (bid + ask) / 2
    spread = ea.get('spread', ask - bid)
    atr = ea.get('atr_m15', mid * 0.003)
    f = {}
    for tf in ['1m_close', '5m_close', '15m_close', '30m_close']:
        f[f'd_{tf}'] = (mid - ea.get(tf, mid)) / (85823.01 + 1e-10) if tf in ea else 0
    f['atr_pct'] = atr / mid if mid > 0 else 0
    rsi = ea.get('rsi_m15', 50)
    f['rsi_n'] = (rsi - 50) / 50
    f['rsi_os'] = 1 if rsi < 30 else 0
    f['rsi_ob'] = 1 if rsi > 70 else 0
    f['rsi_mom'] = ea.get('rsi_mom', 0)
    for lv in ['micro_r', 'sec_r', 'ter_r', 'micro_s', 'sec_s', 'ter_s']:
        f[f'd_{lv}'] = (mid - ea.get(lv, mid)) / (atr + 1e-10) if lv in ea else 0
    for px in ['micro', 'sec', 'ter']:
        rv, sv = ea.get(f'{px}_r', 0), ea.get(f'{px}_s', 0)
        rng = rv - sv
        f[f'{px}_pos'] = (mid - sv) / (rng + 1e-10) if abs(rng) > 1e-6 else 0.5
        f[f'{px}_sqz'] = atr / (rng + 1e-10) if abs(rng) > 1e-6 else 0
    f['sp_atr'] = spread / (atr + 1e-10)
    bv, av = ea.get('bid_volume', 0), ea.get('ask_volume', 0)
    f['vol_imb'] = (bv - av) / (bv + av + 1e-10)
    f['vol_tot'] = np.log1p(bv + av)
    for lag in [1, 3, 5, 10, 20]: f[f'ret_{lag}'] = ea.get(f'ret_{lag}', 0)
    for lag in [10, 20, 60]: f[f'tv_{lag}'] = ea.get(f'tv_{lag}', 0)
    for lag in [20, 60]: f[f'tsk_{lag}'] = ea.get(f'tsk_{lag}', 0)
    for lag in [20, 60]: f[f'rpos_{lag}'] = ea.get(f'rpos_{lag}', 0.5)
    f['mtf_al'] = ea.get('mtf_al', 0)
    return f


def predict_scalper(ea: dict, instrument='BTCUSD') -> dict:
    """Predict P(Long), P(Short) from EA tick data."""
    long_m, short_m, meta = load_scalper_models(instrument)
    feat = compute_features_from_ea(ea)
    fn = meta['feature_names']
    X = pd.DataFrame([{n: feat.get(n, 0) for n in fn}])
    p_long = float(long_m.predict(X)[0])
    p_short = float(short_m.predict(X)[0])
    lt = meta.get('long_thr', 0.5)
    st = meta.get('short_thr', 0.5)
    signal = 0
    if p_long > lt and p_long > p_short: signal = 1   # Long
    elif p_short > st and p_short > p_long: signal = -1  # Short
    return {'p_long': p_long, 'p_short': p_short, 'signal': signal,
            'long_thr': lt, 'short_thr': st, 'net': p_long - p_short}


if __name__ == '__main__':
    import argparse, sys
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--stdin', action='store_true')
    a = p.parse_args()
    if a.stdin:
        ea = json.load(sys.stdin)
    else:
        ea = {'bid': 86000, 'ask': 86005, 'spread': 5,
              '1m_close': 85990, '5m_close': 85950, '15m_close': 85880, '30m_close': 85800,
              'atr_m15': 300, 'rsi_m15': 35,
              'micro_r': 86200, 'sec_r': 86500, 'ter_r': 87000,
              'micro_s': 85800, 'sec_s': 85500, 'ter_s': 85000,
              'bid_volume': 28, 'ask_volume': 32}
    print(json.dumps(predict_scalper(ea, a.instrument), indent=2))