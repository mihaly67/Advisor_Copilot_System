import pandas as pd, numpy as np
df = pd.read_csv("/data/dev/projects/z-ai-copilot/Master_csv/processed/labeled_dollar_bars_adaptive.csv")
df['ts'] = pd.to_datetime(df['End_Timestamp'])
print(f"Időszak: {df.ts.min()} → {df.ts.max()}")
print(f"Barok: {len(df):,}")
c = df['Close'].values
print(f"Ár: {c[0]:.1f} → {c[-1]:.1f} ({c[-1]-c[0]:+.1f})")
df['month'] = df.ts.dt.to_period('M')
for m, g in df.groupby('month'):
    d = g.Close.iloc[-1] - g.Close.iloc[0]
    print(f"  {m}: {d:+.1f} ({d/c[0]*100:+.2f}%)")
lb = df.Target_Label.value_counts()
print(f"\nLabel: Long={lb.get(1,0):,} Short={lb.get(-1,0):,} Noise={lb.get(0,0):,}")
print(f"Long/Short: {lb.get(1,0)/lb.get(-1,0):.2f}")
