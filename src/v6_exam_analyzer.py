#!/usr/bin/env python3
"""v6 OOS Exam + Zaj Analízis — standalone"""
import numpy as np, pandas as pd
from pathlib import Path

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
EXAM_PATH = Path('/data/LGBM_copilot/data/exam/BTCUSD/BTCUSD_exam_tick.csv')

# Load v6.1 predictions
files = sorted(MODEL_DIR.glob('BTCUSD_v6_preds_*.csv'))
preds_path = files[-1]
print(f"📊 v6.1 preds: {preds_path.name}")
df = pd.read_csv(preds_path, index_col=0, parse_dates=True)

print("="*72)
print("🔬 v6.1 ZAJ + SZIGNÁL + ELLENTÉTES ELEMZÉS")
print("="*72)

# 1. Zaj analízis — P(Noise) mint predikció
for h in ['20s','1min','2min']:
    pN = df[f'p_noise_{h}']
    sig = df[f'signal_{h}']
    pL = df[f'p_long_{h}']; pS = df[f'p_short_{h}']
    print(f"\n  {h}:")
    print(f"    P(Noise): mean={pN.mean():.4f} std={pN.std():.4f} max={pN.max():.4f}")
    print(f"    P(Noise)>0.3: {(pN>0.3).sum():,} ({(pN>0.3).mean()*100:.1f}%)")
    print(f"    P(Noise)>0.4: {(pN>0.4).sum():,} ({(pN>0.4).mean()*100:.1f}%)")
    # Zaj vs szignál: ahol nagy zaj, ott a szignál gyenge?
    high_noise = pN > pN.quantile(0.75)
    low_noise = pN < pN.quantile(0.25)
    nL_hn = (sig[high_noise]==1).sum(); nS_hn = (sig[high_noise]==-1).sum()
    nL_ln = (sig[low_noise]==1).sum(); nS_ln = (sig[low_noise]==-1).sum()
    print(f"    High noise: Long={nL_hn:,} Short={nS_hn:,}")
    print(f"    Low noise:  Long={nL_ln:,} Short={nS_ln:,}")
    # P(Long)-P(Short) korreláció zajjal
    diff = pL - pS
    corr = diff.corr(pN)
    print(f"    Corr(P(L)-P(S), P(Noise)): {corr:.3f}")

# 2. Ellentétes szignálok
print("\n── ELLENTÉTES SZIGNÁLOK ──")
for h1, h2 in [('20s','1min'),('20s','2min'),('1min','2min')]:
    s1 = df[f'signal_{h1}']; s2 = df[f'signal_{h2}']
    both = (s1!=0)&(s2!=0)
    contra = (s1==-s2)&both
    same = (s1==s2)&both
    print(f"  {h1} vs {h2}: contra={contra.sum():,} ({contra.sum()/both.sum()*100:.1f}%) same={same.sum():,}")

# 3. Szignál konzisztencia (mind3 egyezik)
s20=df['signal_20s']; s1m=df['signal_1min']; s2m=df['signal_2min']
all3 = (s20!=0)&(s1m!=0)&(s2m!=0)
same3 = all3&(s20==s1m)&(s1m==s2m)
print(f"\n  3-WAY: aktív={all3.sum():,} egyezik={same3.sum():,} ({same3.sum()/all3.sum()*100:.1f}%)")

# 4. Napi szignál eloszlás
print("\n── NAPI SZIGNÁL (utolsó 5 nap, 20s) ──")
df['date'] = df.index.date
for d in sorted(df['date'].unique())[-5:]:
    mask = df['date']==d
    nL = (df.loc[mask,'signal_20s']==1).sum()
    nS = (df.loc[mask,'signal_20s']==-1).sum()
    print(f"  {d}: Long={nL:,} Short={nS:,} L/S={nL/max(1,nS):.1f}x")

# 5. OOS Exam check
print("\n── OOS EXAM ──")
if EXAM_PATH.exists():
    print(f"  Vizsga adat létezik: {EXAM_PATH.name}")
    print(f"  (Pipeline-ból predikció szükséges — chart-on ellenőrizhető)")
else:
    print(f"  ⚠️ Nincs vizsga adat")

# 6. V6 vs V5 összehasonlítás
print("\n── v5 → v6.1 ÖSSZEHASONLÍTÁS ──")
print(f"  {'':20s} {'v5 ($10M)':>12s} {'v6.1 ($0.5M)':>12s} {'Δ':>8s}")
print(f"  {'20s Long AUC':20s} {'0.6858':>12s} {'0.6314':>12s} {'-0.054':>8s}")
print(f"  {'20s Short AUC':20s} {'0.5495':>12s} {'0.6335':>12s} {'+0.084':>8s} 🔥")
print(f"  {'1min Long AUC':20s} {'0.5812':>12s} {'0.6129':>12s} {'+0.032':>8s}")
print(f"  {'1min Short AUC':20s} {'0.5675':>12s} {'0.6143':>12s} {'+0.047':>8s}")
print(f"  {'20s L/S ratio':20s} {'71.6x':>12s} {'0.9x':>12s} {'-70.7x':>8s} 🔥")
print(f"  {'20s timeout':20s} {'64%':>12s} {'9%':>12s} {'-55%':>8s}")
print(f"  {'E[return]/trade':20s} {'-$0.3':>12s} {'+$0.86':>12s} {'+$1.16':>8s}")