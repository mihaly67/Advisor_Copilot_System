# Jules CFD V5 Exact — Audit Report

**Dátum**: 2026-10-07
**Pipeline**: jules_cfd_pipeline.py
**Cél**: Jules rendszer PONTOS reprodukciója CFD-re

## Adatforrás VERIFIED ✅
- **Train**: features_dollar_bars.csv (28,212 rows, CFD Gold XAUUSD, $444K threshold, shift(1) leakfix)
- **Vizsga**: dollar_bars_kulon_vizsga.csv (4,063 rows, pre-built dollar bars, DV mean=$411K)
- **ZZ**: Master_ZigZag_XAUUSD_M1.csv (M1 zigzag pivots, merge_asof backward)
- **Price range**: $3,960 - $4,681 (CFD, nem futures!)

## Jules 10 Feature Mapping ✅
| Jules Feature | CSV Column | Computed |
|---------------|-----------|----------|
| Tick_Speed | Tick_Speed | Direct |
| Dist_Micro_R | Dist_Micro_R_ATR | (Micro_R - Close) / ATR14 |
| Dist_Micro_S | Dist_Micro_S_ATR | (Close - Micro_S) / ATR14 |
| Dist_Sec_R/S | Dist_Sec_R/S_ATR | Same pattern |
| Dist_Ter_R/S | Dist_Ter_R/S_ATR | Same pattern |
| Stoch_State_M1 | Stoch_K | (Stoch_K - 50) / 50 |
| Upper_Wick_ATR | Wick_Upper_ATR | (High - max(O,C)) / ATR14 |
| Lower_Wick_ATR | Wick_Lower_ATR | (min(O,C) - Low) / ATR14 |

## Eredmények: ROSSZABB MINT VÉLETLEN ❌

| Metrika | OOS | Vizsga |
|---------|-----|--------|
| **WR** | **41.2%** | **39.4%** |
| Profit | $10 | $-22 |
| Trades | 325 | 1,479 |
| Long WR | 36.1% | **0.0%** |
| Short WR | 44.2% | 39.4% |

## Gyökér okok
1. Stoch hard filter blokkolja Long-ot vizsgán
2. Modell aszimmetrikus (Short domináns)
3. Swap > 50% (rossz irány)
4. Stability filter túl szigorú

## Következő lépések
1. Stoch filter enyhítése vagy eltávolítása
2. Aszimmetrikus threshold (P_LONG_MIN < P_SHORT_MIN)
3. Szimmetrikus PT/SL (PT=SL=$1.0)
4. Long-only modell vizsgálata
