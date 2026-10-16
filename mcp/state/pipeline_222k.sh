#!/usr/bin/env bash
set -e
cd /data/dev/projects/z-ai-copilot
PY=/home/Jules/jules_venv/bin/python3

echo "╔══════════════════════════════════════════════════╗"
echo "║  PIPELINE: \$222K threshold + Kelly sizing         ║"
echo "╚══════════════════════════════════════════════════╝"

BASE=/data/dev/projects/z-ai-copilot
RAW=$BASE/Master_csv/raw/Scalper_Copilot_MTF_Data.csv
PROC=$BASE/Master_csv/processed

# 1. Dollar bars $222K threshold
echo ""
echo "=== 1. Dollar Bars (\$222K threshold) ==="
$PY src/prado_dollar_bars.py --threshold 222000 2>&1 | tail -8

# 2. Feature engineering
echo ""
echo "=== 2. Feature Engineering ==="
$PY src/dom_feature_engineer_mtf.py $PROC/dollar_bars_thr222k.csv 2>&1 | tail -5

# A feature engineer 'features_' prefixet rak — keressuk meg
FEAT_FILE=$PROC/features_dollar_bars_thr222k.csv
if [ ! -f "$FEAT_FILE" ]; then
    FEAT_FILE=$PROC/features_thr222k.csv
fi
if [ ! -f "$FEAT_FILE" ]; then
    echo "HIBA: feature file nem talalhato!"
    ls -la $PROC/*222* 2>/dev/null
    exit 1
fi
echo "Feature file: $FEAT_FILE"

# 3. V6 labeling (triple barrier)
echo ""
echo "=== 3. V6 Labeling (triple barrier) ==="
$PY -c "
import sys, os
sys.path.insert(0, 'src')
import dom_labeler_v6 as mod
import pandas as pd, numpy as np

inp = '$FEAT_FILE'
out = '$PROC/labeled_dollar_bars_v6_thr222k.csv'
df = pd.read_csv(inp)
df['Start_Timestamp'] = pd.to_datetime(df['Start_Timestamp'])
df.sort_values('Start_Timestamp', inplace=True)
df.reset_index(drop=True, inplace=True)
print(f'   {len(df):,} sor')
df = mod.apply_triple_barrier(df, pt_long=1.2, pt_short=1.2, sl=1.0, max_bars=8)
df = df.iloc[:-8].copy()
dist = df['Target_Label'].value_counts(normalize=True) * 100
print('Label eloszlas:')
for k, v in dist.items():
    name = {-1: 'Short', 0: 'Noise', 1: 'Long'}.get(int(k), '?')
    print(f'  {name} ({int(k):+d}): {v:.1f}%')
df.to_csv(out, index=False)
print(f'Mentve: {out} ({len(df):,} sor)')
" 2>&1 | tail -12

# 4. V8 meta-labeling
echo ""
echo "=== 4. V8 Meta-Labeling ==="
$PY -c "
import sys, os
sys.path.insert(0, 'src')
import dom_labeler_v8 as mod
import pandas as pd

inp = '$FEAT_FILE'
out = '$PROC/labeled_dollar_bars_v8_thr222k.csv'
df = pd.read_csv(inp)
print(f'   {len(df):,} sor, {len(df.columns)} oszlop')
df = mod.apply_meta_labeling(df, pt_usd=1.2, sl_usd=1.0, max_bars=8)
df = df.iloc[:-8].copy()
total = len(df)
trade = (df['Target_Meta'] == 1).sum()
print(f'Trade(1): {trade} ({trade/total*100:.1f}%)')
print(f'Pass(0):  {total-trade} ({(total-trade)/total*100:.1f}%)')
df.to_csv(out, index=False)
print(f'Mentve: {out} ({len(df):,} sor)')
" 2>&1 | tail -8

# 5. Train meta-model (30 feature)
echo ""
echo "=== 5. Meta-Model Training (30 feature, \$222K) ==="
$PY src/train_lgbm_meta.py \
    --version meta_v3_222k \
    --data $PROC/labeled_dollar_bars_v8_thr222k.csv \
    --features models/v17/features_top30.txt \
    2>&1 | tail -25

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  PIPELINE KÉSZ!                                    ║"
echo "╚══════════════════════════════════════════════════╝"
