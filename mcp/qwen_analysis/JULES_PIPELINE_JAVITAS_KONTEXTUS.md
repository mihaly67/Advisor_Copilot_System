# Jules fusion_v5 Pipeline Javitas — Telles Kontextus (2026.09.25.)

> **Cel:** Jules pipeline lookahead bias javitasa, causal ZigZag, ujratanitas, OOS validacio.
> **Z.ai v1.04 ensemble NEM bolygatjuk** — mar stabil, WR=54.3%, Opp=0.

---

## 0. KULCS FELISMERES: Dollar Bar + Indikator Problem

### A problema
Dollar bar NEM idonalapu — $444K volume threshold:
- 1 dollar bar lehet 2 masodperc VAGY 30 perc
- RSI(14), Stoch(2,3), MACD(12,26) dollar baron → "14 periodus" = valtozo idotartam
- Klasszikus indikator elmelet EGYENES idokoztet feltetelez!

### Z.ai modszere: Indikator KOZVETLENUL a dollar baron
```python
# dom_feature_engineer_mtf.py — Z.ai
close = df['Close']  # dollar bar Close
df['Micro_RSI_14'] = ta.momentum.RSIIndicator(close, window=14).rsi()
stoch = ta.momentum.StochasticOscillator(high=high, low=low, close=close, window=14)
```
RSI(14) = utolso 14 DOLLAR BAR RSI-je → "volume-synchronized momentum"
- Elony: tobb info aktív piacon, kevesebb zaj csendes piacon (Lopez de Prado AFML)
- Hatrany: nem idokomparabilis, klasszikus RSI ertelmezes (>70 overbought) NEM valid

### Jules modszere: Ket vilag fuzioja
```
DOLLAR BAR vilag                M1 IDOALAPU vilag
─────────────────               ──────────────────
Tick_Speed                      Dist_Micro_R/S (M1 pivot tavolsag)
Wick_ATR                        Stoch_State_M1 (M1 Stoch)
Bar_Duration_Sec                (M1-bol merge_asof backward)

        └─────── merge_asof (backward) ──────────┘
                          │
                   FUZIO adat
```
- Elony: idokomparabilis indikatorok, klasszikus ertelmezes valid
- Hatrany: merge pontatlan lehet, dollár bar idobelyeggel M1 gyertya nem mindig align

### Melyik helyes?
MINDKET — mas informaciot kodolnak:
- Z.ai RSI(14) on dollar bars = volume-synchronized RSI (AFML style)
- Jules RSI/M1 merge = classical time-based RSI + dollar bar microstructure

Empirikusan a Z.ai modszzer MUKODIK (54.3% WR) — a volume-synchronized indikatorok
informacio-hatekonyabbak aktív piacon. A Jules modszer is valid, de a pivotoknak
causalisan kell szamolodniuk (nem batch exporttal).

---

## 1. A BIAS BIZONYITASA

### Eredeti teszt (Jules, jul 20-23)
- WR=84.5%, Profit=+3489, 2274 trades (568/day), Opp=336

### Szeptember OOS teszt (jul 24 - sep 1, 40 nap)
- WR=25.7%, Profit=-1776, 7746 trades, Opp=25.8%
- WR < veletlen (33%) = szisztematikusan rossz irany = anti-correlated pattern
- Feature ertekek kompatibilisek: Dist_Micro_R mean 2.641→1.775
- **Kovetkeztetes:** A szivargas a pivot ERTEKEKBEN van, nem a formulaban

### A szivargas lancolata
```
Master_ZigZag_GCEQ26_M1.csv (79052 sor, maj 3 - jul 31)
  ← MT5 HybridContextIndicator_v3.28 buffer export (FULL HISTORY)
    ← CZigZagEngine.Calculate() — extreme_search state machine
      ← Uj pivot felismeresekor TORLI a korabbit:
         ZigZagBuffer[last_low_pos]=0.0  ← VISSZAMENOLEG MODOSIT!
      ← Batch export: jovobeli ar "visszamenoleg atirja" multbeli pivotot

fuse_macro_to_dollar_bars.py
  ← merge_asof(df_micro, df_macro, direction='backward')
    ← Dist_Micro_R = (Micro_R - Close) / ATR_14  ← FORMULA JO
    ← DE: Micro_R batch-exportalt "tisztazott" pivot ← SZIVARGAS

train_lgbm_fusion_v5.py → lgbm_model_fusion_v5_tuned.pkl
  ← Modell megtanulja a "tisztazott" pivot tavolsag mintakat
  ← OOS: ezek a mintak NEM LETEZNEK → anti-correlated predikcio
```

