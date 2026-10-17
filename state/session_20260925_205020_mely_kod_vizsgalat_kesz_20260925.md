# Session: mely_kod_vizsgalat_kesz_20260925
*Időbélyeg: 2026-09-25T20:50:20.662948*

# MÉLY KÓD-ARC VIZSGÁLAT — HÉT HIBA TALÁLÓ (2026.09.25.)

## HIBA 1: ELŐJEL-FLIP (Jules vs Z.ai pivot távolság)

Jules (`fuse_macro_to_dollar_bars.py:14`):
```python
df['Dist_Micro_R'] = (df['Micro_R'] - df['Close']) / (df['ATR_14'] + 1e-8)
```
→ Pozitív = R az ár FELETT

Z.ai (`dom_feature_engineer_mtf.py:95`):
```python
df[f'Dist_{level}_ATR'] = ((close - df[level]) / atr_m15)
```
→ Pozitív = ár R FELETT

**A dual_model_jules_nav.py-ban Dist_Micro_R_ATR-t ettem Dist_Micro_R néven — ELLENTÉTES ELŐJELLEL!**

## HIBA 2: SKÁLA MISMATCH (4-7x különbség)

| Feature | Jules mean | Z.ai mean | Arány |
|---|---|---|---|
| Dist_Micro_R | +2.828 | -0.553 | 5.1x |
| Dist_Micro_S | +3.366 | +0.514 | 6.5x |
| Dist_Sec_R | +6.532 | -1.480 | 4.4x |
| Dist_Ter_R | +18.565 | -2.636 | 7.0x |
| Upper_Wick_ATR | +0.263 | +0.069 | 3.8x |
| Tick_Speed | +0.074 | +0.013 | 5.7x |

OK: A pivot szintek MÁSHONNAN jönnek:
- Jules: ZigZag M1 (`Master_ZigZag_GCEQ26_M1.csv`) — swing high/low algoritmus
- Z.ai: MQ5 EA — MetaTrader pivot számítás, ZMQ-n küldve

És az ATR is más:
- Jules: ATR_14 a ZigZag M1 adaton
- Z.ai: ATR_M15 a dollar bar adaton

## HIBA 3: LABEL MISMATCH

Jules: `Target_Label` = {-1: 1909 (Short), 0: 402 (Noise), +1: 1984 (Long)}
→ Három osztályos triple barrier (PT=1.5$, SL=1.0$, max_bars=5)
→ Entry = Open[i+1] (nincs lookahead)

Z.ai V8: `Target_Meta` = {0: 2287 (pass), 1: 2713 (trade)} + `Side` = {-1, +1}
→ Bináris meta-label (Side=Slope_Close_14, triple barrier PT=1.2$ SL=1.0$ max_bars=8)
→ Entry = Close[i] (NEM Open[i+1] — kisebb lookahead!)

A dual_model_jules_nav.py a V8 Side+Target_Meta címkéket használta a Jules modellt értékelve
— de a Jules mást tanult!

## HIBA 4: JULES PIPELINE NEM CSAK LGBM

A Jules CSV tartalmaz: P_Long, P_Short, P_Noise, LGBM_Signal, Meta_Label

Jules pipeline:
1. LGBM → P_Long/P_Short/P_Noise (ezt töltöttem be)
2. LSTM Meta Advisor → Meta_Label (EZ A VALÓDI TRADING SIGNAL)
3. Én csak az LGBM-et használtam, nem az LSTM meta-advisort!

A Jules adat Meta_Label eloszlás: {-1: 749, 0: 780, +1: 2766}
→ Teljesen más mint a Target_Label

## HIBA 5: IN-SAMPLE LEAKAGE (korábban felfedezve)

NavSystem v1.01 az első 80%-on tanult, de dual_model_jules_nav.py az EGÉSZ CSV-n értékelt.
OOS: WR=97.1% → 51.5% (in-sample → OOS).

## HIBA 6: PRIMARY MODEL HALOTT

Corr(Slope_Close_14, fwd_ret_5) = 0.006 — gyakorlatilag nulla.
Side accuracy: 49.8% (baseline=50%).
A V8 meta-labeling véletlenszerű címkéket generál.

## HIBA 7: EGYETLEN FEATURE SEM PREDIKTÍV

Pivot distances vs breakout: corr=-0.10 (legjobb, de extrém gyenge)
Pivot distances vs direction: corr~0.003 (NULLA)
NavSystem momentum vs direction: corr~0.005 (NULLA)
Pivot-based Side accuracy: 49.6%
Slope-based Side accuracy: 49.8%

## KÖVETKEZTETÉS

A usernek igaza van: "Jules téved, te máshogy tévedsz."

Jules hibái:
1. ZigZag pivot M1-ből lehet nem releváns dollar bar-okon
2. Az LGBM nem a végleges signal (LSTM meta-advisor az)
3. A modell valószínűleg overfit (4295 bar, túl kevés adat)

Az én hibáim:
1. Előjel-flip: Dist_Micro_R_ATR → Dist_Micro_R (ellentétes előjel!)
2. Skála mismatch: 4-7x eltérés, más pivot forrás, más ATR
3. Label mismatch: 3-class vs binary+Side
4. In-sample leakage: whole CSV-n értékeltem
5. Csak LGBM, nem LSTM meta-advisor
6. OOS validáció hiánya

## FÁJLOK:
- /data/dev/projects/scalper-copilot/Micro_LGBM/src/fuse_macro_to_dollar_bars.py (Jules pivot számítás)
- /data/dev/projects/z-ai-copilot/src/dom_feature_engineer_mtf.py (Z.ai pivot számítás)
- /data/dev/projects/scalper-copilot/Micro_LGBM/src/dom_labeler_v5.py (Jules labeler)
- /data/dev/projects/z-ai-copilot/src/dom_labeler_v8.py (Z.ai labeler)