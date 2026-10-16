# Jules CFD — Adatarchitektúra Tisztázás

## Jelenlegi adatok (broker szerver)

### Elérhető adatok
| Forrás | Időtartam | Mennyiség | Megjegyzés |
|--------|-----------|-----------|------------|
| **Tick adat** | 2026.06.16 – 2026.09.01 | 4.15M tick (tanító) | Bid/Ask/volume másodperces |
| **Tick adat (vizsga)** | 2026.09.14 – 2026.09.18 | 386K tick | OOS / vizsga |
| **M1 gyertya** | Évek | Korlátlan | CopyRates(PERIOD_M1) |
| **M5/M15/M30/M60 gyertya** | Évek | Korlátlan | CopyRates(PERIOD_M*) |

### Megszorítások
- CFD-n (IC Markets XAUUSD) **nincs valódi trade volume** — TICK_FLAG_VOLUME sosem set
- Tick-count proxy: minden tick = 1 lot
- Bid_Volume/Ask_Volume: v2-ben valódi (ha elérhető), egyébként tick-count proxy

---

## CSV STRUKTÚRÁK

### 1. TICK CSV (Scalper_Copilot_MTF_Data_v2.csv)
**Gyűjtőscript:** `Scalper_Copilot_Miner_v2.mq5`
**Sorok:** ~4.15M (tanító 2.5 hónap), ~386K (vizsga 5 nap)
**Aggregáció:** Másodpercenkénti (1 sor = 1 másodperc utolsó tick)

| Oszlop | Típus | Leírás | Forrás |
|--------|------|--------|--------|
| Timestamp | datetime | Másodperc kezdete | tick time |
| Bid | float | Utolsó Bid ár | tick bid |
| Ask | float | Utolsó Ask ár | tick ask |
| Bid_Volume | float | Bid volume (valódi vagy proxy) | tick volume |
| Ask_Volume | float | Ask volume (valódi vagy proxy) | tick volume |
| Spread | float | Ask - Bid | számított |
| 1m_Close | float | M1 gyertya Close | CopyRates(PERIOD_M1) |
| 5m_Close | float | M5 gyertya Close | CopyRates(PERIOD_M5) |
| 15m_Close | float | M15 gyertya Close | CopyRates(PERIOD_M15) |
| 30m_Close | float | M30 gyertya Close | CopyRates(PERIOD_M30) |
| ATR_M15 | float | ATR(14) M15-on | iATR(PERIOD_M15, 14) |
| RSI_M15 | float | RSI(14) M15-on | iRSI(PERIOD_M15, 14) |
| Micro_R | float | Mikro ZigZag Resistance | CalcSR(M1, 15) |
| Sec_R | float | Szekunder ZigZag Resistance | CalcSR(M15, 5) |
| Ter_R | float | Tercier ZigZag Resistance | CalcSR(M30, 3) |
| Micro_S | float | Mikro ZigZag Support | CalcSR(M1, 15) |
| Sec_S | float | Szekunder ZigZag Support | CalcSR(M15, 5) |
| Ter_S | float | Tercier ZigZag Support | CalcSR(M30, 3) |

**18 oszlop, másodpercenként 1 sor**

---

### 2. ZIGZAG CSV (Master_ZigZag_XAUUSD_M1.csv)
**Gyűjtőscript:** Külön MQ5 script (ZigZag adatgyűjtő)
**Sorok:** ~M1 gyertyák száma (évekre)

| Oszlop | Típus | Leírás |
|--------|------|--------|
| Time | datetime | M1 gyertya idő |
| Open,High,Low,Close | float | M1 OHLC |
| TickVolume, RealVolume | int | Volume |
| Micro_R, Micro_S | float | Mikro ZigZag R/S |
| Sec_R, Sec_S | float | Szekunder ZigZag R/S |
| Ter_R, Ter_S | float | Tercier ZigZag R/S |

---

### 3. DOLLAR BAR CSV (dollar_bars_adaptive.csv)
**Generátor:** `prado_dollar_bars.py`
**Bemenet:** Tick CSV → kumulatív dollar value threshold ($444K)
**Sorok:** ~42K (tanító 2.5 hónap)

| Oszlop | Típus | Leírás |
|--------|------|--------|
| Start_Timestamp, End_Timestamp | datetime | Bar időtartam |
| Open, High, Low, Close | float | OHLC (Mid_Price) |
| Num_Ticks | int | Tick-ek száma a bar-ban |
| Total_Dollar_Value | float | Kumulatív dollar value |
| Avg_Spread | float | Átlagos spread |
| Close_1m/5m/15m/30m | float | MTF Close (forward-fill) |
| ATR_M15, RSI_M15 | float | Indikátorok (forward-fill) |
| Micro_R/S, Sec_R/S, Ter_R/S | float | ZigZag S/R (forward-fill) |
| Bar_Duration_Sec | int | Bar időtartama másodpercben |

---

### 4. FEATURES CSV (features_dollar_bars.csv / nav_v31_*.csv)
**Generátor:** Feature engineering pipeline
**Bemenet:** Dollar bar CSV → feature computation
**Sorok:** Ugyanannyi mint dollar bar

