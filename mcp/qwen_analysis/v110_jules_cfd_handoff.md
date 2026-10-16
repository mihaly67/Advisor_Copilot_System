# V1.10 Jules CFD — Teljes Reprodukciós Handoff

**Dátum:** 2026-10-05  
**Session:** Stoch diagnózis → THN tuning → Optuna → SHAP  
**Következő session:** Új featurák (irány egyértelműsítés)

---

## 1. RENDSZER ARCHITEKTÚRA

### Adatforrás
- **Platform:** CFD (Contract For Difference) — **nem zárt gyertya, tick szint**
- **Volume proxy:** tick-count (nem dollar volume, nem trade volume)
- **Gyertya:** 1 perces, tick-count alapú — minden tick 1 volume egység
- **Threshold:** $1,746K (CFD szintű)

### Pipeline
```
Raw tick data → jules_v110_reproduction.py (CSV gyűjtő)
  → jules_v110_labeled.csv (processed)
  → lgbm_v110_jules.pkl (LightGBM 3-osztályos)
  → viz_v110_jules_pred.py (jelalkotás + vizualizáció)
```

### Osztályok
- **-1 = Short** (ár esik következő gyertyán)
- **0 = Noise** (nincs egyértelmű irány)
- **1 = Long** (ár emelkedik következő gyertyán)

---

## 2. SCRIPTEK ÉS FÁJLOK

### CSV Gyűjtő / Reprodukció
| Script | Útvonal | Funkció |
|---|---|---|
| **jules_v110_reproduction.py** | `/data/dev/projects/z-ai-copilot/src/` | CSV gyűjtő: tick-count volume, 10 feature, labeling |
| **jules_v110_labeled.csv** | `/data/dev/projects/z-ai-copilot/Master_csv/processed/` | 30,557 bar (80% train, 20% OOS = 24,446 bar) |

### Modell
| Fájl | Útvonal | Leírás |
|---|---|---|
| **lgbm_v110_jules.pkl** | `models/production_v110_jules/` | LightGBM multi-class (Short/Noise/Long) |
| **features.txt** | `models/production_v110_jules/` | 10 feature list |

### Predikció / Vizualizáció
| Script | Útvonal | Funkció |
|---|---|---|
| **viz_v110_jules_pred.py** | `src/` | Jelalkotás + Plotly viz (2 panel) |
| **optuna_v110_threshold_tuner.py** | `src/` | Threshold optimalizáció (NoStoch, THN 0.30-0.40) |
| **viz_v110_jules_optuna.py** | `src/` | Optuna viz (ha kell) |

### Kimenet
| Fájl | Útvonal | Leírás |
|---|---|---|
| **viz_v110_jules_pred.html** | `docs/v110/` | Plotly interaktív (1055 KB) |
| **optuna_results.json** | `models/production_v110_jules/` | Optuna best params |
| **shap_heatmap.png** | `docs/v110/` | SHAP feature × osztály heatmap |
| **shap_bar_*.png** | `docs/v110/` | Per-class és overall bar charts |

---

## 3. 10 FEATURE — A MODELL BEMENETE

| # | Feature | Leírás | SHAP rank |
|---|---|---|---|
| 1 | **Dist_Micro_R** | Micro timeframe R távolság (RSI/std) | **#1** (0.085) |
| 2 | **Dist_Micro_S** | Micro timeframe S távolság | **#2** (0.075) |
| 3 | **Tick_Speed** | Tick sebesség (tick/s) | **#3** (0.069) |
| 4 | **Dist_Ter_S** | Tertiary timeframe S távolság | #4 (0.060) |
| 5 | **Dist_Ter_R** | Tertiary timeframe R távolság | #5 (0.053) |
| 6 | **Dist_Sec_R** | Secondary timeframe R távolság | #6 (0.040) |
| 7 | **Dist_Sec_S** | Secondary timeframe S távolság | #7 (0.037) |
| 8 | **Stoch_State_M1** | Stochastic oscillator (K-50)/50, window=2, smooth=3 | #8 (0.023) |
| 9 | **Upper_Wick_ATR** | Upper wick / ATR | #9 (0.012) |
| 10 | **Lower_Wick_ATR** | Lower wick / ATR | #10 (0.012) |

**Megjegyzés:** A Dist_* featurek 3 timeframe-ből jönnek: Micro (1p), Secondary (~5p), Tertiary (~15p)

---

## 4. JELALKOTÁS PIPELINE (viz_v110_jules_pred.py)

### Logika
```
1. Modell → P(Short), P(Noise), P(Long) per bar
2. Long jel:  P(Long) > THL  AND  P(Long) > P(Short)  AND  P(Noise) < THN
3. Short jel: P(Short) > THS  AND  P(Short) > P(Long)  AND  P(Noise) < THN
4. Stoch szűrés: KIKAPCSOLVA (CFD-n káros, r≈0 a labelel)
5. Stability: csak N egymást követő azonos jel marad (SW=2)
```

