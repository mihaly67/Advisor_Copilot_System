#!/usr/bin/env python3
"""
dom_labeler_v7.py — Binary Direction Labeler (gyokerorok javitas)

VALTOZAS vs v6:
  - Nincs Noise osztály! Csak Long (+1) vagy Short (-1)
  - Fixed-horizon: 5 bar mulva return > threshold → Long, < -threshold → Short
  - Koztes → a kisebb abszolút irány (Long vagy Short)
  - Nincs ATR-based Noise, ami a modellt osszezarja

Bemenet:  features_dollar_bars_adaptive.csv
Kimenet:  labeled_dollar_bars_v7.csv
"""
import pandas as pd
import numpy as np
import os
import sys


def apply_binary_labeling(df, horizon=5, threshold_pct=0.05):
    """
    Binary fixed-horizon labeling.

    Label:
      +1 = Long  (5 bar mulva return > +threshold_pct)
      -1 = Short (5 bar mulva return < -threshold_pct)

    Ha koztes (|return| < threshold): a kisebb abszolut irany (mindig Long vagy Short).
    Ez erzkenyelesi celbol — nincs Noise osztaly.

    threshold_pct: a minimális ármozgás százalékban.
    """
    print(f"Labeler V7 (Binary): Horizon={horizon} bar, Threshold={threshold_pct}%")
    print(f"   Noise osztaly: NINCS (binary Long/Short)")

    close = df['Close'].values
    labels = np.zeros(len(df))

    for i in range(len(df)):
        if i + horizon >= len(df):
            break
        future_return = (close[i + horizon] - close[i]) / close[i] * 100
        if future_return > threshold_pct:
            labels[i] = 1   # Long
        elif future_return < -threshold_pct:
            labels[i] = -1  # Short
        else:
            # Koztes: a kisebb abszolut irany (tartjuk az iranyt)
            if future_return >= 0:
                labels[i] = 1   # Long (enyhe emelkedes)
            else:
                labels[i] = -1  # Short (enyhe sullyedes)

    df['Target_Label'] = labels
    return df


def main():
    base = '/data/dev/projects/z-ai-copilot'
    input_csv = os.path.join(base, 'Master_csv', 'processed',
                             'features_dollar_bars_adaptive.csv')
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]

    out_csv = os.path.join(base, 'Master_csv', 'processed',
                           'labeled_dollar_bars_v7.csv')

    print(f"=== BINARY DIRECTION LABELER V7 ===")
    print(f"Beolvasas: {input_csv}")

    df = pd.read_csv(input_csv)
    df['Start_Timestamp'] = pd.to_datetime(df['Start_Timestamp'])
    df.sort_values('Start_Timestamp', inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f"   {len(df):,} sor")

    df_labeled = apply_binary_labeling(df, horizon=5, threshold_pct=0.05)
    df_labeled = df_labeled.iloc[:-5].copy()

    dist = df_labeled['Target_Label'].value_counts(normalize=True) * 100
    print(f"\nLabel elosztas:")
    for label, pct in dist.items():
        name = {1: 'Long', -1: 'Short'}.get(int(label), '?')
        print(f"   {name} ({int(label):+d}): {pct:.1f}%")

    short = df_labeled[df_labeled['Target_Label'] == -1]
    long_ = df_labeled[df_labeled['Target_Label'] == 1]
    print(f"\nADX breakdown:")
    print(f"   Short (n={len(short)}): ADX mean={short['Regime_ADX'].mean():.1f}")
    print(f"   Long  (n={len(long_)}): ADX mean={long_['Regime_ADX'].mean():.1f}")

    # Feature diszkriminacio
    print(f"\nFeature diszkriminacio (Short vs Long) — irany-specifikusak:")
    irany_feats = ['Bar_Direction', 'Price_Vel_Signed', 'Mom5_Direction',
                   'Mom10_Direction', 'Wick_Asymmetry', 'Consec_Bearish_3',
                   'Consec_Bullish_3', 'Bearish_Rejection', 'Bullish_Rejection',
                   'Trend_Align_Bull', 'Trend_Align_Bear', 'Regime_Slope',
                   'Price_Velocity', 'Trade_Flow_Imb']
    for ft in irany_feats:
        if ft not in df_labeled.columns:
            continue
        s_mean = short[ft].mean()
        l_mean = long_[ft].mean()
        pooled = np.sqrt((short[ft].std()**2 + long_[ft].std()**2) / 2)
        d = (s_mean - l_mean) / (pooled + 1e-9)
        marker = ' ***' if abs(d) > 0.3 else (' *' if abs(d) > 0.15 else '')
        print(f"   {ft:25s} Short={s_mean:+.3f} Long={l_mean:+.3f} d={d:+.3f}{marker}")

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df_labeled.to_csv(out_csv, index=False)
    print(f"\nMentve: {out_csv} ({len(df_labeled):,} sor)")


if __name__ == '__main__':
    main()
