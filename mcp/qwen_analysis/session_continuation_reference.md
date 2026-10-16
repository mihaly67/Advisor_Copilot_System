# Z.ai Copilot — Session Folytatás Referencia

**Utoljára frissítve**: 2026-10-03
**Státusz**: Jules visszafejtés KÉSZ, implementáció következik

---

## Hol tartunk?

### KÉSZ:
- ✅ Jules rendszer teljes visszafejtése (27+4 script átolvasva)
- ✅ 7 alapelv rekonstruálva
- ✅ 10 feature, labeler, trainer, döntés logika dokumentálva
- ✅ Z.ai implementációs terv megvan
- ✅ Minden mentve (lást: Mentett fájlok alább)

### KÖVETKEZŐ LÉPÉS:
1. **Dollar Bar Engine** implementálása Z.ai-ban ($444K, O(1) OHLC)
2. **10 Feature** kalkuláció (6 Dist + 2 Wick + Stoch + Tick_Speed)
3. **LGBM UJRA tanítani** dollar bar adaton
4. **Döntés logika** (4D threshold + Stoch filter + stability)
5. **O(1) architektúra** (dict+Lock, nincs Pandas élőben)

### KIHAGYVA (nem kell v1):
- ❌ LSTM Meta-Advisor
- ❌ CatBoost
- ❌ Kaufman AMA

### NYITOTT KÉRDÉS:
- Z.ai honnan kapja a ZigZag pivotokat és Stoch_K-t?

---

## Mentett fájlok

| Fájl | Tartalom |
|------|----------|
| `/data/Brain/_qwen_analysis/jules_deep_script_analysis.md` | Teljes visszafejtés (95 sor) |
| `/data/mcp_server/state/session_jules_reverse_engineering.json` | Strukturált state (15 key, 10 feature, 5 plan) |
| `/home/Jules/.cline/mcp.json` | MCP bridge konfig (új session-től él) |

---

## Jules referencia fájlok (NEM MÓDOSÍTANDÓ!)

| Script | Útvonal |
|--------|---------|
| Live Copilot | `/data/dev/projects/scalper-copilot/Micro_LGBM/src/mt5_live_copilot_v2.00.py` |
| Dollar Bar Engine | `/data/dev/projects/scalper-copilot/Micro_LGBM/src/prado_dollar_bars.py` |
| Feature Fúzió | `/data/dev/projects/scalper-copilot/Micro_LGBM/src/fuse_macro_to_dollar_bars.py` |
| Labeler V5 | `/data/dev/projects/scalper-copilot/Micro_LGBM/src/dom_labeler_v5.py` |
| Trainer V5 | `/data/dev/projects/scalper-copilot/Micro_LGBM/src/train_lgbm_fusion_v5.py` |
| Macro Feature | `/data/dev/projects/scalper-copilot/Macro_Regime/src/macro_feature_engineer.py` |
| Pipeline Master | `/data/dev/projects/scalper-copilot/Micro_LGBM/src/pipeline_master.py` |
| Jules Model | `/home/Jules/LGBM_mlops/Micro_LGBM/models/lgbm_model_fusion_v5_tuned.pkl` |

---

## Kritikus számok

| Param | Érték |
|-------|-------|
| Dollar Bar Threshold | $444,000 |
| PT (Profit Target) | $1.5 |
| SL (Stop Loss) | $1.0 |
| Max Bars | 5 |
| P_LONG_MIN | 0.350 |
| P_SHORT_MIN | 0.360 |
| P_NOISE_MAX | 0.470 |
| Stability Window | 3 (deque maxlen) |
| ATR Window | 15 (deque maxlen) |
| LGBM n_estimators | 781 |
| LGBM learning_rate | 0.0142 |
| LGBM num_leaves | 57 |
| LGBM max_depth | 6 |
| LGBM min_child_samples | 24 |
| LGBM colsample_bytree | 0.566 |
