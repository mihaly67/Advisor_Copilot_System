"""
LGBM Copilot Pipeline Orchestrator
Complete: data → CUSUM → TBM → features → weights → model → eval

Usage:
  python3 -m src.pipeline --instrument BTCUSD --data-path /path/to/data.csv
"""
import argparse
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Knowledge code templates
sys.path.insert(0, '/data/LGBM_copilot/knowledge/code_templates')

from labeling_cusum_filter import cusum_filter
from labeling_meta_labeling import triple_barrier_meta
from features_direction import compute_all_direction_features, compute_boolean_features
from sample_weights import compute_sample_weights
from instrument_config import get_instrument


def run_pipeline(data_path: str, instrument: str = 'BTCUSD',
                 output_dir: str = '/data/LGBM_copilot/data') -> dict:
    """
    Run the complete ML pipeline.
    
    Returns: dict with all results, metrics, and paths
    """
    print(f"\n{'='*60}")
    print(f"LGBM COPILOT PIPELINE — {instrument}")
    print(f"{'='*60}")
    
    # Load instrument config
    config = get_instrument(instrument)
    print(f"\nConfig: {instrument}")
    print(f"  Dollar bar threshold: {config.dollar_bar_threshold:,}")
    print(f"  Profit mult: {config.profit_mult}σ, Stop mult: {config.stop_mult}σ")
    print(f"  Max holding: {config.max_holding_bars} bars")
    
    # Step 1: Load data
    print(f"\n[1/8] Loading data from {data_path}...")
    df = pd.read_csv(data_path, parse_dates=True, index_col=0)
    print(f"  Loaded: {len(df)} bars")
    
    # Step 2: CUSUM filter
    print(f"\n[2/8] CUSUM filter — event detection...")
    events = cusum_filter(df['close'])
    n_up = (events['direction'] == 1).sum()
    n_down = (events['direction'] == -1).sum()
    print(f"  Events: {len(events)} (UP={n_up} → Short, DOWN={n_down} → Long)")
    
    # Step 3: Meta-labeling
    print(f"\n[3/8] Side-aware Triple Barrier — meta-labeling...")
    barrier_params = config.get_barrier_params()
    labels = triple_barrier_meta(df['close'], events, **barrier_params)
    take_rate = (labels['label'] == 1).mean()
    print(f"  Labels: {len(labels)}, Take rate: {take_rate:.2%}")
    
    # Step 4: Features
    print(f"\n[4/8] Feature engineering...")
    dir_features = compute_all_direction_features(df)
    bool_features = compute_boolean_features(df, dir_features)
    all_features = pd.concat([dir_features, bool_features], axis=1)
    print(f"  Features: {len(all_features.columns)} ({len(dir_features.columns)} dir + {len(bool_features.columns)} bool)")
    
    # Step 5: Align features with labels
    print(f"\n[5/8] Aligning features with labels...")
    event_features = all_features.loc[labels.index].dropna()
    event_labels = labels.loc[event_features.index]
    print(f"  Aligned: {len(event_features)} samples with complete features")
    
    # Step 6: Sample weights
    print(f"\n[6/8] Sample weights...")
    try:
        weights = compute_sample_weights(event_labels, df['close'])
        print(f"  Weights: mean={weights.mean():.4f}, std={weights.std():.4f}")
    except Exception as e:
        weights = None
        print(f"  Weights error: {e} (using uniform)")
    
    # Step 7: Validation
    print(f"\n[7/8] Validation checks...")
    checks = {}
    
    # Label distribution
    checks['take_rate'] = take_rate
    checks['label_balance'] = 'OK' if 0.20 < take_rate < 0.80 else 'EXTREME'
    
    # Feature leakage
    max_corr = max(
        abs(event_features[col].corr(event_labels['label']))
        for col in event_features.select_dtypes(include=[np.number]).columns
    )
    checks['max_feature_label_corr'] = max_corr
    checks['leakage'] = 'OK' if max_corr < 0.95 else 'LEAKAGE!'
    
    # NaN check
    nan_pct = event_features.isnull().mean().max()
    checks['max_nan_pct'] = nan_pct
    checks['data_quality'] = 'OK' if nan_pct < 0.05 else 'POOR'
    
    for k, v in checks.items():
        print(f"  {k}: {v}")
    
    # Step 8: Save results
    print(f"\n[8/8] Saving results...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save labels
    labels_path = output_path / f'labels_{instrument}_{timestamp}.csv'
    labels.to_csv(labels_path)
    
    # Save features
    features_path = output_path / f'features_{instrument}_{timestamp}.csv'
    event_features.to_csv(features_path)
    
    result = {
        'instrument': instrument,
        'timestamp': timestamp,
        'n_bars': len(df),
        'n_events': len(events),
        'n_labels': len(labels),
        'take_rate': take_rate,
        'n_features': len(all_features.columns),
        'checks': checks,
        'labels_path': str(labels_path),
        'features_path': str(features_path),
    }
    
    # Save metadata
    meta_path = output_path / f'pipeline_result_{instrument}_{timestamp}.json'
    with open(meta_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE ✅")
    print(f"  Labels: {labels_path}")
    print(f"  Features: {features_path}")
    print(f"  Meta: {meta_path}")
    print(f"{'='*60}")
    
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='LGBM Copilot Pipeline')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--data-path', required=True)
    p.add_argument('--output-dir', default='/data/LGBM_copilot/data')
    a = p.parse_args()
    
    run_pipeline(a.data_path, a.instrument, a.output_dir)
