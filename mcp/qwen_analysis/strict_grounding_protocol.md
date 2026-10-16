# 🧠 Strict Grounding Protokoll — AGENTS.md Szabályrendszer

## VÁLTOZAT: 1.0 | Dátum: 2026-10-12
## CÉL: Kikényszeríteni az LLM-ből a hibátlan ML munkát a tudástér alapján

---

## SZABÁLY 1: SOHA NE ÍRJ ML ALGORITMUST FEJBŐL

**Minden** ML implementáció ELŐTT kötelező:

1. ✅ Olvasd el: `/data/Brain/_qwen_analysis/concept_map.json`
2. ✅ Keresd meg a releváns koncept-et (pl. "triple_barrier")
3. ✅ Olvasd el a Level 3 digest-ét (pl. `digest_triple_barrier.md`)
4. ✅ Olvasd el a referenciakódot (Level 4) célzottan — csak a szükséges függvényeket
5. ✅ CSAK UTÁNA implementálj — és **mindig** a referenciakód struktúráját kövesd!

**TILTOTT**:
- ❌ "Írok egy TBM-et..." — NEM! Olvasd el a `labeling.py`-t és `labeling_advanced.py`-t!
- ❌ "Kitalálok egy direction feature-t..." — NEM! Olvasd el `digest_direction_features.md`-t!
- ❌ "Egy sima K-Fold elég..." — NEM! Olvasd el `digest_sample_weights.md` PurgedKFold szekcióját!

---

## SZABÁLY 2: REFERENCIA HIVATKOZÁS KÖTELEZŐ

Minden implementált kódhoz kommentben hivatkozz a forrásra:

```python
# Based on: AFML Ch.3 / financial-ml-toolkit/labeling.py::triple_barrier_labels
# Adapted for: BTCUSD dollar bars, EWMA vol span=20
def my_triple_barrier_labels(close, ...):
```

---

## SZABÁLY 3: MARKET SPECIFICS KÖTELEZŐ BEOLVASÁS

Mielőtt BTCUSD kódot írsz, olvasd el:

```json
// concept_map.json → market_specifics.BTCUSD
{
  "instrument": "BTCUSD",
  "tick_size": 0.01,
  "point_value": 1.0,
  "pip_decimal_position": 2,
  "dollar_bar_threshold": 500000,
  "bar_type": "dollar_bar",
  "vol_method": "EWMA on returns, span=20",
  "notes": "No footprint data. Use OHLC+volume proxies for order flow."
}
```

**SOHA** ne számolj fejből kontraktusméretet, pip value-t, vagy tick size-t!

---

## SZABÁLY 4: DIRECTION FEATURE-K KÖTELEZŐ SORRENDJE

Ha direction model-t építesz, **csak** a `digest_direction_features.md`-ben listázott feature-eket használd, ebben a sorrendben:

1. DF_Curve (CUSUM sign) — PRIORITÁS 1
2. Flow_Delta (vol × close_position) — PRIORITÁS 2
3. PV_Correlation — PRIORITÁS 4
4. Momentum_Persistence — PRIORITÁS 5
5. Vol_Adj_Momentum — PRIORITÁS 6
6. Variance_Ratio_1_4 — PRIORITÁS 7

**TILTOTT**: RSI, StochasticK, ADX, ATR, Bollinger mint direction feature! Ezek AUC≈0.53!

---

## SZABÁLY 5: LABELING PIPELINE HELYES SORREND

1. **Side Labeling** (TBM vagy Trend Labeling) → label = +1/-1 (irány)
2. **Meta-Labeling** → label = 0/1 (trade filter, NEM irány!)
3. **SOHA** ne keverd a kettőt! A meta-label NEM direction prediction!

---

## SZABÁLY 6: SAMPLE WEIGHTS KÖTELEZŐ

Ha LightGBM-et tanítasz financial label-ekre:
- ✅ compute average_uniqueness
- ✅ compute return_attribution
- ✅ combine: uniqueness × return × time_decay
- ✅ pass `sample_weight` to `model.fit()`
- ❌ NEM szabad unweighted training financial label-ekkel!

---

## SZABÁLY 7: PURGED CV KÖTELEZŐ

- ✅ PurgedKFold vagy CPCV — standard K-Fold LEAKS!
- ✅ pct_embargo ≥ 0.01
- ❌ NEM szabad sklearn KFold-ot használni financial label-ekkel!

---

## KÖTELEZŐ OLVASMÁNYOK (MINDEN ML TASK ELŐTT)

1. `/data/Brain/_qwen_analysis/concept_map.json` — tudás-navigáció
2. `/data/Brain/_qwen_analysis/ml_knowledge_base_labeling_feature_engineering.md` — teljes tudásbázis
3. Releváns digest a concept_map alapján

---

## TUDÁSTÉR FÁJL INDEX

| Fájl | Szint | Tartalom |
|------|-------|----------|
| `concept_map.json` | Level 1 | Koncept → repo/fájd/függvény map |
| `digest_triple_barrier.md` | Level 3 | TBM implementáció + BTCUSD adaptáció |
| `digest_meta_labeling.md` | Level 3 | Meta-labeling pipeline + position sizing |
| `digest_direction_features.md` | Level 3 | Direction feature-ek + Python proxy kód |
| `digest_sample_weights.md` | Level 3 | Uniqueness, bootstrap, PurgedKFold |
| `digest_frac_diff.md` | Level 3 | Frakcionális differencia + min-d search |
| `ml_knowledge_base_labeling_feature_engineering.md` | Level 2-3 | Teljes tudásbázis (17KB) |
| `ml_knowledge_supplement_advanced.md` | Level 2-3 | Kiegészítés (7KB) |

---

## REFERENCIA REPO INDEX

| Repo | Útvonal | Relevancia |
|------|---------|-----------|
| financial-ml-toolkit | `/data/ml/Labelling.../financial-ml-toolkit-main/pipeline/` | **PRIMARY** — TBM, features, weights, CV |
| triple_barrier-main | `/data/ml/triple_barrier-main/` | OOP reference — Labeler, Orders, Types |
| LGBM-Stock-Prediction | `/data/ml/LGBM-Stock-Prediction-main/` | End-to-end LGBM pipeline |
| LightGBM-Quant-Model | `/data/ml/LightGBM-Quant-Model-master/` | Market indicators + LGBM |
| quant-ohlcv-feature | `/data/ml/Labelling.../quant-ohlcv-feature-master/` | 100+ OHLCV feature classes |
| mlfinlab | `/data/ml/Quant_Repos/mlfinlab/` | AFML hivatalos implementáció |
| Adv_Fin_ML_Exercises | `/data/ml/Quant_Repos/Adv_Fin_ML_Exercises/` | AFML könyv gyakorlatok |