Két verzió:
- **Alap (54 oszlop):** `features_dollar_bars.csv` — Dist_*, Tick_Speed, Price_Velocity, RSI, MACD, stb.
- **Teljes (170 oszlop):** `nav_v31_train.csv` — +Bar_Direction, NavSystem direction, Regime, microstructural, stb.

**Kritikus feature-k amik hiányozhatnak az alap CSV-ből:**
- `Bar_Direction` — (Close-Open)/(High-Low), buying/selling pressure
- `DF_Direction`, `MACD_Direction`, `Nav_Consensus` — NavSystem irány
- `Regime_ADX`, `Regime_Trending` — Környezeti kontextus

---

## PIPELINE ARCHITEKTÚRA (v4 meta-labeling)

```
┌─────────────────────┐
│  TICK CSV (18 col)   │  4.15M sor (2.5 hónap)
│  Scalper_Copilot_    │  Másodperces aggregáció
│  MTF_Data_v2.csv     │  Bid/Ask/MTF/SR/Indikátorok
└──────────┬──────────┘
           │
           ▼  prado_dollar_bars.py ($444K threshold)
┌─────────────────────┐
│  DOLLAR BARS         │  ~42K bar
│  OHLC + ZZ/MTF/Ind   │  Information-equivalent sampling
└──────────┬──────────┘
           │
           ▼  compute_features_v4() — 15 feature
┌─────────────────────┐
│  FEATURES            │  S/R + Bar_Dir + Momentum + Trend + Regime
│  (shift(1) leakfix)  │
└──────────┬──────────┘
           │
           ▼  CUSUM filter (s_pos/s_neg, 1.5x daily vol)
┌─────────────────────┐
│  CUSUM EVENTS        │  ~10K event (24.6% of bars)
│  + direction (+1/-1) │  Structural shift detection
└──────────┬──────────┘
           │
           ▼  Triple Barrier (PT=$1.5, SL=$1.0, MB=5)
┌─────────────────────┐
│  LABELED EVENTS      │  Long/Short/Noise at CUSUM events
└──────────┬──────────┘
           │
           ▼  Meta-Labeling (Prado CH3)
┌─────────────────────┐
│  PRIMARY: CUSUM dir  │  → side prediction (+1=Long, -1=Short)
│  SECONDARY: LightGBM │  → meta-label (1=follow, 0=skip)
│  FINAL: side * meta  │  → Long/Short/Skip
└─────────────────────┘
```

---

## HIÁNYZÓ ADATOK / AMIT MÉG KELL

### 1. NavSystem indikátorok a Tick CSV-ben
**Probléma:** A Tick CSV csak ATR_M15 + RSI_M15 indikátorokat tartalmaz.
A NavSystem (Pulse/Flow/Context/Momentum) indikátorok NINCSNEK benne.
**Megoldás:** Új gyűjtőscript ami a Tick CSV-hez hozzáadja a NavSystem értékeket,
vagy a feature engineering pipeline számolja őket Python-ból a dollar bar OHLC-ről.

### 2. Regime indikátorok
**Probléma:** Regime_ADX, Regime_Trending hiányozhat az alap Tick CSV-ből.
**Megoldás:** Számolható a dollar bar Close-ból Python-ból (rolling ADX).

### 3. Hosszabb vizsga adat
**Probléma:** Vizsga csak 5 nap (386K tick). Több kell a statisztikai szignifikanciához.
**Megoldás:** Újabb tick adat gyűjtése a broker-ről.

### 4. Volume microstructure (ha elérhető)
**Probléma:** CFD-n nincs valódi volume. Kyle_lambda, Amihud_Illiq, VPIN stb.
csak tick-count proxy-val számolhatók.
**Megoldás:** Ha a broker valaha valódi volume-t ad, újra kell gyűjteni az adatot.

---

## JAVASOLT ÚJ GYŰJTŐSCRIPT

### Scalper_Copilot_Miner_v3.mq5
Cél: A v2 kiterjesztése NavSystem indikátorokkal.

**Új oszlopok (v2 18 → v3 ~30):**
- `Nav_Pulse_MACD` — MACD hisztogram (Pulse)
- `Nav_Pulse_DF_Curve` — DF görbe (árgyorsulás)
- `Nav_Flow_MFI` — MFI (volumenetikus áramlás)
- `Nav_Flow_Delta` — Flow Delta (buy vs sell)
- `Nav_Flow_VROC` — VROC (volume rate of change)
- `Nav_WPR` — WPR (Williams %R)
- `Nav_Stoch_K` — Stochastic K
- `Nav_RSI_Fast` — RSI(5) fast
- `Nav_Context_Trend_Fast` — EMA(8) távolság
- `Nav_Context_Trend_Medium` — EMA(21) távolság
- `Nav_Context_Trend_Slow` — EMA(50) távolság
- `Regime_ADX` — ADX(14)
- `Bar_Direction` — (Close-Open)/(High-Low) pre-computed

VAGY: Python feature engineering pipeline számolja ezeket a dollar bar OHLC-ről.
