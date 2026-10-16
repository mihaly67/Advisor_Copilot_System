#!/usr/bin/env python3
"""Raw CSV audit: mi kell, mi nem? CFD project."""
import pandas as pd, os

BASE = '/data/dev/projects/z-ai-copilot/Master_csv/raw/új'

for f in sorted(os.listdir(BASE)):
    if not f.endswith('.csv'): continue
    path = os.path.join(BASE, f)
    size_mb = os.path.getsize(path) / 1024 / 1024
    
    # Read header
    df = pd.read_csv(path, nrows=5)
    cols = list(df.columns)
    
    # Read timestamp range
    ts_col = 'Timestamp' if 'Timestamp' in cols else 'Time'
    df_ts = pd.read_csv(path, usecols=[ts_col])
    
    print(f'{"="*70}')
    print(f'  {f}')
    print(f'{"="*70}')
    print(f'  Size: {size_mb:.0f} MB | Rows: {len(df_ts):,}')
    print(f'  Time: {df_ts.iloc[0,0]} → {df_ts.iloc[-1,0]}')
    print(f'  Cols ({len(cols)}): {cols}')
    
    # Volume check
    if 'Bid_Volume' in cols:
        bv = pd.read_csv(path, usecols=['Bid_Volume','Ask_Volume'], nrows=10000)
        total = bv['Bid_Volume'] + bv['Ask_Volume']
        nonzero = int((total>0).sum())
        print(f'  Volume: avg={total.mean():.1f}, nonzero={nonzero}/10000', end='')
        if nonzero == 0:
            print(' ← NINCS VOLUME!')
        else:
            print(' ← VAN volume')
    
    # ZZ check
    zz_cols = [c for c in ['Micro_R','Micro_S','Sec_R','Sec_S','Ter_R','Ter_S'] if c in cols]
    if zz_cols:
        print(f'  ZZ oszlopok: {zz_cols} ← BENNE VAN!')
    
    # MTF check
    mtf_cols = [c for c in ['1m_Close','5m_Close','15m_Close','30m_Close','ATR_M15','RSI_M15'] if c in cols]
    if mtf_cols:
        print(f'  MTF oszlopok: {mtf_cols} ← BENNE VAN!')
    
    print()
