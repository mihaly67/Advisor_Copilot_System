#!/usr/bin/env python3
"""
Scalper Copilot v4.0 — Multi-Horizon Charts (1 nap)
Generál 3 KÜLÖN chartot: 1min / 2min / 3min — mindegyik clean 2-panel template.
NEM egy zsúfolt 3-panel — külön-külön, a minta: scalper_copilot_chart.py

Használat:
  python scalper_copilot_chart_mh.py --date 2026-10-07       # mind a 3
  python scalper_copilot_chart_mh.py --date 2026-10-07 --horizon 2min  # csak 2min
"""
from scalper_copilot_chart import build_chart, VALID_HORIZONS


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Scalper Copilot v4.0 — Multi-Horizon Charts (külön fájlok)')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--date', default=None, help='YYYY-MM-DD')
    p.add_argument('--horizon', default='all', choices=['1min', '2min', '3min', 'all'],
                    help='Egy horizont vagy "all" mind a 3 külön chart')
    p.add_argument('--max-points', type=int, default=8000)
    a = p.parse_args()
    result = build_chart(a.instrument, a.date, a.horizon, a.max_points)
    if isinstance(result, list):
        print(f"\n📊 {len(result)} chart generálva")
    elif result:
        print(f"\n📊 Chart: {result}")

