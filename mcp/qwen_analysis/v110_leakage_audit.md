# V1.10 LEAKAGE AUDIT — VÉGSŐ EREDMÉNY

**Dátum:** 2026-10-06  
**Status:** LEKAPCSOLÁS ELŐTT  

---

## 🚨 TALÁLT PROBLÉMÁK

### 1. ❌ LOOKAHEAD BIAS — Dist_* és Wick_* feature-k (KRITIKUS)

**A mi scriptünk `compute_features()` újraszámolja a Dist_* és Wick_* feature-ket a CSV nyers oszlokaiból (Micro_R, Close, ATR14) — NELKÜL shift(1)!**

```
CSV Dist_Micro_R[t] = (Micro_R[t-1] - Close[t-1]) / ATR14[t-1]  ← SHIFTED ✅
Mi Dist_Micro_R[t] = (Micro_R[t] - Close[t]) / ATR14[t]         ← UNSHIFTED ❌
```

Ez **1 bar lookahead bias**-t okoz! A modell a bar[t] Close-ját látja a feature-ben, de a label[t] a bar[t+1]...bar[t+5] jövőjét predikálja.

**Hatás mértéke:**
- A Dist_Micro_R különbség (no_shift - shift1) std = 1.70
- Ez a feature std 10.8%-a → **nem elhanyagolható!**
- De a korreláció-audit szerint a |r| különbség csak 0.0008 → **kicsi, de szignifikáns lehet**

**Érintett scriptek:**
- `norm_ablation_study.py` — `compute_atr_norm()` és `compute_raw_pct()` NEM shiftel
- `direction_features_study.py` — `compute_features()` NEM shiftel

**NEM érintett:**
- `jules_v110_reproduction.py` — eredeti pipeline, step 9: `for f in JULES_FEATURES: df[f]=df[f].shift(1)` ✅
- A 8 irány feature (RSI_signed, MACD_Hist_ATR stb.) — a CSV-ből jönnek, MÁR shiftelve ✅

### 2. ⚠️ BB_ZScore és MFI_5 enyhe lookahead gyanú

A CSV-ben lévő `Micro_BB_ZScore` és `Micro_MFI_5` nagyobb korrelációt mutat shift nélkül mint shift(1)-el:
- BB_ZScore: diff = +0.0093 (határ felett)
- MFI_5: diff = +0.0053 (határ felett)

De: a CSV-ben ezek MÁR shiftelve vannak (az eredeti pipeline .shift(1)-et alkalmaz). A mi scriptünk a CSV értéket használja → **NEM lookahead ez esetben**. A korreláció-különbség a rolling feature-k lassú változásából eredeztethető.

### 3. ⚠️ Threshold optimalizáció OOS-on (INFORMATION LEAKAGE)

THL=0.390, THS=0.400, THN=0.400 — az `optuna_v110_threshold_tuner.py` az OOS-on optimalizált. Ha a threshold-ok az OOS-adatot látták, az **information leakage**! Ez mind a 6 modellünk eredményét érinti.

### 4. ⚠️ Nincs purged K-FOLD

Egyszerű 80/20 index-alapú split. A rolling feature-k (ATR14, RSI14, MACD) 14-26 bar lookback miatt ~14-26 bar overlap a train/OOS határon.

---

## ✅ NEM PROBLÉMA

1. **Stability filter** — csak múlt és jelen jeleket néz, NEM lookahead ✅
2. **Label lookahead** — a label szándékosan néz előre (triple barrier), ez OK ✅
3. **merge_asof backward** — a ZigZag pivot-ok és MTF adatok csak múltbeli értékeket használnak ✅
4. **Stoch irány-kizáró** — NEM lookahead (a Stoch_State_M1 már shiftelve van a CSV-ben) ✅

---

## 🔧 MEGOLDÁSOK (KÖVETKEZŐ SESSION)

### 1. Azonnal: shift(1) hozzáadása compute_features()-hez
```python
def compute_features(df):
    # ... feature számítás ...
    result = pd.DataFrame(f)
    # ANTI-LOOKAHEAD: shift(1) MINDEN feature-re
    for feat in FEAT_ALL:
        result[feat] = result[feat].shift(1)
    return result
```

### 2. VAGY: CSV-ben lévő shiftelt feature-k használata közvetlenül
A `jules_v110_labeled.csv` Dist_Micro_R stb. oszlopai MÁR shiftelve vannak — használjuk ezeket újraszámolás helyett!

### 3. Threshold audit
- THL/THS/THN-t walk-forward módon optimalizálni
- VAGY: fix threshold-ok használata (nem Optuna-tuned)

### 4. Purged K-Fold implementálás
- Train/OOS határon 14-26 bar purge
- VAGY: embargo period

---

## ⚡ VÁRHATÓ HATÁS A JAVÍTÁS UTÁN

A lookahead bias miatt a jelenlegi WR=56.0% valószínűleg **csökkenni fog** shift(1) hozzáadása után. Becslés:
- A 10.8%-os feature std különbség alapján ~1-2% WR csökkenés várható
- De a **valós** WR (lookahead nélkül) ez lesz — minden eddigi eredményt ezzel kell korrigálni!

**FONTOS: Minden eredményt ÚJRA kell futtatni shift(1)-el!**
