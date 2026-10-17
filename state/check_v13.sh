#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot
echo "=== V13 IRANY-SPECIFIKUS FEATURE SHAP ==="
/home/Jules/jules_venv/bin/python3 -c "
import pandas as pd
df = pd.read_csv('models/v13/shap_importance.csv')
irany = ['Bar_Direction','Bar_Bullish','Price_Vel_Signed','Price_Vel_Up',
         'Mom5_Direction','Mom5_Up','Mom10_Direction','Mom10_Up',
         'Wick_Asymmetry','Bearish_Rejection','Bullish_Rejection',
         'Consec_Bearish_3','Consec_Bullish_3','EMA50_Slope_Up',
         'Higher_High_5','Lower_Low_5','Trend_Align_Bull','Trend_Align_Bear']
sub = df[df['feature'].isin(irany)].sort_values('SHAP_Total', ascending=False)
print(sub[['feature','SHAP_Short','SHAP_Long','SHAP_Total','Long_minus_Short']].to_string(index=False))
print()
print('=== TOP 30 OVERALL ===')
print(df.head(30)[['feature','SHAP_Short','SHAP_Long','SHAP_Total']].to_string(index=False))
"
