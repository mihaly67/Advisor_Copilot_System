#!/usr/bin/env python3
"""Short diagnosztika V5 — labeling + feature + predikcio vizsgalat"""
import sys, os
import pandas as pd
import numpy as np

# Projekt gyoker
base = '/data/dev/projects/z-ai-copilot'
os.chdir(base)
sys.path.insert(0, os.path.join(base, 'src'))

# Adat betoltese
csv_path = os.path.join(base, 'Master_csv', 'processed', 'labeled_dollar_bars_adaptive.csv')
df = pd.read_csv(csv_path)
print(f'=== OSSZES BAR: {len(df)} ===')

# Label eloszlás
print(f'\n=== LABEL ELOSZLAS ===')
vc = df['Target_Label'].value_counts().sort_index()
for k, v in vc.items():
    print(f'  {int(k):+d}: {v} ({v/len(df)*100:.1f}%)')

# ADX statisztika
adx = df['Regime_ADX']
print(f'\n=== REGIME_ADX STAT ===')
print(f'  mean={adx.mean():.1f} median={adx.median():.1f}')
print(f'  ADX<20: {(adx<20).sum()} ({(adx<20).mean()*100:.1f}%)')
print(f'  ADX>=20: {(adx>=20).sum()} {(adx>=20).mean()*100:.1f}%)')

# Short/Long/Noise bontas
short = df[df['Target_Label'] == -1]
long_ = df[df['Target_Label'] == 1]
noise = df[df['Target_Label'] == 0]
print(f'\n=== ADX LABEL SZERINT ===')
print(f'  Short (n={len(short)}): ADX mean={short["Regime_ADX"].mean():.1f} <20: {(short["Regime_ADX"]<20).sum()} ({(short["Regime_ADX"]<20).mean()*100:.1f}%)')
print(f'  Long  (n={len(long_)}): ADX mean={long_["Regime_ADX"].mean():.1f} <20: {(long_["Regime_ADX"]<20).sum()}')
print(f'  Noise (n={len(noise)}): ADX mean={noise["Regime_ADX"].mean():.1f} <20: {(noise["Regime_ADX"]<20).sum()}')

# V5 features
feat_path = os.path.join(base, 'models', 'v5', 'features.txt')
with open(feat_path) as f:
    features = [l.strip() for l in f if l.strip()]
print(f'\n=== V5 FEATURES ({len(features)}) ===')
for ft in features:
    print(f'  {ft}')

# V5 modell betoltese
import joblib
model_path = os.path.join(base, 'models', 'v5', 'model.pkl')
model = joblib.load(model_path)
print(f'\n=== MODELL BETOLTVE ===')
print(f'  Classes: {model.classes_}')

# OOS predikcio
split = int(len(df) * 0.8)
test = df.iloc[split:].copy()
print(f'\n=== OOS TEST SET: {len(test)} bar ===')

probs = model.predict_proba(test[features])
cls = model.classes_
idx_s = list(cls).index(0)  # 0 = Short (y+1 mapping: -1->0, 0->1, 1->2)
idx_n = list(cls).index(1)  # Noise
idx_l = list(cls).index(2)  # Long

test['P_S'] = probs[:, idx_s]
test['P_N'] = probs[:, idx_n]
test['P_L'] = probs[:, idx_l]

# True Short barokon predikcio
ts = test[test['Target_Label'] == -1]
tl = test[test['Target_Label'] == 1]
tn = test[test['Target_Label'] == 0]
print(f'\n=== V5 PREDIKCIO OOS ===')
print(f'True Short (n={len(ts)}):')
print(f'  P(Short) mean={ts["P_S"].mean():.3f} P(Noise) mean={ts["P_N"].mean():.3f} P(Long) mean={ts["P_L"].mean():.3f}')
print(f'  P(L)>P(S): {(ts["P_L"]>ts["P_S"]).sum()}/{len(ts)} ({(ts["P_L"]>ts["P_S"]).mean()*100:.1f}%)')
print(f'  Predicted class distribution:')
pred_ts = model.predict(test[features][test['Target_Label'] == -1])
for c in [-1, 0, 1]:
    cnt = (pred_ts == (c + 1)).sum()
    print(f'    {c:+d}: {cnt} ({cnt/len(ts)*100:.1f}%)')

print(f'\nTrue Long (n={len(tl)}):')
print(f'  P(Long) mean={tl["P_L"].mean():.3f} P(Short) mean={tl["P_S"].mean():.3f}')
print(f'  P(L)>P(S): {(tl["P_L"]>tl["P_S"]).sum()}/{len(tl)} ({(tl["P_L"]>tl["P_S"]).mean()*100:.1f}%)')
pred_tl = model.predict(test[features][test['Target_Label'] == 1])
for c in [-1, 0, 1]:
    cnt = (pred_tl == (c + 1)).sum()
    print(f'    {c:+d}: {cnt} ({cnt/len(tl)*100:.1f}%)')

# Feature diszkriminacio Short vs Long
print(f'\n=== FEATURE DISZKRIMINACIO (Short vs Long, teljes adat) ===')
for ft in features:
    s_mean = short[ft].mean()
    l_mean = long_[ft].mean()
    pooled_std = np.sqrt((short[ft].std()**2 + long_[ft].std()**2) / 2)
    cohen_d = (s_mean - l_mean) / (pooled_std + 1e-9)
    print(f'  {ft:25s} Short={s_mean:+.3f} Long={l_mean:+.3f} d={cohen_d:+.3f}')

# SHAP importalas
shap_path = os.path.join(base, 'models', 'v5', 'shap_importance.csv')
if os.path.exists(shap_path):
    shap_df = pd.read_csv(shap_path)
    print(f'\n=== SHAP IMPORTANCE (V5) ===')
    print(shap_df.to_string(index=False))

# Labeling parameter ellenorzes — megnezzuk a barok aranyat ahol short nyert
print(f'\n=== LABELING MATRIX ===')
print(f'  Short barokbol hany nyert volna (ar<entry)?')
# Entry a kovetkezo bar open-je
short_entry = df['Open'].shift(-1)
short_won = (df['Low'].shift(-1) < short_entry - 1.8)  # pt_short=1.8
short_lost = (df['High'].shift(-1) > short_entry + 1.0)  # sl=1.0
print(f'  Potencialis Short win (PT<1.8$ elerte): {short_won.sum()}')
print(f'  Potencialis Short loss (SL>1.0$ elerte): {short_lost.sum()}')

print('\n=== KESZ ===')
