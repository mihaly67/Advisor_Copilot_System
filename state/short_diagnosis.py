"""Short predikció diagnosztika — miért zuhan P(Short) volatilis dropokon?"""
import pandas as pd, numpy as np, joblib

BASE = '/data/dev/projects/z-ai-copilot'
df = pd.read_csv(f'{BASE}/Master_csv/processed/labeled_dollar_bars_adaptive.csv')
clf = joblib.load(f'{BASE}/models/lgbm_model_v5_adaptive.pkl')

features = [
    'Trade_Flow_Imb', 'VPIN', 'Run_Length', 'Micro_Price_Dist',
    'Roll_Spread', 'Kyle_Lambda', 'Kyle_Vol_Sync', 'Amihud_Illiq',
    'Price_Velocity', 'WPR_14', 'RSI_Fast_5', 'Pulse_MACD_Hist',
    'Micro_R_Vel', 'Micro_S_Vel', 'Dist_Micro_R_ATR', 'Dist_Micro_S_ATR',
    'Pulse_DF_Curve', 'Avg_Spread', 'ATR_Micro',
    'Wick_Upper_ATR', 'Wick_Lower_ATR', 'Bar_Duration_Sec',
    'Stoch_D', 'Regime_Above_EMA50', 'Regime_ADX', 'Regime_Trending',
    'Regime_ZScore', 'Regime_Slope', 'Regime_Mom_10',
    'Regime_Long_Context', 'Regime_Short_Context',
]
features = [f for f in features if f in df.columns]

split = int(len(df)*0.8)
test = df.iloc[split:].copy()

probs = clf.predict_proba(test[features])
c = clf.classes_
i_s, i_n, i_l = list(c).index(0), list(c).index(1), list(c).index(2)

test['P_Short'] = probs[:, i_s]
test['P_Noise'] = probs[:, i_n]
test['P_Long'] = probs[:, i_l]

short_mask = test['Target_Label'] == -1
long_mask = test['Target_Label'] == 1
noise_mask = test['Target_Label'] == 0

print(f'=== TEST SET: {len(test)} bars ===')
print(f'Short: {short_mask.sum()} | Long: {long_mask.sum()} | Noise: {noise_mask.sum()}')

# 1. P(Short) eloszlás az igaz Short barokon
ps_ts = test.loc[short_mask, 'P_Short']
ps_tl = test.loc[long_mask, 'P_Short']
print(f'\n=== P(Short) ELOSZLÁS ===')
print(f'True Short (n={len(ps_ts)}): mean={ps_ts.mean():.4f} med={ps_ts.median():.4f}')
print(f'  >0.3: {(ps_ts>0.3).sum()} ({(ps_ts>0.3).mean()*100:.1f}%)')
print(f'  >0.5: {(ps_ts>0.5).sum()} ({(ps_ts>0.5).mean()*100:.1f}%)')
print(f'  <0.1: {(ps_ts<0.1).sum()} ({(ps_ts<0.1).mean()*100:.1f}%)')
print(f'True Long  (n={len(ps_tl)}): mean={ps_tl.mean():.4f} med={ps_tl.median():.4f}')

# 2. P(Long) eloszlás az igaz Short barokon — HANEM Long-ot mond?
pl_ts = test.loc[short_mask, 'P_Long']
pn_ts = test.loc[short_mask, 'P_Noise']
print(f'\n=== TRUE SHORT barok: P(Long) és P(Noise) ===')
print(f'P(Long)  mean={pl_ts.mean():.4f} med={pl_ts.median():.4f}')
print(f'P(Noise) mean={pn_ts.mean():.4f} med={pn_ts.median():.4f}')
print(f'P(Long)>P(Short): {(pl_ts > ps_ts).sum()}/{len(ps_ts)} ({(pl_ts > ps_ts).mean()*100:.1f}%)')

