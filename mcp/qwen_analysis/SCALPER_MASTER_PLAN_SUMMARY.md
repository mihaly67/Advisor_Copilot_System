# SCALPER COPILOT — VÉGLEGES MESTERTERV v2.0

**Dátum:** 2026.09.22.
**Állapot:** ✅ VÉGLEGES — minden korábbi terv törölve

---

## TÖRTÉNET:
- v1.0 (2026.09.20) — TÖRÖLVE ❌
- v1.1 (2026.09.22) — TÖRÖLVE ❌
- v1.2 (2026.09.22) — TÖRÖLVE ❌
- **v2.0 (2026.09.22) — EGYETLEN ÉRVÉNYES TERV** ✅

---

## 3 LÉPCSŐ = KÉSZ COPILOT RENDSZER

### LÉPCSŐ 1: LGBM Copilot Hibajavítás → Működő (2-3 hét)
- Meglévő kód: `mt5_live_copilot_v2.00.py`, `train_lgbm_fusion_v5.py`, `dom_feature_engineer_mtf.py`, `dom_labeler_v5.py`, `hud_v1.16.py`, `pipeline_master.py`
- ÚJ CSV → pipeline → tanítás → vakteszt → gyorsított szimuláció → éles validáció → HUD javítás

### LÉPCSŐ 2: GAF-CNN + GAN Predikció Bővítés (2-3 hét)
- LGBM + CNN együtt vagy külön (teszt dönt)
- Ha együtt: vizualizáció (két eltérő módszer egy HUD-on)
- Ha nem: külön predikció, kereskedő dönt
- Alternatíva: egyik felülbírál, de marad külön
- RAG: cnn_gaf-master, scafe-master, Series2GAF-master

### LÉPCSŐ 3: Python EA + Kereskedelmi Panel (2-3 hét)
- Platform-független API absztrakció (MT5/TV/IBKR/Mock)
- Grafikus panel: chart + kezelő + platform választó
- TV önálló asztal, MT5 tálcán, broker nem érzékel
- RAG: metatrader-mcp-server, tradingview-mcp, lightweight-charts

---

## ALAPelvek:
1. Meglévő váz, hibajavítás — nem nulláról
2. GAF-CNN+LGBM: együtt vagy külön, vizualizáció ha együtt
3. Python EA + grafikus panel, TV-re is alkalmas
4. Platform-független (API a kulcs)
5. Robot irány TÖRÖLVE — Copilot only
6. Minden pont külön tervezendő

---

**Fájl:** `/data/Brain/_qwen_analysis/SCALPER_MASTER_PLAN_v2.0.md` (22056 bájt)
**Session:** `scalper_master_plan_v2_final_20260922`