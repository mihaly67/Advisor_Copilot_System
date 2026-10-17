# Session: v5cfd_long_bias_diagnosis
*Időbélyeg: 2026-10-08T23:46:37.307996*

# V5 CFD Long-Bias Diagnózis (2026-10-09)

## Tünet
- Live: 353 LONG vs 3 SHORT predikció (99% Long!)
- P(Long) mindig >0.50 (még CUSUM UP = Short signal esetén is)
- Modell baseline: P(Long)=0.588 minden inputra

## 3 Gyökéroka

### 1. `scale_pos_weight` NINCS alkalmazva
- A kód tartalmazza: `spw = ns_t/nl_t` → `scale_pos_weight=spw`
- De a modell file RÉGI — `class_weight=None`, nincs scale_pos_weight
- **A modell NEM lett újraitanítva** a scale_pos_weight-tel!

### 2. CUSUM_Direction feature ELHANYAGOLHATÓ (0.57% importance)
- A modell nem használja a CUSUM irányt → nem tud Short-ot prediktálni CUSUM UP alapján
- Momentum feature-k (Pulse_DF_Curve 11.5%, Price_Velocity 10.8%, RSI 11.1%) dominálnak
- Ezek trend-követők → uptrend-ben mindig Long-ot jeleznek

### 3. PT=1.5 SL=1.0 aszimmetrikus Triple Barrier
- Dokumentáció szimmetrikust mond (PT=SL=1.0), de kód PT=1.5 SL=1.0
- Label eloszlás: 44.8% Long / 55.2% Short — TÖBB Short label
- Szimmetrikus (PT=SL=1.0): 49.8% Long / 50.2% Short — kiegyensúlyozott
- Az aszimmertia NEM okozza a Long-bias-t (sőt, Short-favoring!)

## Modell baseline predikció
- CUSUM=+1 (UP→Fade Short): P(Long)=0.574 → Long!
- CUSUM=-1 (DN→Fade Long): P(Long)=0.588 → Long!
- CUSUM=0: P(Long)=0.588 → Long!
- CUSUM=-1 + bearish bar: P(Long)=0.471 → Short (de csak alig!)

## Javítási terv
1. **Azonnali**: Retrain scale_pos_weight-tel (Short/Long = 6397/5182 = 1.234)
2. **Feature engineering**: 
   - CUSUM_Direction × Bar_Direction interakció feature (CUSUM UP + bearish → Short)
   - Overbought/Oversold indikátor (RSI>70 + CUSUM UP → Short)
3. **PT=SL=1.0 szimmetrikus** Triple Barrier (kiegyensúlyozott label-ek)
4. **class_weight='balanced'** alternatíva scale_pos_weight helyett
5. **Focal loss** hogy a modell a nehéz Short esetekre koncentráljon
