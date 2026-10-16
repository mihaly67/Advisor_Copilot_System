# Z.ai Copilot Trading Model — Teljes Optimalizálási Jelentés

**Dátum**: 2026.09.30  
**Verziók**: v1.04 → v1.05 → v1.06

---

## 1. VÉGSŐ EREDMÉNYEK

### Optimális Konfigurációk

| Config | Features | nw | ThN | Dir | WR% | **Profit** | P/tr | PL | L→N | S→N |
|--------|----------|----|-----|-----|-----|-----------|------|-----|-----|-----|
| v104 Szigor | 42 | 0.70 | 0.55 | 5,344 | 66.8% | 5,369 | 1.005 | 2.01 | 2,454 | 1,816 |
| v105 Szigor | 55 | 0.85 | 0.55 | 5,353 | 67.5% | 5,492 | 1.026 | 2.08 | 2,406 | 1,820 |
| **v105 ThN0.70** | **55** | **0.85** | **0.70** | **11,787** | **61.8%** | **10,053** | **0.853** | **1.62** | **374** | **187** |
| **v106 ThN0.75** | **65** | **0.70** | **0.75** | **12,138** | **61.2%** | **10,149** | **0.836** | **1.58** | **323** | **89** |

### Javulás v104 → v106
- **+4,780 profit (+89.1%!)**
- **-2,131 L→Noise (-86.8%)**
- **-1,727 S→Noise (-95.1%)**
- Max theoretical profit: 15,682 → v106 eléri a **64.7%**-át

---

## 2. FŐ FELFEDEZÉSEK

### A. ThN az egyetlen szabályzó
- THL és THS irrelevánsak — a modell sosem cserel Long↔Short (Opp=0 mindig)
- Csak a P(Noise) küszöb (ThN) számít
- ThN=0.70-0.75 az optimális tartomány (max profit)

### B. Cascade architektúra
- Stage 1 (Noise-vs-Dir): AUC=0.7666
- Stage 2 (Long-vs-Short): **AUC=1.0000** — Long/Short teljesen szétválnak
- Hybrid = Baseline (Opp már=0, Stage2 nem ad hozzá semmit)
- Cascade WR jobb, de túl kevés trade → profit rosszabb

### C. Feature-ök
- v1.05 (+13): Regime, Informed Flow, Price Dist, Larger TF → Noise-vs-Dir javulás
- v1.06 (+10 safe): Pulse_DF_Curve, ATR_M15, Num_Ticks, volume, stb.
- Kompozit feature-ök redundánsak (LightGBM már tanul interakciókat)
- Legfontosabb feature-ök: RSI_M15, Regime_ADX, ATR_Micro, VPIN, Pulse_DF_Curve

### D. P(Noise) kalibráció
- A modell rosszul kalibrált (alulbecsli Noise-t alacsony P-nél)
- Izotonikus kalibráció túltanul OOS-on → nem segít
- P(Noise) rangsorolási pontszám, nem valószínűség — ez rendben van

### E. Dir→Noise hibák
- Közös jellemző: gyengébb trend, kisebb slope, középső RSI, magasabb ADX
- Legnagyobb hatású feature-ök: MomScore_14, Slope_Close_14, Flow_Delta_10

---

## 3. MENTETT FÁJLOK

| Fájl | Leírás |
|------|--------|
| `/models/v106/lgbm_v106.pkl` | v1.06 modell (65 feature) |
| `/models/v105_cascade/stage1_noise_vs_dir.pkl` | Binary Noise-vs-Dir |
| `/models/v105_cascade/stage2_long_vs_short.pkl` | Binary Long-vs-Short (AUC=1.0) |
| `/src/train_jules_v106.py` | Production tréning script |
| `/src/features_v9.py` | v1.06 feature lista (65) |
| `/src/cascade_v105.py` | Cascade architektúra script |

---

## 4. KÖVETKEZŐ LÉPÉSEK

1. **Production deployment**: v105 ThN=0.70 vagy v106 ThN=0.75
2. **Real-time P(Noise) monitoring**: kalibráció drift detektálás
3. **v1.07 feature-ök**: Regime_Change kompozit, további multi-timeframe
4. **Walk-forward validation**: időrendi OOS teszt (nem random split)
