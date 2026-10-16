# V5 CFD ML — Teljes állapot mentés (2026-10-09 shutdown előtt)

## CÉL
Fix V5 CFD ML Long-bias + HUD subchart: meta-labeling, ATR-normalizált TB, P(Long)/P(Short) subchart zajzóna vonalakkal

---

## KÓD VÁLTOZÁSOK (már megtettük)

### 1. hud_v5_cfd.py — Line series init fix
**Probléma**: Ha első tick `has_pred=False`, a line series-ek nem kaptak `.set()`-et → később `.update()` IndexError (üres DataFrame).

**Fix**: Line series MINDIG init-elve, ha `has_pred=False` akkor 0.5 alapértékkel:
```python
if not self.is_init:
    self.chart.set(pd.DataFrame([cd_data]))
    # Subchart line series init — MINDIG, nem csak has_pred!
    base_ts=raw_dt.floor('min')
    a0=(base_ts - pd.Timedelta(minutes=3)).strftime('%Y-%m-%d %H:%M:%S')
    a1=(base_ts - pd.Timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    a2=(base_ts - pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
    if has_pred:
        self.plong_line.set(pd.DataFrame([
            {'time':a0,'value':0.0},{'time':a1,'value':1.0},{'time':ts_str,'value':pl}
        ]))
        self.pshort_line.set(pd.DataFrame([{'time':ts_str,'value':ps}]))
    else:
        self.plong_line.set(pd.DataFrame([
            {'time':a0,'value':0.0},{'time':a1,'value':1.0},{'time':ts_str,'value':0.5}
        ]))
        self.pshort_line.set(pd.DataFrame([{'time':ts_str,'value':0.5}]))
    # Zajzóna MINDIG
    self.noise_lo_line.set(pd.DataFrame([{'time':a0,'value':0.425},{'time':ts_str,'value':0.425}]))
    self.noise_hi_line.set(pd.DataFrame([{'time':a0,'value':0.575},{'time':ts_str,'value':0.575}]))
    self.thresh_line.set(pd.DataFrame([{'time':a0,'value':0.50},{'time':ts_str,'value':0.50}]))
    self.is_init=True
```

### 2. hud_v5_cfd.py — traceback debug eltávolítva
```python
# Before:
except Exception as e:
    import traceback; traceback.print_exc(limit=2)
    print(f"[HUD Error] {e}",flush=True)
# After:
except Exception as e:
    print(f"[HUD Error] {e}",flush=True)
```

### 3. jules_cfd_v5.py — Aktuális állapot
- ATR-normalizált TB: PT=SL=2×ATR, MAX_BARS=15
- Meta-labeling: Fade CUSUM = primary, ML = secondary filter
- CUSUM_Direction feature + CUSUM_x_Bar interakció
- scale_pos_weight alkalmazva
- Feature set (17 feature):
  - FEAT_SR: Dist_Micro_R, Dist_Micro_S, Dist_Ter_R, Dist_Ter_S
  - FEAT_BAR: Bar_Direction
  - FEAT_CUSUM: CUSUM_Direction
  - FEAT_INTER: CUSUM_x_Bar
  - FEAT_MOM: Pulse_DF_Curve, Price_Velocity, Micro_RSI_14
  - FEAT_TREND: Trend_EMA_Fast_Dist, Trend_EMA_Medium_Dist
  - FEAT_NAV: DF_Direction, MACD_Direction, Nav_Consensus (mind 0.0 placeholder)
  - FEAT_REGIME: Regime_ADX, Regime_Trending (shift(1) if exists)

---

## SZÁMOK (utolsó tréning)