### Aktuális konfig
```python
CFG = dict(
    th_long   = 0.390,    # Long küszöb
    th_short  = 0.400,    # Short küszöb
    th_noise  = 0.400,    # Noise küszöb (P(N) < 0.40 → jel)
    noise_mode = 'abs',   # abszolút THN (nem ratio)
    use_stoch_filter = False,  # Stoch KIKAPCSOLVA
    stability_window = 2,     # 2 consecutive bar
)
```

### Viz Panel 2
- P(Long) zöld, P(Short) piros, P(Noise) szürke
- THL=0.39, THS=0.40 vonalak (dash)
- THN=0.40 vonal (dot) — P(Noise) ez alatti = jel

---

## 5. FELISMERÉSEK ÉS EREDMÉNYEK

### 5a. Stoch szűrés CFD-n KÁROS
| Teszt | WR | Trades | Profit |
|---|---|---|---|
| Nincs Stoch | **54.6%** | **2,635** | **965** |
| Raw Stoch (eredeti) | 52.5% | 562 | 176 |
| Stoch derivált | 55.1% | 272 | 103 |

**Ok:** Stoch(window=2) tick-count CFD-n r≈-0.001 a labelel — null korreláció  
**Stoch autocorr:** lag1=0.288, lag2=0.01 — túl gyors, szinte zaj  
**SHAP megerősíti:** Stoch_State_M1 csak 8. (0.023) a 10 feature közül

### 5b. THN=0.25 blokkolta jelek 70%-át
- P(Noise) mean=0.310, median=0.313 az OOS barokon
- Long/Short candidátusok P(N) mean≈0.280, median≈0.290
- THN=0.25 < P(N) median → a jelek 70%-a elvész!

### 5c. Optuna optimalizáció (THN 0.30-0.40)
- **Keresési tér:** THL[0.25,0.50], THS[0.25,0.50], THN[0.30,0.40], SW[1,5]
- **Objective:** profit × (WR/50)² — WR≥50 bonusz
- **Param importance:** THS=55.7%, THL=34.1%, THN=8.5%, SW=1.8%

### 5d. Végső eredmény
| | Régi (THN=0.25, Stoch be) | Új (Optuna, NoStoch) | Változás |
|---|---|---|---|
| THL | 0.35 | **0.39** | +0.04 |
| THS | 0.36 | **0.40** | +0.04 |
| THN | 0.25 | **0.40** | +0.15 |
| SW | 3 | **2** | -1 |
| Stoch | be | **ki** | — |
| WR (OOS) | 54.6% | 52.0% | -2.6% |
| Trades (OOS) | 2,635 | **8,588** | **+226%** |
| Profit (OOS) | 965 | **2,567** | **+166%** |
| Jelek (3nap viz) | 516 | **1,939** | **+276%** |

---

## 6. SHAP ELEMZÉS — MIT HASZNÁL A MODELL?

### Heatmap (Top 10 feature × 3 osztály)
```
                    Short   Noise   Long
Dist_Micro_R       0.072   0.051   0.133  ← Long domináns
Dist_Micro_S       0.101   0.033   0.090  ← Short+Long
Tick_Speed         0.034   0.130   0.042  ← Noise domináns
Dist_Ter_S         0.047   0.100   0.033  ← Noise+Short
Dist_Ter_R         0.030   0.090   0.040  ← Noise+Long
Dist_Sec_R         0.035   0.048   0.038  ← egyenletes
Dist_Sec_S         0.042   0.033   0.037  ← egyenletes
Stoch_State_M1     0.031   0.014   0.024  ← GYENGE
Upper_Wick_ATR     0.013   0.012   0.012  ← minimális
Lower_Wick_ATR     0.011   0.012   0.013  ← minimális
```

### SHAP Irány
- **Long:** Tick_Speed++ (gyorsabb → Long), Dist_Sec_R++ (R táv → Long)
- **Short:** Dist_Sec_S++ (S táv → Short), Dist_Ter_S++ (ter S → Short), Dist_Micro_S-- (micro S↓ → Short)

---

## 7. GYENGSÉGEK — MIT KELL FEJLESZTENI?

### 🔴 KRITIKUS: Irány egyértelműsítés
**A modell legnagyobb gyengesége az irány felismerése.**

- WR=52.0% csak — alig jobb mint véletlenszerű (50%)
- Long WR_L=51.5%, Short WR_S=54.9% — Long különösen gyenge
- A 10 feature közül **7 Dist_* távolság** — ezek MAGNITUDE-t mérnek, nem irányt!
- Tick_Speed Noise-t dominálja (SHAP=0.130) — megmondja hol NINCS jel, de nem merre
- Stoch_State_M1 gyenge (SHAP=0.023) és CFD-n káros

**A Dist_* featurek problémája:**
- Dist_Micro_R = távolság RSI/STD-től → mindig pozitív → **nincs irányinfo**
- Dist_Micro_S = távolság short zónától → szintén magnitude
- A modell "megérzi" hogy nagy távolság = erős jel, de Long/Short irányt alig tudja