# 3. Volatilitás quintile vs P(Short) true Short barokon
if 'ATR_Micro' in test.columns:
    test['ATR_Q'] = pd.qcut(test['ATR_Micro'], 5, labels=['Q1_low','Q2','Q3','Q4','Q5_high'])
    print(f'\n=== VOLATILITÁS vs P(Short) a TRUE SHORT barokon ===')
    for q in ['Q1_low','Q2','Q3','Q4','Q5_high']:
        m = short_mask & (test['ATR_Q'] == q)
        if m.sum() > 0:
            ps = test.loc[m, 'P_Short']
            pl = test.loc[m, 'P_Long']
            print(f'  {q}: n={m.sum()}, P(S)={ps.mean():.4f} P(L)={pl.mean():.4f} P(S)>0.5: {(ps>0.5).sum()}/{m.sum()}')

# 4. Regime_ADX vs P(Short)
if 'Regime_ADX' in test.columns:
    print(f'\n=== Regime_ADX vs P(Short) TRUE SHORT barokon ===')
    for lo, hi, label in [(0,15,'ADX<15'), (15,20,'15-20'), (20,30,'20-30'), (30,50,'30-50'), (50,100,'ADX>50')]:
        m = short_mask & (test['Regime_ADX'].between(lo, hi))
        if m.sum() > 0:
            ps = test.loc[m, 'P_Short']
            pl = test.loc[m, 'P_Long']
            print(f'  {label}: n={m.sum()}, P(S)={ps.mean():.4f} P(L)={pl.mean():.4f}')

# 5. Volatilis dropok amik NEM Short label
if 'Price_Velocity' in test.columns:
    pv5 = test['Price_Velocity'].quantile(0.05)
    big_drop = (test['Price_Velocity'] < pv5) & (~short_mask)
    if big_drop.sum() > 0:
        print(f'\n=== GYORS DROP DE NEM SHORT LABEL (n={big_drop.sum()}) ===')
        print(f'  P(S) mean={test.loc[big_drop,"P_Short"].mean():.4f}')
        print(f'  P(L) mean={test.loc[big_drop,"P_Long"].mean():.4f}')
        print(f'  P(N) mean={test.loc[big_drop,"P_Noise"].mean():.4f}')
        print(f'  Valódi label: Long={((test["Target_Label"]==1)&big_drop).sum()}, Noise={((test["Target_Label"]==0)&big_drop).sum()}')

# 6. TOP/BOTTOM Short predikciók
test_s = test[short_mask].copy().sort_values('P_Short', ascending=False)
print(f'\n=== TOP 5 LEGJOBB Short pred (true Short) ===')
for _, r in test_s.head(5).iterrows():
    adx = r.get('Regime_ADX', 0)
    atr = r.get('ATR_Micro', 0)
    print(f'  P(S)={r["P_Short"]:.3f} P(L)={r["P_Long"]:.3f} | ADX={adx:.1f} ATR={atr:.4f}')
print(f'\n=== TOP 5 LEGROSSZABB Short pred (true Short) ===')
for _, r in test_s.tail(5).iterrows():
    adx = r.get('Regime_ADX', 0)
    atr = r.get('ATR_Micro', 0)
    print(f'  P(S)={r["P_Short"]:.3f} P(L)={r["P_Long"]:.3f} | ADX={adx:.1f} ATR={atr:.4f}')

# 7. P(Short) histogram értékek
bins = [0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0]
print(f'\n=== P(Short) HISTOGRAM true Short barokon ===')
for i in range(len(bins)-1):
    m = (ps_ts >= bins[i]) & (ps_ts < bins[i+1])
    print(f'  [{bins[i]:.2f}-{bins[i+1]:.2f}): {m.sum()} ({m.mean()*100:.1f}%)')

# 8. SHAP-like: feature korreláció P(Short)-tal
test_s2 = test[short_mask]
corr_ps = test_s2[features + ['P_Short']].corr()['P_Short'].drop('P_Short').abs().sort_values(ascending=False)
print(f'\n=== Feature |corr| P(Short)-al TRUE SHORT barokon ===')
for f, v in corr_ps.head(10).items():
    raw = test_s2[features + ['P_Short']].corr()['P_Short'][f]
    print(f'  {f:>25}: r={raw:+.3f}')
