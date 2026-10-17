#!/usr/bin/env python3
"""
kelly_sizing_eval.py — Kelly Criterion + Confidence-Graded Position Sizing

A meta-modell (meta_v1, $444K) predikcióit értékeli Kelly alapú
pozícióméretezéssel ahelyett, hogy bináris trade/pass küszöböt használna.

Módszerek:
  1. FLAT: minden trade ugyanakkora (1% tőke)
  2. FRACTIONAL KELLY: f* = (p·b - q) / b, majd 0.25x szorzó
  3. CONFIDENCE-GRADED: P(trade) alapján 0.5x-2.0x szorzó
  4. KELLY + CONFIDENCE: kombinált

Profit számolás:
  - Pozícióméret × (win ? +2.0 : -1.0) = trade profit/loss
  - Win/Loss ratio (b) = 2.0/1.0 = 2.0 (PT=2$, SL=1$)
"""
import pandas as pd
import numpy as np
import joblib
import os
import sys

BASE = '/data/dev/projects/z-ai-copilot'


def kelly_fraction(p, b=2.0, kelly_mult=0.25):
    """Kelly Criterion: f* = (p·b - q) / b, majd szorzó"""
    q = 1 - p
    f = (p * b - q) / b
    return max(0, f * kelly_mult)


def confidence_grade(p, base_size=0.01):
    """Confidence-graded sizing: P alapján 0.5x-2.0x"""
    if p < 0.45:
        return base_size * 0.5
    elif p < 0.55:
        return base_size * 1.0
    elif p < 0.65:
        return base_size * 1.5
    else:
        return base_size * 2.0


def kelly_confidence(p, b=2.0, kelly_mult=0.25, base_size=0.01):
    """Kombinált: Kelly × confidence grade"""
    k = kelly_fraction(p, b, kelly_mult)
    if k <= 0:
        return 0
    # Confidence grade multiplier
    if p < 0.45:
        mult = 0.5
    elif p < 0.55:
        mult = 1.0
    elif p < 0.65:
        mult = 1.5
    else:
        mult = 2.0
    return min(k * mult, 0.10)  # max 10% tőke


def evaluate_sizing(y_test, probs, sides, method='flat', base_size=0.01,
                    kelly_mult=0.25, min_trade_prob=0.35):
    """
    Értékeli a pozícióméretezési stratégiát.

    Returns: dict with profit, win_rate, trades, max_drawdown, sharpe
    """
    p_trade = probs[:, 1] if probs.shape[1] > 1 else probs

    trades = []
    for i in range(len(p_trade)):
        p = p_trade[i]
        if p < min_trade_prob:
            continue  # skip low confidence

        actual = y_test[i]
        side = sides[i]  # +1=Long, -1=Short
        win = (actual == 1)  # 1=PT hit (win), 0=SL (loss)

        # Position size
        if method == 'flat':
            size = base_size
        elif method == 'kelly':
            size = kelly_fraction(p, b=2.0, kelly_mult=kelly_mult)
        elif method == 'confidence':
            size = confidence_grade(p, base_size)
        elif method == 'kelly_conf':
            size = kelly_confidence(p, b=2.0, kelly_mult=kelly_mult, base_size=base_size)
        else:
            size = base_size

        if size <= 0:
            continue

        # Profit: win → +size × b, loss → -size × 1
        pnl = size * (2.0 if win else -1.0)
        trades.append({
            'p': p, 'side': side, 'win': win, 'size': size, 'pnl': pnl
        })

    if not trades:
        return {'profit': 0, 'n_trades': 0}

    df = pd.DataFrame(trades)
    total_profit = df['pnl'].sum()
    n_trades = len(df)
    n_wins = df['win'].sum()
    win_rate = n_wins / n_trades * 100

    # Max drawdown
    cumsum = df['pnl'].cumsum()
    running_max = cumsum.cummax()
    drawdown = running_max - cumsum
    max_dd = drawdown.max()

    # Sharpe (simplified)
    if df['pnl'].std() > 0:
        sharpe = df['pnl'].mean() / df['pnl'].std() * np.sqrt(252)
    else:
        sharpe = 0

    # Long/Short breakdown
    long_mask = df['side'] == 1
    short_mask = df['side'] == -1
    long_profit = df[long_mask]['pnl'].sum()
    short_profit = df[short_mask]['pnl'].sum()
    long_wins = df[long_mask]['win'].sum()
    short_wins = df[short_mask]['win'].sum()

    return {
        'total_profit': round(total_profit, 2),
        'n_trades': n_trades,
        'n_wins': int(n_wins),
        'win_rate': round(win_rate, 1),
        'max_drawdown': round(max_dd, 4),
        'sharpe': round(sharpe, 2),
        'long_profit': round(long_profit, 2),
        'short_profit': round(short_profit, 2),
        'long_trades': int(long_mask.sum()),
        'short_trades': int(short_mask.sum()),
        'long_wins': int(long_wins),
        'short_wins': int(short_wins),
        'avg_size': round(df['size'].mean(), 4),
        'avg_per_trade': round(total_profit / n_trades, 4),
    }