### A live EA viszont CAUSALIS
```
Merkava_Behavioral_Profiler_v3.0_Online.mq5
  ← OnCalculate() bar-by-bar halad (shift=m_depth → rates_total)
  ← microZigZag.Calculate() streaming, csak az eddigi adaton
  ← FindHistoricResistance(MicroHigh, i, ...) visszafele keres
  ← MicroR1[i] = curr_r  ← EZ CAUSALIS!
  ← SocketSend(port=5555, JSON) ← causal pivot ertekek kuldes
  ← Python MacroReceiver(port=5555) fogadas
  ← Dist_Micro_R = (mic_r - close) / atr  ← CAUSALIS
```

---

## 2. PORT ARCHITEKTURA (3 port)

| Port | Protokoll | Irany | Tartalom | Causalis? |
|---|---|---|---|---|
| 5555 | TCP/JSON | EA→Python | Micro_R/S, Sec_R/S, Ter_R/S, Stoch_K, M1 OHLC | Igen |
| 5556 | TCP/JSON | EA→Python | Tick adatok (bid/ask, dollar bar agg) | Igen |
| 5557 | ZMQ PUB/SUB | Python→HUD | Jelzesek, pivot szintek, P_Long/P_Short | N/A |

---

## 3. JULES FEATURE FORMULA (pontos)

```python
ATR_14 = ta.volatility.AverageTrueRange(high, low, close, window=14)
Dist_Micro_R = (Micro_R - Close) / ATR_14   # pozitiv = R felett
Dist_Micro_S = (Close - Micro_S) / ATR_14   # pozitiv = S felett
Dist_Sec_R   = (Sec_R   - Close) / ATR_14
Dist_Sec_S   = (Close - Sec_S)   / ATR_14
Dist_Ter_R   = (Ter_R   - Close) / ATR_14
Dist_Ter_S   = (Close - Ter_S)   / ATR_14
Upper_Wick_ATR = (High - max(Open,Close)) / ATR_14
Lower_Wick_ATR = (min(Open,Close) - Low)  / ATR_14
Stoch_State_M1 = (Stoch(2,3) - 50) / 50   # [-1, +1]
Tick_Speed = 1.0 / Bar_Duration_Sec
```

### Z.ai vs Jules ELLENTES ELOJEL!
```python
# Jules:  Dist_Micro_R = (Micro_R - Close) / ATR  → pozitiv ha R > Close
# Z.ai:   Dist_Micro_R_ATR = (Close - Micro_R) / ATR  → negativ ha R > Close
```

---

## 4. Z.ai dom_feature_engineer_mtf.py — MUKODASI MOD

A Z.ai KOZVETLENUL a dollar baron szamolja az indikatorokat:
- NavSystem: RSI(14), Stoch(14,3), MACD(15,5,5), WPR(14), MFI(5) — dollar bar H/L/C
- Mikrostruktura: Roll Spread, Kyle Lambda, Amihud Illiq, VPIN — dollar bar
- Pivot distance: (Close - Micro_R) / ATR_M15 — EA-sent Micro_R, causal
- Geometria: Ter_R/S = rolling max/min 200 dollar bar — causal
- Pivot interakciok: Wick_Rej, Breakout, Breakdown — event-based, causal
- Anti-lookahead: MINDEN feature .shift(1)

Fontos: a Z.ai Scalper_Copilot_MTF_Data.csv mar tartalmazza az EA-sent
Micro_R/S, Sec_R/S, Ter_R/S ertekeket (port 5555)! A prado_dollar_bars.py
ezeket forward-fill-eli a dollar barba: ('Micro_R', 'last').

---

