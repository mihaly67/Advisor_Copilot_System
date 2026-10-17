# Session: v106_final_results
*Időbélyeg: 2026-09-30T23:43:39.207890*

# v1.06 Teljes Eredmények — Végső Összehasonlítás — 2026.09.30

## OPTIMALIS KONFIGURACIOK

| Config | Features | nw | ThN | Dir | WR% | Profit | P/tr | PL | L→N | S→N |
|--------|----------|----|-----|-----|-----|--------|------|-----|-----|-----|
| v104 Szigor | 42 | 0.70 | 0.55 | 5,344 | 66.8% | 5,369 | 1.005 | 2.01 | 2,454 | 1,816 |
| v105 Szigor | 55 | 0.85 | 0.55 | 5,353 | 67.5% | 5,492 | 1.026 | 2.08 | 2,406 | 1,820 |
| **v105 ThN0.70** | 55 | 0.85 | 0.70 | **11,787** | **61.8%** | **10,053** | 0.853 | 1.62 | **374** | **187** |
| **v106 ThN0.75** | 65 | 0.70 | 0.75 | **12,138** | **61.2%** | **10,149** | 0.836 | 1.58 | **323** | **89** |

## JAVULASOK v104 Szigor → v106 ThN0.75
- **+4,780 profit (+89.1%!)**
- **-2,131 L→Noise (-86.8%)**
- **-1,727 S→Noise (-95.1%)**
- WR: -5.6% (de a profit drasztikusan jobb)

## JAVULASOK v105 Szigor → v105 ThN0.70
- **+4,561 profit (+83.0%!)**
- **-2,032 L→Noise (-84.5%)**
- **-1,633 S→Noise (-89.7%)**

## P(Noise) KALIBRACIO
- A modell P(Noise) rosszul kalibralt: alulbecsli a Noise-t alacsony P-n, tulbecsli magasn
- Izotonikus kalibracio OOS-on rosszabb (Brier 0.2547 → 0.3178) — túltanul
- P(Noise) rangsorolasi pontszam, nem valószínűseg — ez rendben van a küszöb-döntéshez

## COMPOSITE FEATURE-OK
- 9 kompozit feature tesztelve: csak Regime_Change (+0.0024 AUC) javit
- LightGBM mar nonline'ris interakciókat tanul — kompozit feature-ok redundánsak
- A valo javulas uj oszlopokbol jon (Pulse_DF_Curve, ATR_M15, stb.)

## MENTETT FAJLOK
- /models/v106/lgbm_v106.pkl — v1.06 modell (65 feature)
- /models/v106/features.txt
- /src/train_jules_v106.py — production tréning script
- /src/features_v9.py — v1.06 feature lista
- /src/cascade_v105.py — cascade architektúra script
- /models/v105_cascade/ — Stage1 + Stage2 modellek
- /models/v105/pnoise_isotonic.pkl — kalibrátor (nem segít)
