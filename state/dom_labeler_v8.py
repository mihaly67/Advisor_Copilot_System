#!/usr/bin/env python3
"""
dom_labeler_v8.py — Meta-Labeling (López de Prado)

Kétlépéses folyamat:
  1. PRIMARY modell: egyszerű irány szabály (Slope_Close_14 > 0 → Long, < 0 → Short)
     - Ez határozza meg a "side"-ot (oldalt)
  2. TRIPLE BARRIER: a primary iránnyal
     - PT = +1.2$ (profit taking)
     - SL = -1.0$ (stop loss)
     - Vertical = 8 bar
  3. BINÁRIS LABEL:
     - 1 = PT barrier érintve (primary modell helyes volt → trade)
     - 0 = SL barrier érintve vagy vertical (primary modell rossz volt → pass)

A secondary modell bináris: trade(1) / no-trade(0)
A side (irány) már a primary modelltől jön — secondary csak szűr.

Bemenet:  features_dollar_bars_adaptive.csv (114 feature)
Kimenet:  labeled_dollar_bars_v8.csv (+ Target_Meta = 0/1, + Side = -1/+1)
"""
import pandas as pd
import numpy as np
import os
import sys


def apply_meta_labeling(df, pt_usd=1.2, sl_usd=1.0, max_bars=8):
    """
    Meta-labeling: primary modell irányt mond, triple barrier eldönti
    hogy az irány helyes volt-e.

    Returns: df with 'Side' (-1/+1) and 'Target_Meta' (0/1)
      Side: primary modell irány
      Target_Meta: 1=trade (PT hit), 0=pass (SL vagy vertical)
    """
    print(f"=== META-LABELER V8 (López de Prado) ===")
    print(f"  PT={pt_usd}$, SL={sl_usd}$, MaxBars={max_bars}")
    print(f"  Primary: Slope_Close_14 > 0 → Long, < 0 → Short")

    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values
    slope = df['Slope_Close_14'].values  # már shift(1)-elve a feature engineer-ben

    n = len(df)
    sides = np.zeros(n, dtype=np.int8)
    labels = np.zeros(n, dtype=np.int8)

    for i in range(n):
        if np.isnan(slope[i]):
            sides[i] = 0
            labels[i] = 0
            continue

        # Primary: irány a slope alapján
        side = 1 if slope[i] > 0 else -1
        sides[i] = side

        if i + max_bars >= n:
            labels[i] = 0
            continue

        # Triple barrier: primary side-dal
        entry_price = close[i]
        hit_pt = False
        hit_sl = False

        for j in range(1, max_bars + 1):
            idx = i + j
            if side == 1:  # Long
                if high[idx] >= entry_price + pt_usd:
                    hit_pt = True
                    break
                if low[idx] <= entry_price - sl_usd:
                    hit_sl = True
                    break
            else:  # Short
                if low[idx] <= entry_price - pt_usd:
                    hit_pt = True
                    break
                if high[idx] >= entry_price + sl_usd:
                    hit_sl = True
                    break

        # Meta label: 1=PT hit (trade), 0=SL vagy vertical (pass)
        labels[i] = 1 if hit_pt else 0

    df['Side'] = sides
    df['Target_Meta'] = labels
    return df


def main():
    base = '/data/dev/projects/z-ai-copilot'
    input_csv = os.path.join(base, 'Master_csv', 'processed',
                             'features_dollar_bars_adaptive.csv')
    out_csv = os.path.join(base, 'Master_csv', 'processed',
                           'labeled_dollar_bars_v8.csv')

    print(f"Beolvasas: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"   {len(df):,} sor, {len(df.columns)} oszlop")

    if 'Slope_Close_14' not in df.columns:
        print("HIBA: Slope_Close_14 nem található!")
        sys.exit(1)

    df = apply_meta_labeling(df, pt_usd=1.2, sl_usd=1.0, max_bars=8)
    df = df.iloc[:-8].copy()

    # Statisztika
    total = len(df)
    long_side = (df['Side'] == 1).sum()
    short_side = (df['Side'] == -1).sum()
    trade = (df['Target_Meta'] == 1).sum()
    no_trade = (df['Target_Meta'] == 0).sum()

    print(f"\nPrimary modell (Side):")
    print(f"  Long  (Side=+1):  {long_side:,} ({long_side/total*100:.1f}%)")
    print(f"  Short (Side=-1):  {short_side:,} ({short_side/total*100:.1f}%)")

    print(f"\nMeta label (Target_Meta):")
    print(f"  Trade (1):  {trade:,} ({trade/total*100:.1f}%)")
    print(f"  Pass  (0):  {no_trade:,} ({no_trade/total*100:.1f}%)")

    # Primary modell pontossága (PT rate = milyen gyakran volt helyes az irány)
    long_trades = ((df['Side'] == 1) & (df['Target_Meta'] == 1)).sum()
    short_trades = ((df['Side'] == -1) & (df['Target_Meta'] == 1)).sum()
    long_total = (df['Side'] == 1).sum()
    short_total = (df['Side'] == -1).sum()

    print(f"\nPrimary modell teljesítménye:")
    print(f"  Long:  {long_trades}/{long_total} = {long_trades/long_total*100:.1f}% PT hit")
    print(f"  Short: {short_trades}/{short_total} = {short_trades/short_total*100:.1f}% PT hit")
    print(f"  Összes: {(long_trades+short_trades)/total*100:.1f}% PT hit")

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"\nMentve: {out_csv} ({len(df):,} sor)")


if __name__ == '__main__':
    main()
