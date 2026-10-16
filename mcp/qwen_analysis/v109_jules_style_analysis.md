# v1.09 Jules-Style Analysis — 2026-10-02

## Goal
Compare Jules v5 Fusion model with Z.ai approach; adopt what works

## Key Finding: Jules v5 CANNOT be directly applied to Z.ai 1-min bar data
- Jules v5 trained on dollar bars with absolute distance features
- Z.ai uses 1-min bars with ATR-normalized features
- Feature distribution mismatch: P(Short) max=0.37 (barely above 0.36 threshold)
- Result: Jules v5 on Z.ai data → **only Long signals** (WR=100% but meaningless)

## v1.09: Jules-style model trained on Z.ai data
- Same 10 features, same LGBM params as Jules v5
- But trained on Z.ai 1-min bar data with Target_Label
- Result: **WR=52.2%, circ=0.565, acc=0.533** — much worse than v1.08

## Comparison Table
| Model | Features | WR (stable) | Circ | Accuracy | Profit |
|-------|----------|-------------|------|----------|--------|
| Jules v5 (on dollar bars) | 10 | ~65% (live) | ? | ? | good |
| Jules v5 (on Z.ai bars) | 10 | 100%* | N/A | N/A | broken |
| v1.09 (10feat, Z.ai bars) | 10 | 52.2% | 0.565 | 0.533 | poor |
| v1.08 M10 (65feat) | 65 | 65.9% | 0.713 | ? | 12,581 |
| v1.08 TS (65feat) | 65 | 65.7% | 0.499 | ? | 12,495 |
| v1.06 (original) | 65 | 61.0% | 0.946 | ? | 10,555 |

*100% WR because only Long signals (feature distribution mismatch)

## Conclusion
1. **10 microstructure features alone are NOT enough** on 1-min bar data
   - Dollar bars aggregate by volume → each bar has equal market activity
   - 1-min bars have variable activity → need more context features
2. **Jules' architecture is good for dollar bars** but doesn't transfer to time bars
3. **v1.08's 65 features are necessary** because time bars need:
   - Regime features (trending/ranging)
   - Trend features (EMA distances, slopes)
   - Flow features (MFI, Delta, VROC)
   - Multi-timeframe features (M15, EMA50)
4. **What to adopt from Jules**:
   - ✅ Stability filter (3 consecutive same signal)
   - ✅ Threshold logic (P_L > min AND P_N < max)
   - ✅ class_weight='balanced'
   - ❌ 10-feature set (too few for time bars)
   - ❌ Dollar bar approach (different data structure)

## Next Steps
- Add Jules stability filter to v1.08 → v1.10
- Consider hybrid: Jules microstructure (10) + v1.08 context (55) = 65 features
- The stability filter could reduce noise signals and improve WR
