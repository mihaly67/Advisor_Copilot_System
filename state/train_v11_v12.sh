#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

# V11: 20 feature (v10_pruned volt 10, kell kulon 20-as)
# Elso generaljunk egy 20-as feature listat
/home/Jules/jules_venv/bin/python3 -c "
import pandas as pd
df = pd.read_csv('models/v10/shap_importance.csv').sort_values('SHAP_Total', ascending=False)
top20 = df.head(20)['feature'].tolist()
with open('models/v10/features_top20.txt', 'w') as f:
    for feat in top20:
        f.write(feat + '\n')
print('Top 20 mentve')
print(top20)
"

# V11: top 20 feature
echo '=== V11: top 20 ==='
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v11 \
    --data Master_csv/processed/labeled_dollar_bars_v6.csv \
    --features models/v10/features_top20.txt \
    2>&1 | tail -25

# V12: top 10 feature (v10_pruned mar megvan)
echo '=== V12: top 10 ==='
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v12 \
    --data Master_csv/processed/labeled_dollar_bars_v6.csv \
    --features models/v10_pruned/features.txt \
    2>&1 | tail -25
