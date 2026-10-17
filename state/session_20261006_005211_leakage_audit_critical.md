# Session: leakage_audit_critical
*Időbélyeg: 2026-10-06T00:52:11.250932*

LEAKAGE AUDIT KÉSZ — KRITIKUS PROBLÉMA TALÁLVA!

🚨 LOOKAHEAD BIAS: compute_features() NEM alkalmaz shift(1)-et a Dist_* es Wick_* feature-ken!
  - CSV Dist_Micro_R MAR shiftelve van (eredeti pipeline step 9)
  - De mi UJRASZAMOLJUK shift nelkul = 1 bar lookahead!
  - Hatas: ~10.8% feature std → ~1-2% WR overstatement varhato

⚠️ Threshold Optuna OOS-on futott = information leakage
⚠️ Nincs purged K-fold (14-26 bar overlap)

✅ NEM problema: stability filter, merge_asof backward, label triple barrier
✅ Irany feature-k (RSI_signed stb.) CSV-bol jonnek = MAR shiftelve

MEGOLDAS KOVETKEZO SESSION:
1. shift(1) hozzaadasa compute_features() vegen MINDEN feature-re
2. VAGY: CSV-ben levo shiftelt oszlopok hasznalata kozvetlenul
3. Minden eredmenyt UJRA futtatni shift(1)-el!
4. Threshold audit (walk-forward vagy fix)

MENTVE: /data/Brain/_qwen_analysis/v110_leakage_audit.md