## 5. ZIGZAG PARAMETEREK (HybridContextIndicator_v3.28)

| Szint | Depth | Deviation | Backstep | Jelentes |
|---|---|---|---|---|
| Micro | 3 | 5 | 3 | 5 fel/5 le, 1 perces ablak |
| Secondary | 4 | 5 | 3 | Kozepes pivotok |
| Tertiary | 7 | 5 | 3 | Nagy strukturalt szintek |

---

## 6. MODELL PARAMETEREK

- Fajl: lgbm_model_fusion_v5_tuned.pkl
- Tipus: LGBMClassifier, 3-class [0=Short, 1=Noise, 2=Long]
- 10 feature: Tick_Speed, Dist_Micro_R, Dist_Micro_S, Dist_Sec_R, Dist_Sec_S, Dist_Ter_R, Dist_Ter_S, Stoch_State_M1, Upper_Wick_ATR, Lower_Wick_ATR
- Jelzes kuszobok: P_SIGNAL_MIN=0.494, P_NOISE_MAX=0.351
- Label konvencio: -1=Short, 0=Noise, 1=Long → LGBM y+1 → 0,1,2
- Profit matrix: LW=2.0, LL=-1.0, SW=2.0, SL=-1.0
- Labeling: triple barrier, PT=1.5, SL=1.0, max_bars=5

---

## 7. ELERHETO ADATOK

| Fajl | Idoszak | Sorok | Tartalom |
|---|---|---|---|
| Master_ZigZag_GCEQ26_M1.csv | maj 3 - jul 31 | 79052 | M1 OHLC + pivotok (BIAS!) |
| Scalper_Copilot_MTF_Data.csv | jun 15 - sep 1 | ~8M | Tick + EA-sent pivotok (causalis) |
| labeled_dollar_bars_v8.csv | jun 15 - sep 1 | 31139 | Dollar bar + feature + Target_Meta |
| features_dollar_bars.csv | jun 15 - sep 1 | 28212 | Dollar bar + 54 feature |
| meta_labeled_fused_v5_mom.csv | jul 20-23 | 4295 | Jules teszt adat (BIAS!) |
| labeled_dollar_bars_v5_strict.csv | maj 27 - jul 17 | nagy | Jules tanitasi adat (BIAS!) |

---

## 8. FAJL UTVONALAK

### Jules projekt
- Modell: /home/Jules/LGBM_mlops/Micro_LGBM/models/lgbm_model_fusion_v5_tuned.pkl
- Fuse script: /home/Jules/LGBM_mlops/Micro_LGBM/src/fuse_macro_to_dollar_bars.py
- Labeler: /home/Jules/LGBM_mlops/Micro_LGBM/src/dom_labeler_v5.py
- Feature eng: /home/Jules/LGBM_mlops/Micro_LGBM/src/dom_feature_engineer_mtf.py
- Dollar bar: /home/Jules/LGBM_mlops/Micro_LGBM/src/prado_dollar_bars.py
- Train: /home/Jules/LGBM_mlops/Micro_LGBM/src/train_lgbm_fusion_v5.py
- Live copilot: /home/Jules/LGBM_mlops/Micro_LGBM/src/mt5_live_copilot_v2.0_no_stoch.py
- OOS test: /home/Jules/LGBM_mlops/Micro_LGBM/src/sept_oos_bias_test.py
- ZigZag CSV (BIAS): /home/Jules/LGBM_mlops/Macro_Regime/data/Master_ZigZag_GCEQ26_M1.csv
- Feature eng (Macro): /home/Jules/LGBM_mlops/Macro_Regime/src/macro_feature_engineer.py

### MT5 EA / Indikatorok
- EA (v3.0): /home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Indicators/Jules/Merkava_Behavioral_Profiler_v3.0_Online.mq5
- Context indicator: /home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Indicators/Jules/HybridContextIndicator_v3.28.mq5
- NavSystem: /home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Indicators/Indicators/NavSystem_v2_22.mqh

