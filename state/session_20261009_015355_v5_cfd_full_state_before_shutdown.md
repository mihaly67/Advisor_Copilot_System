# Session: v5_cfd_full_state_before_shutdown
*Időbélyeg: 2026-10-09T01:53:55.775542*

V5 CFD ML — Teljes állapot mentés (2026-10-09 shutdown előtt)

=== CÉL ===
Fix V5 CFD ML Long-bias + HUD subchart: meta-labeling, ATR-normalizált TB, P(Long)/P(Short) subchart zajzóna vonalakkal

=== MEGTETT LÉPÉSEK ===

1. ML-first signal logika implementálva
2. HUD Y-axis [0,1] fix anchor pontokkal P(Long) line series-ben
3. Noise/threshold line series-k (nem horizontal_line) — noise_lo=0.425, noise_hi=0.575, thresh=0.50
4. CUSUM_x_Bar interakció feature (8.5% importance)
5. ATR-normalizált TB: PT=SL=2×ATR, MAX_BARS=15
6. Meta-labeling pipeline: Primary=Fade CUSUM direction, Secondary=ML take/skip filter
7. scale_pos_weight alkalmazva
8. Modell retraint
9. HUD subchart line series init fix — MINDIG init-eljük (nem csak has_pred esetén)
10. HUD traceback debug eltávolítva

=== SZÁMOK (utolsó tréning eredmény) ===
- AUC OOS: 0.4973, VIZSGA: 0.4823
- Meta WR OOS: 50.6%, VIZSGA: 17.9% (OVERFIT)
- Fade CUSUM WR OOS: 51.0%, VIZSGA: 50.8%
- Fade+ML WR OOS: 52.9%, VIZSGA: 52.7%
- VIZSGA Short WR: 7.1% (nagy Short bias overfit)
- Feature importance: szinte egyenlő 8-11% (egyik sem domináns)
- Train bars: Long=5,109 Short=5,391 Noise=4,637
- ATR14 medián: Train=$2.50 Vizsga=$2.43

=== FUNDAMENTÁLIS DIAGNÓZIS (3 probléma) ===

PROBLÉMA 1: CÍMKE — Véletlenszerű
- Szimmetrikus TB (PT=SL=2×ATR) + rövid lookahead = ~50/50 Long/Short
- Ha a label random → modell is random (AUC≈0.50)

PROBLÉMA 2: FEATURE-K — Nem érti a jelentésüket
- Dist_Micro_S=1.5 csak szám, a fa nem tudja=hogyan support felett=bullish
- Nincsenek boolean/categorical feature-k (Above_Support, RSI_Oversold, stb.)
- Nincsenek kontextus-kombinációk (Fade_Short_Setup, Bounce_Long_Setup)

PROBLÉMA 3: NORMALIZÁCIÓ — Nem a fő baj
- LightGBM NEM igényel normalizációt (histogram-based)
- DE boolean/categorical feature-k nagyon segítik a fát

=== KUTATÁS EREDMÉNYEK ===

AlphaPy: abovema(), belowma(), higher(), lower() → boolean feature-k a fa számára
freqtrade FreqAI: sample_weight temporal, RSI/EMA/SMA multi-timeframe, .to_numpy() (nem normalizál)
LightGBM-Quant-Model (Two Sigma): StandardScaler outlier kezelés, confidence scoring
Triple Barrier repo: trade_side=BUY/SELL, stop_loss_width, take_profit_width, time_barrier_periods
LightGBM: histogram-based algorithm, categorical_feature paraméter, nem igényel normalizációt

=== ÚJ TERV (folytatáshoz) ===

Phase 1: Diagnosztika (15 perc)
- Feature-label korreláció mátrix (Pearson + Spearman)
- Label eloszlás vizualizáció
- Ha egyetlen feature sem korrelál >0.05 → fundamentálisan rossz

Phase 2: Feature Engineering — Jelentés definiálása (30 perc)
- Boolean/categorical feature-k: Above_Support, Near_Support, Below_Resistance, RSI_Oversold, RSI_Overbought, Bullish_Bar, Bearish_Bar, CUSUM_Up, CUSUM_Down, Trend_Up, Trend_Down
- Kontextus-kombinációk: Fade_Short_Setup, Bounce_Long_Setup, Trend_Resume_Long, Trend_Resume_Short, Breakdown, Breakout
- LightGBM categorical_feature paraméter

Phase 3: Címke javítás (20 perc)
- Opció A: Aszimmetrikus TB — PT=1.5×ATR, SL=3.0×ATR a signal irányához
- Opció B: Return label — jövő N bar return előjele
- MAX_BARS=30, sample weighting

Phase 4: 2 Külön modell + Optuna (45 perc)
- Long modell: CUSUM DOWN event-ek, label=1 ha Long PT hit
- Short modell: CUSUM UP event-ek, label=1 ha Short PT hit
- Ha mindkettő AUC≈0.50 → fundamentális probléma
- Optuna hyperopt

Phase 5: Érvényesítés (15 perc)
- OOS AUC > 0.55, VIZSGA WR > 53%, Long/Short szimmetrikus

=== KÓD VÁLTOZÁSOK (már megtettük) ===

1. hud_v5_cfd.py: line series init MINDIG (nem csak has_pred)
   - if has_pred: plong_line.set(anchor+pl), pshort_line.set(ps)
   - else: plong_line.set(anchor+0.5), pshort_line.set(0.5)
   - noise/thresh line series MINDIG init-elve

2. hud_v5_cfd.py: traceback debug eltávolítva (except block simplified)

3. jules_cfd_v5.py: ATR-normalizált TB, meta-labeling pipeline, CUSUM_dir feature

=== HUD ZMQ PROBLÉMA (nyitott) ===
- HUD [ZMQ] Connected to 5557 OK
- Copilot küld jeleket (P(L)=57.3% etc.)
- DE HUD nem kap adatot (csak 1 sor log: [ZMQ] Connected)
- Lehetséges ok: copilot nem publikál ZMQ-t dollár bar-onként, csak konzolra logol
- TODO: debug ZMQ publish a copilot-ban

=== FÁJLOK ===
Tréning script: /data/dev/projects/z-ai-copilot/src/jules_cfd_v5.py
HUD: /home/Jules/LGBM_mlops/HUD_Development/hud_v5_cfd.py
Copilot: /home/Jules/LGBM_mlops/Micro_LGBM/src/mt5_live_copilot_v5_cfd.py
Modell: /data/dev/projects/z-ai-copilot/models/jules_cfd_v5/lgbm_v5.pkl
Diagnózis: /data/Brain/_qwen_analysis/v5_cfd_diagnosis_and_plan.md

=== KÖVETKEZŐ LÉPÉS (folytatáskor) ===
Phase 1: Diagnosztika — feature-label korreláció mátrix futtatása
Phase 2: Boolean/categorical feature-k implementálása compute_features()-ben