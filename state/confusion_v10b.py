import pandas as pd, numpy as np, joblib
from sklearn.metrics import confusion_matrix
df = pd.read_csv("/data/dev/projects/z-ai-copilot/Master_csv/processed/labeled_dollar_bars_adaptive.csv")
clf = joblib.load("/data/dev/projects/z-ai-copilot/models/lgbm_model_v5_adaptive.pkl")
features = ["Trade_Flow_Imb","VPIN","Run_Length","Micro_Price_Dist","Roll_Spread","Kyle_Lambda","Kyle_Vol_Sync","Amihud_Illiq","Price_Velocity","WPR_14","RSI_Fast_5","Pulse_MACD_Hist","Micro_R_Vel","Micro_S_Vel","Dist_Micro_R_ATR","Dist_Micro_S_ATR","Pulse_DF_Curve","Avg_Spread","ATR_Micro","Wick_Upper_ATR","Wick_Lower_ATR","Bar_Duration_Sec","Stoch_D","Regime_Above_EMA50","Regime_ADX","Regime_Trending","Regime_ZScore","Regime_Slope","Regime_Mom_10","Regime_Long_Context","Regime_Short_Context"]
features = [f for f in features if f in df.columns]
split = int(len(df)*0.8)
test = df.iloc[split:]
preds = clf.predict(test[features])
y_true = (test["Target_Label"] + 1).astype(int).values
cm = confusion_matrix(y_true, preds)
labels = ["Short","Noise","Long"]
print("=== CONFUSION V10b (short regime) ===")
for i,l in enumerate(labels):
    print(f"{l:>8} | " + " | ".join(f"{cm[i][j]:>8}" for j in range(3)))
opposite = cm[0][2] + cm[2][0]
print(f"Opposite: {opposite} ({opposite/cm.sum()*100:.1f}%)")
print(f"Short R={cm[0][0]/cm[0].sum()*100:.1f}% P={cm[0][0]/cm[:,0].sum()*100:.1f}%")
print(f"Long  R={cm[2][2]/cm[2].sum()*100:.1f}% P={cm[2][2]/(cm[:,2].sum())*100:.1f}%")
print(f"Accuracy: {np.trace(cm)/cm.sum()*100:.1f}%")
print("\n=== REGIME DISCRIMINATION ===")
lm = test["Target_Label"] == 1
sm = test["Target_Label"] == -1
for f in ["Regime_Above_EMA50","Regime_ADX","Regime_Trending","Regime_ZScore","Regime_Slope","Regime_Mom_10","Regime_Long_Context","Regime_Short_Context"]:
    if f not in test.columns: continue
    l = test.loc[lm, f].dropna()
    s = test.loc[sm, f].dropna()
    d = (l.mean()-s.mean()) / np.sqrt((l.std()**2+s.std()**2)/2) if l.std()+s.std() > 0 else 0
    print(f"  {f:>22}: d={d:+.3f}  L={l.mean():+.4f}  S={s.mean():+.4f}")