### Z.ai projekt (NEM BOLYGATJUK)
- Gyoker: /data/dev/projects/z-ai-copilot/
- Modell: models/nav_3c_v1.04/ (LGBM+ET ensemble, WR=54.3%)
- dom_feature_engineer_mtf.py: indikatorok KOZVETLENUL dollar baron (volume-synchronized)
- prado_dollar_bars.py: EA-sent pivotok forward-fill dollar barba

### Adatok
- Raw tick: /home/Jules/LGBM_mlops/Master_csv/raw/Scalper_Copilot_MTF_Data.csv (850MB)
- V8 labeled: /home/Jules/LGBM_mlops/Master_csv/processed/labeled_dollar_bars_v8.csv

---

## 9. A JAVITASI TERV — RESZLETES

### Lepes 1: Python causal ZigZag engine
- Streaming, bar-by-bar — megegyezik az EA CZigZagEngine logikajaval
- Input: M1 OHLC adat
  - Opciok: (a) raw tick CSV-bol M1 aggregalva, (b) Master_ZigZag M1 oszlopaibol
  - AJANLAS: (b) — Master_ZigZag mar tartalmazza az M1 OHLC-t, csak a pivotokat ujra kell szamolni
- Output: Micro_R/S, Sec_R/S, Ter_R/S minden M1 bar-ra — CAUSALIS
- 3 hierarchikus ZigZag (depth=3/4/7, dev=5, back=3)
- FindHistoricResistance/Support visszafele keres (mint az EA)
- KULONBSEG: nem fut a teljes tortenetre, bar-by-bar halad, nem modosítja korabbi pivotokat

### Lepes 2: Causal feature dataset epites
- OPCIOK (ket ut):
  - (A) Jules modszer: dollar bar + M1 causal pivot merge_asof
  - (B) Z.ai modszer: dollar bar + causal pivot forward-fill + indikator dollar baron
  - AJANLAS: (A) — Jules architekturaval kompatibilis, a modell ujratanitasa egyszerubb
- Dollar bar epites a tick adatbol ($444K, tick-count proxy)
- M1 causal pivotok merge_asof backward a dollar barokra
- Feature szamitas a Jules formulaval (10 feature)
- Triple barrier labeling (PT=1.5, SL=1.0, max_bars=5)

### Lepes 3: Modell ujratanitas
- LGBMClassifier, 10 feature, 3-class
- Tanitasi idoszak: jun 15 - aug 15 (2 honap, causalis)
- OOS teszt: aug 16 - sep 1 (2 hetes true blind)
- Optuna kuszob kalibracio az OOS eredmenyen

### Lepes 4: Osszehasonlitas
- Uj Jules causal modell vs Z.ai v1.04 ensemble
- Ha WR > 55%: a pivot feature-ok ertekesek, uj kiindulopont
- Ha WR < 50%: a pivot koncepcio nem mukodik causalis kornyezetben
- Mindket eset tanulsagos

---

## 10. TANULSAGOK

1. Allapottarto indikator batch export = lookahead bias. ZigZag extreme_search visszamenoleg modosítja a korabbiakat. Csak shift(1)-es history-fuggetlen indikatorok biztonságosak batch modban.

2. WR < veletlen = szisztematikus anti-pattern. Ha WR < 33% (3-class), data leakage, nem overfit.

3. Feature ertekek kompatibilisek LEHETNEK, de a bemeneti adat mergezo. A formula jo, a pivot ertekek voltak biasosak.

4. A pivot koncepcio potenciálisan ervenyes. A live EA causalisan kuld pivotokat.

5. 3 port architektura mukodik elesben. A szivargas csak az offline pipeline-ben van.

6. Z.ai ensemble (54.3%) bizonyítottan tisztan causalis. Nem hasznal batch-exportalt ZigZag-ot.

7. Dollar bar + klasszikus indikator: ket megkozelites letezik. Z.ai: indikator dollar baron (volume-synchronized). Jules: indikator M1-en + merge_asof (ido-komparabilis). Mindket valid, mas informaciot kodol.

8. A Scalper_Copilot_MTF_Data.csv mar tartalmazza az EA-sent causal pivotokat! Nem kell uj ZigZag engine — lehet, hogy eleg megnyitni ezt a CSV-t es a benne levo Micro_R/S ertekeket hasznalni a tanitasi adatban.
