# Session: short_kenyszerites_v7_v9_20260924
*Időbélyeg: 2026-09-24T02:24:16.965962*

# Short kényszerítés V7-V9 — 2026-09-24

## Eredmények (8 feature, Long+Short)

| Verzió | Módszer | Accuracy | Trades (L/S) | Win% | Opp% | Profit$ |
|--------|---------|----------|-------------|------|------|---------|
| v5 | Long-only baseline | 46.5% | 6029/0 | 47.8% | 16.8% | +2611 |
| v7 | cw_short=5.0 | 44.4% | 3619/2508 | 44.0% | 20.8% | +1952 |
| v8 | th_short=0.30 | 46.4% | 3577/2571 | 44.0% | 20.8% | +1964 |
| v9 | cw=5.0+th=0.30 | 44.3% | 3386/2769 | 43.7% | 21.1% | +1915 |

## Megállapítások
1. V7 (cw=5.0): Short recall 97% de opposite 20.8% — a modell mindent Short-nak mond
2. V8 (th=0.30): Ugyanaz az opposite (20.8%) — a threshold nem oldja meg
3. V9 (kombó): ROSSZABB (21.1% opposite, $1915) — a két módszer nem segít egymásnak
4. **Long-only (V5) jobb**: +$2611 vs +$1952 — a Short kényszerítés rontja a profitot

## Key insight
A class_weight és threshold módosítás NEM elég — a modell nem tanul jó Short-ot, csak többet mond. Opposite nem csökken. 
Következő: meta-labeling (2. modell szűrő) vagy asymmetric loss function.