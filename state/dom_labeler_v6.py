#!/usr/bin/env python3
"""
dom_labeler_v6.py — Triple Barrier Labeler v6 (gyokerorok javitas)

VALTOZASOK vs v5:
  1. regime_short_filter=False — Short mindig engedelyezve (nincs korroros ADX filter)
  2. pt_short=1.2$ (szimmetrikus PT_Long-al, nem 1.8$)
  3. Regime_ADX feature tovabbra is elerheto, de nem hasznaljuk a labelingben

Bemenet:  features_dollar_bars_adaptive.csv
Kimenet:  labeled_dollar_bars_v6.csv
"""
import pandas as pd
import numpy as np
import os
import sys


def apply_triple_barrier(df, pt_long=1.2, pt_short=1.2, sl_multiplier=1.0, max_bars=8):
    """
    Triple Barrier labeling — szimmetrikus, regime filter nelkul.

    Labeling:
      +1 = Long  (PT=1.2$ emelkedes max_bars-on belul)
      -1 = Short (PT=1.2$ eses max_bars-on belul)
       0 = Noise (SL=1.0$ elerte vagy vertical barrier lejarat)

    Strict wick: ha SL es PT ugyanabban a bar-ban, SL nyer (konzervativ).
    Entry: kovetkezo bar Open (nincs lookahead bias).
    """
    print(f"Labeler V6: PT_Long={pt_long}$, PT_Short={pt_short}$, SL={sl_multiplier}$, MaxBars={max_bars}")
    print(f"   Regime filter: KIKAPCSOLVA (Short mindig engedelyezve)")

    labels = np.zeros(len(df))
    high_prices = df['High'].values
    low_prices = df['Low'].values
    close_prices = df['Close'].values
    open_prices = df['Open'].values

    for i in range(len(df)):
        if i + 1 >= len(df):
            break

        entry_price = open_prices[i + 1]

        # Szimmetrikus barrier-ek
        upper_long = entry_price + pt_long
        lower_long = entry_price - sl_multiplier
        lower_short = entry_price - pt_short
        upper_short = entry_price + sl_multiplier

        hit = 0  # Default Noise

        for j in range(i + 1, min(i + 1 + max_bars, len(df))):
            curr_high = high_prices[j]
            curr_low = low_prices[j]

            # --- LONG ertekeles ---
            long_pt = curr_high >= upper_long
            long_sl = curr_low <= lower_long

            # --- SHORT ertekeles ---
            short_pt = curr_low <= lower_short
            short_sl = curr_high >= upper_short

            # Intra-bar ambiguitas: ha SL es PT ugyanabban a bar-ban -> SL nyer
            if long_pt and long_sl:
                long_pt = False
            if short_pt and short_sl:
                short_pt = False

            if hit == 0:
                if long_pt and not short_pt:
                    hit = 1
                    break
                elif short_pt and not long_pt:
                    hit = -1
                    break
                elif long_sl and short_sl:
                    # Mindket irany SL-t talalt -> massziv wick -> Noise
                    break
                elif long_sl and hit == 0:
                    pass
                elif short_sl and hit == 0:
                    pass

        labels[i] = hit

    df['Target_Label'] = labels
    return df


def main():
    base = '/data/dev/projects/z-ai-copilot'
    input_csv = os.path.join(base, 'Master_csv', 'processed',
                             'features_dollar_bars_adaptive.csv')
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]

    out_csv = os.path.join(base, 'Master_csv', 'processed',
                           'labeled_dollar_bars_v6.csv')

    print(f"=== TARGET BARRIER LABELER V6 (Z.ai Copilot) ===")
    print(f"Beolvasas: {input_csv}")

    df = pd.read_csv(input_csv)
    df['Start_Timestamp'] = pd.to_datetime(df['Start_Timestamp'])
    df.sort_values('Start_Timestamp', inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f"   {len(df):,} sor")

    df_labeled = apply_triple_barrier(df, pt_long=1.2, pt_short=1.2,
                                       sl_multiplier=1.0, max_bars=8)

    # Utolso max_bars sort eldobjuk
    df_labeled = df_labeled.iloc[:-8].copy()

    # Eloszlas
    dist = df_labeled['Target_Label'].value_counts(normalize=True) * 100
    print(f"\nLabel elosztas:")
    for label, pct in dist.items():
        name = {1: 'Long', -1: 'Short', 0: 'Noise'}.get(int(label), '?')
        print(f"   {name} ({int(label):+d}): {pct:.1f}%")

    # ADX breakdown label szerint
    short = df_labeled[df_labeled['Target_Label'] == -1]
    long_ = df_labeled[df_labeled['Target_Label'] == 1]
    noise = df_labeled[df_labeled['Target_Label'] == 0]
    print(f"\nADX breakdown:")
    print(f"   Short (n={len(short)}): ADX mean={short['Regime_ADX'].mean():.1f} <20: {(short['Regime_ADX']<20).sum()} ({(short['Regime_ADX']<20).mean()*100:.1f}%)")
    print(f"   Long  (n={len(long_)}): ADX mean={long_['Regime_ADX'].mean():.1f} <20: {(long_['Regime_ADX']<20).sum()} ({(long_['Regime_ADX']<20).mean()*100:.1f}%)")
    print(f"   Noise (n={len(noise)}): ADX mean={noise['Regime_ADX'].mean():.1f} <20: {(noise['Regime_ADX']<20).sum()} ({(noise['Regime_ADX']<20).mean()*100:.1f}%)")

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df_labeled.to_csv(out_csv, index=False)
    print(f"\nMentve: {out_csv} ({len(df_labeled):,} sor)")


if __name__ == '__main__':
    main()