```
[4] Triple Barrier (PT=2.0×ATR, SL=2.0×ATR, MAX_BARS=15)
  ATR14 median: Train=$2.50 Vizsga=$2.43
  Train: Long=5,109 Short=5,391 Noise=4,637

[5] Meta-labeling (Fade CUSUM = primary, ML = secondary filter)
  Train: 8,400 | OOS: 2,100
    Take trade (1): train=4,222 oos=1,070
    Skip trade (0): train=4,178 oos=1,030
  scale_pos_weight = 0.990

Feature importance (top 10):
     1. Dist_Ter_R                11.16%
     2. Dist_Ter_S                10.93%
     3. Trend_EMA_Fast_Dist       9.92%
     4. Micro_RSI_14              9.62%
     5. Bar_Direction             9.05%
     6. Dist_Micro_S              8.91%
     7. Dist_Micro_R              8.89%
     8. Trend_EMA_Medium_Dist     8.44%
     9. Pulse_DF_Curve            8.26%
    10. Price_Velocity            7.79%

[6] OOS: AUC = 0.4973, WR=50.6% P=$12 T=1080 L:49.7% S:51.5%
[7] VIZSGA: AUC = 0.4823, WR=17.9% P=$-1374 T=2140 L:65.0% S:7.1%
[8] CUSUM-only: OOS WR=49.0%, VIZSGA WR=49.2%
[9] Fade CUSUM: OOS WR=51.0%, VIZSGA WR=50.8%
[10] Fade+ML: OOS WR=52.9%, VIZSGA WR=52.7%
```

---

## FUNDAMENTÁLIS DIAGNÓZIS

### PROBLÉMA 1: CÍMKE — Véletlenszerű
- Szimmetrikus TB (PT=SL=2×ATR) + MAX_BARS=15 → ~50/50 Long/Short
- Random walk-ban az ár ~50% eséllyel megy fel 2×ATR mielőtt lemegy 2×ATR
- Ha a label random → modell is random (AUC≈0.50)

### PROBLÉMA 2: FEATURE-K — Nem érti a jelentésüket
- A fa split-eket keres, de `Dist_Micro_S=1.5` csak szám
- Nem tudja: "ár a support felett = bullish kontextus"
- Feature importance szinte egyenlő (8-11%) → egyik sem domináns
- NINCSENEK boolean/categorical feature-k
- NINCSENEK kontextus-kombinációk

### PROBLÉMA 3: NORMALIZÁCIÓ — Nem a fő baj
- LightGBM histogram-based → NEM igényel normalizációt
- DE boolean/categorical feature-k nagyon segítik a fát (1 split = tiszta szétválasztás)

---

## KUTATÁS ÖSSZEFoglALÓ

| Repo/Szolgáltatás | Kulcs tanulság |
|---|---|
| **AlphaPy** | `abovema()`, `belowma()`, `higher()`, `lower()` — boolean feature-k a fa számára |
| **freqtrade FreqAI** | sample_weight temporal, multi-timeframe RSI/EMA/SMA, .to_numpy() (nem normalizál) |
| **LightGBM-Quant (Two Sigma)** | StandardScaler outlier kezelés, confidence scoring, market residual returns |
| **triple_barrier-main** | trade_side=BUY/SELL, stop_loss_width, take_profit_width, time_barrier_periods |
| **LightGBM hivatalos** | Histogram-based algorithm, categorical_feature paraméter, NEM igényel normalizációt |
| **Prado (MLfinLab)** | Meta-labeling, sample uniqueness, feature importance MDA |

---

## ÚJ TERV (folytatáskor)

### Phase 1: Diagnosztika (15 perc)
1. Feature-label korreláció mátrix (Pearson + Spearman)
2. Label eloszlás vizualizáció
3. Feature eloszlás + outlier detektálás
4. Ha egyetlen feature sem korrelál >0.05 → fundamentálisan rossz

### Phase 2: Feature Engineering — Jelentés definiálása (30 perc)

**Boolean/Categorical feature-k**:
| Új Feature | Definíció | Jelentés |
|---|---|---|
| `Above_Support` | Dist_Micro_S > 0 | Ár a support felett = bullish |
| `Near_Support` | 0 < Dist_Micro_S < 0.5 | Ár közel a support-höz = bounce setup |
| `Below_Resistance` | Dist_Micro_R > 0 | Resistance az ár felett = bearish cap |
| `Near_Resistance` | 0 < Dist_Micro_R < 0.5 | Ár közel a resistance-hez = reject setup |
| `RSI_Oversold` | Micro_RSI_14 < 30 | Oversold = Long setup |
| `RSI_Overbought` | Micro_RSI_14 > 70 | Overbought = Short setup |
| `Bullish_Bar` | Bar_Direction > 0 | Bullish candle |
| `Bearish_Bar` | Bar_Direction < 0 | Bearish candle |
| `CUSUM_Up` | CUSUM_Direction > 0 | Felfelé momentum |
| `CUSUM_Down` | CUSUM_Direction < 0 | Lefelé momentum |
| `Trend_Up` | Trend_EMA_Fast_Dist > 0 | Ár az EMA felett |
| `Trend_Down` | Trend_EMA_Fast_Dist < 0 | Ár az EMA alatt |