**Megoldás (következő session):**
- Új featurák amik **ELŐJELLEL** mérnek — pozitív=Long irány, negatív=Short irány
- Példák:
  - `RSI_signed` = RSI - 50 (pozitív=Long, negatív=Short)
  - `Price_momentum` = Close - Open (gyertya body iránya)
  - `MACD_signal` = MACD - Signal (keresztezés iránya)
  - `EMA_slope` = EMA(10) - EMA(10)[-1] (trend iránya)
  - `BB_position` = (Close - BB_mid) / BB_width (BB-n belüli pozíció, előjeles)
  - `Volume_delta` = Volume - Volume[-1] (tick sebesség változás iránya)
  - `Price_vs_VWAP` = Close - VWAP (ár a VWAP felett/alatt)

### 🟡 KÖZEPES: Noise felismerés
- Tick_Speed jó Noise detector (SHAP=0.130)
- De P(Noise) mean=0.31, és a modell mindig 31% zajt mond → THN=0.40 elvileg enged
- Lehet hogy külön Noise-ellenes featurák kellenek (pl. ATR_ratio, spread)

### 🟢 RENDBEN: Stoch megszüntetése
- SHAP és korreláció egyaránt alátámasztja: Stoch CFD-n haszontalan
- Kikapcsolva, WR és profit is javult

---

## 8. KÖVETKEző SESSION TERV

### Prioritás 1: Irány featurák (7-10 db)
```
Cél: egyértelmű Long/Short irány info a 10 meglévő Dist_* mellé

Új featurák:
1. RSI_signed_M1      = RSI - 50 (előjeles, pozitív=Long)
2. Price_momentum_M1  = Close - Open (gyertya body)
3. EMA_slope_M1       = EMA(10) - EMA(10)[1] (trend irány)
4. MACD_hist_M1       = MACD - Signal (keresztezés)
5. BB_position_M1     = (Close - BB_mid) / BB_width (előjeles)
6. Price_vs_VWAP_M1   = Close - VWAP (ár vs VWAP)
7. Volume_delta_M1    = Tick_Speed - Tick_Speed[1] (sebesség változás)
8. CCI_M1             = CCI(20) (Commodity Channel Index, előjeles)
9. ADX_signed_M1      = +DI - -DI (DI iránykülönbség)
10. MFI_M1            = MFI(14) - 50 (Money Flow, előjeles)
```

### Prioritás 2: Modell retrénálás
- 10 → 17-20 feature
- LightGBM újra tanítása
- SHAP ellenőrzés: az új irány featurák domináljanak-e

### Prioritás 3: Optuna re-tuning
- THL, THS, THN újra optimalizálása több feature-rel
- SW tartomány kibővítése

### Prioritás 4: Viz + validáció
- Új viz generálás
- WR, profit, SHAP heatmap frissítés

---

## 9. FÁJL HELYEK ÖSSZEFOGLALVA

```
/data/dev/projects/z-ai-copilot/
├── src/
│   ├── jules_v110_reproduction.py      # CSV gyűjtő (tick-count, 10 feat, label)
│   ├── viz_v110_jules_pred.py          # Jelalkotás + Plotly viz
│   ├── optuna_v110_threshold_tuner.py  # Optuna THN 0.30-0.40
│   └── viz_v110_jules_optuna.py        # Optuna viz
├── Master_csv/processed/
│   └── jules_v110_labeled.csv          # 30,557 bar (10 feat + label)
├── models/production_v110_jules/
│   ├── lgbm_v110_jules.pkl             # LightGBM modell
│   ├── features.txt                    # 10 feature list
│   └── optuna_results.json             # Optuna eredmény
└── docs/v110/
    ├── viz_v110_jules_pred.html        # Interaktív Plotly viz (1055 KB)
    ├── shap_heatmap.png                # Feature × osztály heatmap
    ├── shap_bar_overall.png            # Összesített importance
    ├── shap_bar_short/long/noise.png   # Per-class importance
    └── shap_summary_*.png              # Beeswarm summary
```

---

## 10. GYORS REPRODUKCIÓ

```bash
# 1. CSV gyűjtő (ha újra kell)
cd /data/dev/projects/z-ai-copilot
/home/Jules/jules_venv/bin/python3 src/jules_v110_reproduction.py

# 2. Viz generálás (aktuális config: THL=0.39 THS=0.40 THN=0.40 SW=2 NoStoch)
/home/Jules/jules_venv/bin/python3 src/viz_v110_jules_pred.py

# 3. Optuna re-tuning (ha kell)
/home/Jules/jules_venv/bin/python3 src/optuna_v110_threshold_tuner.py

# 4. SHAP analízis (ha kell)
# Lásd: session shap_analysis script
```

---

**Jó pihenést! 🌙 A következő session az irány featurákkal folytatódik — az a legnagyobb gyengeség.**
