# Session: optuna_thn_final
*Időbélyeg: 2026-10-04T23:46:20.768327*

OPTUNA THN TUNING KÉSZ.

Keresési tér: THL[0.25,0.50], THS[0.25,0.50], THN[0.30,0.40], SW[1,5], NoStoch
Objective: profit × (WR/50)^2 (WR>=50 bonusz, WR<50 büntetés)

OPTUNA BEST: THL=0.389, THS=0.400, THN=0.395, SW=1 (WR=50.7%, P=3186)
De SW=1 túl laza. Grid SW=2,3-mal:

VÉGSŐ KONFIG: THL=0.39, THS=0.40, THN=0.40, SW=2, NoStoch
- Teljes OOS: WR=52.0%, T=8,588, P=2,567
- 3nap viz: L:1200 S:739 = 1,939 jel (vs 516 régen = +276%)
- WR 54.6%→52.0% (-2.6%), de profit 965→2,567 (+166%)

Param importance: THS=0.557, THL=0.341, THN=0.085, SW=0.018
→ THS a legfontosabb (Short küszöb), THN kevésbé

Viz: viz_v110_jules_pred.html (1055 KB)
Title: Z.ai v1.10-Jules-CFD NoStoch THN0.40 sw2