**Kontextus-kombinációk**:
| Új Feature | Definíció | Jelentés |
|---|---|---|
| `Fade_Short_Setup` | CUSUM_Up & RSI_Overbought | Fade UP + overbought = Short |
| `Bounce_Long_Setup` | CUSUM_Down & RSI_Oversold | Fade DOWN + oversold = Long |
| `Trend_Resume_Long` | Trend_Up & Bullish_Bar & Above_Support | Trend folytatódik fel |
| `Trend_Resume_Short` | Trend_Down & Bearish_Bar & Below_Resistance | Trend folytatódik le |
| `Breakdown` | ~Above_Support & CUSUM_Down | Support broken + momentum le |
| `Breakout` | ~Below_Resistance & CUSUM_Up | Resistance broken + momentum fel |

### Phase 3: Címke javítás (20 perc)
- Opció A: Aszimmetrikus TB — Fade Long: PT=1.5×ATR, SL=3.0×ATR; Fade Short: PT=1.5×ATR, SL=3.0×ATR
- Opció B: Return label — jövő N bar return előjele
- MAX_BARS=30, sample weighting (Prado uniqueness vagy return magnitude)

### Phase 4: 2 Külön modell + Optuna (45 perc)
- Long modell: CUSUM DOWN event-ek, label=1 ha Long PT hit
- Short modell: CUSUM UP event-ek, label=1 ha Short PT hit
- Ha mindkettő AUC≈0.50 → fundamentális probléma
- Optuna hyperopt

### Phase 5: Érvényesítés (15 perc)
- OOS AUC > 0.55, VIZSGA WR > 53%, Long/Short szimmetrikus
- Feature importance: kontextus feature-k dominálnak?

---

## HUD ZMQ PROBLÉMA (nyitott)
- HUD [ZMQ] Connected to 5557 ✓
- Copilot fut és küld jeleket (P(L)=57.3% stb. a konzolon)
- DE HUD log csak 1 sor: [ZMQ] Connected → nem kap adatot
- Lehetséges okok:
  1. Copilot nem publikál ZMQ-t, csak logol
  2. ZMQ prefix mismatch ("HUD " vs "HUD")
  3. Port 5557 nem publikál a copilot
- TODO: debug ZMQ publish a copilot-ban (mt5_live_copilot_v5_cfd.py)

---

## lightweight-charts ismert hibák
- v4.1.0-rc2: Nincs setVisibleRange() a priceScale-en (csak v5.x)
- horizontal_line() invisible to autoScale → create_line() series-t használunk
- create_line(color='rgba(0,0,0,0)',width=0) → _interval=0 → ZeroDivisionError
- abstract.py line 241: update() IndexError ha data DataFrame üres (már fix-elve)

---

## FÁJLOK
| Fájl | Út | Státusz |
|---|---|---|
| Tréning script | /data/dev/projects/z-ai-copilot/src/jules_cfd_v5.py | Szerkesztve |
| HUD | /home/Jules/LGBM_mlops/HUD_Development/hud_v5_cfd.py | Szerkesztve (init fix) |
| Copilot | /home/Jules/LGBM_mlops/Micro_LGBM/src/mt5_live_copilot_v5_cfd.py | Szerkesztve |
| Modell | /data/dev/projects/z-ai-copilot/models/jules_cfd_v5/lgbm_v5.pkl | Trained |
| Diagnózis doc | /data/Brain/_qwen_analysis/v5_cfd_diagnosis_and_plan.md | Mentve |
| Ez a doc | /data/Brain/_qwen_analysis/v5_cfd_full_state_save.md | Mentve |
| Session | /data/mcp_server/state/session_*_v5_cfd_full_state_before_shutdown.md | Mentve |

---

## KÖVETKEZŐ LÉPÉS (folytatáskor)
1. **Phase 1**: Diagnosztika — feature-label korreláció mátrix futtatása jules_cfd_v5.py-ben
2. **Phase 2**: Boolean/categorical feature-k implementálása compute_features()-ben
3. **Phase 3**: Címke javítás (asymmetrikus TB vagy return label)
4. **Phase 4**: 2 külön modell + Optuna
5. **HUD ZMQ debug**: copilot publish vs HUD subscribe mismatch
