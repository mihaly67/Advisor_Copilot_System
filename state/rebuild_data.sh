#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

# 1. Feature engineering v2 (irany-specifikus feature-okkel)
echo "=== FEATURE ENGINEERING V2 ==="
/home/Jules/jules_venv/bin/python3 src/dom_feature_engineer_mtf.py 2>&1 | tail -5

# 2. V6 labeling az uj adatra
echo "=== V6 LABELING ==="
/home/Jules/jules_venv/bin/python3 -c "
import sys, os
sys.path.insert(0, 'src')
from dom_labeler_v6 import apply_triple_barrier
import pandas as pd

inp = 'Master_csv/processed/features_dollar_bars_adaptive.csv'
out = 'Master_csv/processed/labeled_dollar_bars_v6.csv'
df = pd.read_csv(inp)
df['Start_Timestamp'] = pd.to_datetime(df['Start_Timestamp'])
df.sort_values('Start_Timestamp', inplace=True)
df.reset_index(drop=True, inplace=True)
print(f'{len(df):,} sor')
df_l = apply_triple_barrier(df, pt_long=1.2, pt_short=1.2, sl_multiplier=1.0, max_bars=8)
df_l = df_l.iloc[:-8].copy()
dist = df_l['Target_Label'].value_counts(normalize=True) * 100
for label, pct in dist.items():
    name = {1: 'Long', -1: 'Short', 0: 'Noise'}.get(int(label), '?')
    print(f'   {name} ({int(label):+d}): {pct:.1f}%')
short = df_l[df_l['Target_Label'] == -1]
long_ = df_l[df_l['Target_Label'] == 1]
print(f'Short ADX<20: {(short[\"Regime_ADX\"]<20).mean()*100:.1f}%')
print(f'Long ADX<20: {(long_[\"Regime_ADX\"]<20).mean()*100:.1f}%')
df_l.to_csv(out, index=False)
print(f'Mentve: {out}')
" 2>&1

echo "=== KESZ ==="
