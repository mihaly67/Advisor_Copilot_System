# V5 CFD Long-Bias Fix — Tréning + Live Eredmények

## Változtatások
1. PT=SL=1.0 szimmetrikus Triple Barrier (volt PT=1.5 SL=1.0)
2. CUSUM_x_Bar interakció feature = CUSUM_Direction × Bar_Direction (importance 8.50%)
3. scale_pos_weight=1.012 alkalmazva

## Modell tesztek
- CUSUM UP + bearish → P(Long)=0.446 → SHORT ✅
- CUSUM DN + bullish → P(Long)=0.546 → LONG ✅
- Régi modell: P(Long)≈0.588 MINDEN esetben → LONG

## Live: 7 SHORT vs 10 LONG (régen 3 SHORT vs 353 LONG)
## ML:S 61 vs ML:L 81 (régen ~3 vs ~1680)

## Hátralevő: OOS AUC≈0.50, alacsony conf (0.02-0.37)