def main():
    # Load model and data
    model_path = os.path.join(BASE, 'models', 'meta_v1', 'model.pkl')
    data_path = os.path.join(BASE, 'Master_csv', 'processed', 'labeled_dollar_bars_v8.csv')
    features_file = os.path.join(BASE, 'models', 'v17', 'features_top30.txt')

    print("=== KELLY POSITION SIZING EVALUATION ===")
    print(f"Model: {model_path}")
    print(f"Data: {data_path}")

    clf = joblib.load(model_path)
    df = pd.read_csv(data_path)

    with open(features_file) as f:
        features = [l.strip() for l in f if l.strip()]

    X = df[features]
    y = df['Target_Meta'].astype(int).values
    sides = df['Side'].values

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test, s_train, s_test = train_test_split(
        X, y, sides, test_size=0.2, shuffle=False
    )

    probs = clf.predict_proba(X_test)
    y_test = y_test.flatten() if hasattr(y_test, 'flatten') else y_test
    s_test = s_test.flatten() if hasattr(s_test, 'flatten') else s_test

    print(f"\nTest set: {len(y_test):,} bars")
    print(f"Trade (1): {(y_test==1).sum()} ({(y_test==1).mean()*100:.1f}%)")
    print(f"Pass  (0): {(y_test==0).sum()} ({(y_test==0).mean()*100:.1f}%)")

    # P(trade) distribution
    p_trade = probs[:, 1]
    print(f"\nP(trade) distribution:")
    for pct in [10, 25, 50, 75, 90]:
        print(f"  {pct}th percentile: {np.percentile(p_trade, pct):.3f}")

    # Evaluate different methods
    print(f"\n{'='*80}")
    print(f"{'Method':<20} {'Trades':>7} {'Win%':>6} {'Profit':>9} {'MaxDD':>8} {'Sharpe':>7} {'AvgSize':>8} {'Avg/Tr':>8}")
    print(f"{'='*80}")

    methods = [
        ('FLAT 1%', 'flat', 0.01, 0.25, 0.35),
        ('FLAT 2%', 'flat', 0.02, 0.25, 0.35),
        ('Kelly 0.25x', 'kelly', 0.01, 0.25, 0.35),
        ('Kelly 0.50x', 'kelly', 0.01, 0.50, 0.35),
        ('Confidence', 'confidence', 0.01, 0.25, 0.35),
        ('Kelly+Conf', 'kelly_conf', 0.01, 0.25, 0.35),
        ('Kelly 0.25x th0.45', 'kelly', 0.01, 0.25, 0.45),
        ('Kelly 0.25x th0.50', 'kelly', 0.01, 0.25, 0.50),
        ('Confidence th0.45', 'confidence', 0.01, 0.25, 0.45),
        ('Kelly+Conf th0.45', 'kelly_conf', 0.01, 0.25, 0.45),
    ]

    results = []
    for name, method, base, kmult, min_p in methods:
        r = evaluate_sizing(y_test, probs, s_test, method=method,
                           base_size=base, kelly_mult=kmult, min_trade_prob=min_p)
        if r['n_trades'] > 0:
            print(f"{name:<20} {r['n_trades']:>7} {r['win_rate']:>5.1f}% "
                  f"{r['total_profit']:>8.1f} {r['max_drawdown']:>8.4f} "
                  f"{r['sharpe']:>7.2f} {r['avg_size']:>8.4f} {r['avg_per_trade']:>8.4f}")
            results.append((name, r))
        else:
            print(f"{name:<20} {'0':>7} — no trades")

    # Long/Short breakdown for best method
    print(f"\n{'='*80}")
    print("LONG/SHORT BREAKDOWN (Kelly 0.25x, th=0.35):")
    r = results[2][1] if len(results) > 2 else results[0][1]
    print(f"  Long:  {r['long_trades']} trades, {r['long_wins']} wins, profit={r['long_profit']}")
    print(f"  Short: {r['short_trades']} trades, {r['short_wins']} wins, profit={r['short_profit']}")
    if r['long_trades'] > 0 and r['short_trades'] > 0:
        lw = r['long_wins']/r['long_trades']*100
        sw = r['short_wins']/r['short_trades']*100
        print(f"  Long win%:  {lw:.1f}%  |  Short win%: {sw:.1f}%")
        if sw > lw:
            print(f"  → Short jobb! Short pozíció nagyobb (XAUUSD repo minta)")
        else:
            print(f"  → Long jobb! Long pozíció nagyobb")


if __name__ == '__main__':
    main()
