#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot
/home/Jules/jules_venv/bin/python3 -c "
import pandas as pd
df = pd.read_csv('Master_csv/processed/labeled_dollar_bars_v6.csv')
df['Start_Timestamp'] = pd.to_datetime(df['Start_Timestamp'])
daily = df.groupby(df['Start_Timestamp'].dt.date).size()
print(f'Osszes nap: {len(daily)}')
print(f'Atlag bar/nap: {daily.mean():.1f}')
print(f'Min/Max bar/nap: {daily.min()}/{daily.max()}')
print(f'Percentilis: 10%={daily.quantile(0.10):.0f} 25%={daily.quantile(0.25):.0f} 50%={daily.quantile(0.50):.0f} 75%={daily.quantile(0.75):.0f} 90%={daily.quantile(0.90):.0f}')
" 2>&1
echo "---THRESHOLD---"
grep -n 'threshold\|444000\|DOLLAR' src/prado_dollar_bars.py 2>/dev/null | head -10
