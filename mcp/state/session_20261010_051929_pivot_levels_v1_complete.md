# Session: pivot_levels_v1_complete
*Időbélyeg: 2026-10-10T05:19:29.020803*

PIVOT LEVELS V1 COMPLETE:
- pivot_levels.py implementálva és tesztelve
- 6 metódus: classic(HLC/HLCC), fibonacci, camarilla, woodie, atr_pivotal, round_number
- Touch szűrés: min 5 long + 5 short M1 gyertyán (tol=0.3×ATR)
- Eredmény: 117 deduplikált szint (36,989 nyers → 36,344 szűrt → 117 dedup $3)
- Top szintek: 4062.02 (1719 touch), 4065.03 (1590), 4029.19 (1541)
- ATR Pivotal és Camarilla a legerősebb metódusok
- Mentve: Master_csv/processed/pivot_levels.csv (118 sor)
- V11 pipeline: befejeződött (MLP AUC=0.901, de LGBM mismatch a végén)
- MQ5 elemzés: Pivotal points.mq5 (ATR lokális max), Pivot oscillator (FMA/MMA/SMA 13/21/34), Pivot oscillator extended (4 pivot type + MTF), Pivot_Fibs_Custom (fib ratio), Pivot_Points_Lines_v1.3 (7 típus: Standard/Fibonacci/Camarilla/Woodie/Traditional/Demark/Classic), pivot_points.mq5 (HLC/HLCC/HLOC/HLOO + original/alternate)