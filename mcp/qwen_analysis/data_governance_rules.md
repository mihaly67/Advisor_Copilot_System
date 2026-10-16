# 🗂️ LGBM Copilot — Adatkönyvtár Szabályzat (DATA GOVERNANCE)

## ⚠️ KRITIKUS SZABÁLY: SOHA TANÍTANI VIZSGA ADATON!

A `"külön_vizsga"` CSV **NEM tanító adat** — ez out-of-sample kiértékelő adat!
A `"Scalper_Copilot_MTF_Data_v2"` CSV **EZ a tanító adat** — 2.5 hónap tick adat.

---

## Könyvtárstruktúra

```
/data/LGBM_copilot/data/
├── raw/                          # TANÍTÓ adatok (szimbolikus linkek)
│   ├── BTCUSD/
│   │   ├── train_tick_BTCUSD.csv → Scalper_Copilot_MTF_Data_v2_BTCUSD.csv
│   │   └── M1_history_BTCUSD.csv → M1_History_BTCUSD.csv
│   └── XAUUSD/
│       ├── train_tick_XAUUSD.csv → Scalper_Copilot_MTF_Data_v2.csv
│       └── M1_history_XAUUSD.csv → M1_History_XAUUSD.csv
├── exam/                         # VIZSGA adatok (CSAK kiértékelés!)
│   ├── BTCUSD/
│   │   └── exam_tick_BTCUSD.csv → BTCUSD_külön_vizsga.csv
│   └── XAUUSD/
│       └── exam_tick_XAUUSD.csv → Scalper_Copilot_MTF_Data_külön_vizsga.csv
├── labeled/                      # Címkézett adatok (pipeline output)
├── processed/                    # Feldolgozott adatok (pipeline output)
└── synthetic_btcusd.csv          # Szintetikus teszt adat
```

## Fájl leírások

### BTCUSD

| Fájl | Eredeti név | Méret | Sorok | Időtartam | Típus | Cél |
|---|---|---|---|---|---|---|
| `train_tick_BTCUSD.csv` | Scalper_Copilot_MTF_Data_v2_BTCUSD.csv | 880 MB | ~5M | 2026-06-16 → 2026-09-01 | Tick (Bid/Ask+MTF) | **TANÍTÁS** |
| `M1_history_BTCUSD.csv` | M1_History_BTCUSD.csv | 85 MB | 1.38M | 2024-01-03 → 2026-09-01 | M1 OHLCV | Referencia/háttér |
| `exam_tick_BTCUSD.csv` | BTCUSD_külön_vizsga.csv | 54 MB | 323K | 2026-10-05 → 2026-10-08 | Tick (Bid/Ask+MTF) | **CSAK KIÉRTÉKELÉS** |

### XAUUSD

| Fájl | Eredeti név | Méret | Időtartam | Cél |
|---|---|---|---|---|
| `train_tick_XAUUSD.csv` | Scalper_Copilot_MTF_Data_v2.csv | 838 MB | ~2.5 hónap | **TANÍTÁS** |
| `M1_history_XAUUSD.csv` | M1_History_XAUUSD.csv | 62 MB | ~2.7 év | Referencia |
| `exam_tick_XAUUSD.csv` | Scalper_Copilot_MTF_Data_külön_vizsga.csv | 78 MB | 4 nap | **CSAK KIÉRTÉKELÉS** |

## CSV formátum

### Tick adat (train + exam)
```
Timestamp,Bid,Ask,Bid_Volume,Ask_Volume,Spread,1m_Close,5m_Close,15m_Close,30m_Close,ATR_M15,RSI_M15,Micro_R,Sec_R,Ter_R,Micro_S,Sec_S,Ter_S
2026.06.16 00:00:00.000,66489.58,66501.58,...
```

### M1 History
```
Timestamp,Open,High,Low,Close,TickVolume
2024.01.03 00:05:00,45103.87,45184.60,45055.61,45184.60,77
```

## Pipeline adatfolyam

```
raw/train_tick_*.csv  ──→  build_dollar_bars()  ──→  compute_bar_features()  ──→  label_triple_barrier()
                                                                                ──→  train models
                                                                                ──→  save models/

exam/exam_tick_*.csv  ──→  build_dollar_bars()  ──→  compute_bar_features()  ──→  model.predict()
                                                                                ──→  save preds (OOS!)
                                                                                ──→  build chart
```

## Törölt szennyezett fájlok (2026-10-16 tisztítás)

MINDEN ami a `BTCUSD_külön_vizsga.csv`-vel tanított pipeline-ből származott — TÖRÖLVE:
- models/scalper/BTCUSD_v4_* (összes v4 modell, meta, imp, preds)
- models/scalper/BTCUSD_v401_* (összes v4.01 modell)
- models/scalper/BTCUSD_scalper_* (összes régi scalper modell)
- models/scalper/BTCUSD_v3* (összes v3 modell)
- charts/BTCUSD_*.html + *.png (összes chart)
- data/features_*, labels_*, pipeline_result_*

Ezek mind 4 nap vizsga adaton tanított — ÉRVÉNYTELENek!

## Eredeti forrás (szimbolikus linkek)

```
/data/dev/LGB_copilot_system/RAW_CSV/BTCUSD/  ← eredeti hely
/data/LGBM_copilot/data/raw/BTCUSD/           ← symlink ide mutat
```

NEM duplikálunk — symlink használat, GB-ok spórolva.
