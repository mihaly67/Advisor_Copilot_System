# Session: short_diag_v5_gyokerok_20260924
*Időbélyeg: 2026-09-24T02:46:23.523831*

# Short Diagnosztika V5 — 3 GYÖKÉROK azonosítva

## 1. KÖRKÖRÖS LABELING (fő hiba)
- dom_labeler_v5.py 96-99. sor: `if ADX<20 → Short, else → Noise`
- V5 modell Regime_ADX feature-t használ (SHAP_Short=2.46, #1)
- TAUTOLOGIA: label és feature ugyanazt az információt hordozza
- Short barok 100%-a ADX<20 — a modell csak memorizálja a szabályt
- OOS: 62.6% Short barokon Long-ot mond (nem tud generalizálni)

## 2. ASZIMMETRIKUS PT
- PT_Long=1.2$, PT_Short=1.8$ (50% nagyobb)
- Kisebb esések Noise-ba kerülnek → kevesebb Short tanulópélda
- Short win/loss ratio = 0.55 (torzított)

## 3. 6/8 FEATURE NEM DISZKRIMINÁL
- Cohen's d ≈ 0 for 6 feature (ATR_Micro, RSI, Kyle_Lambda, stb.)
- Csak Regime_ADX (d=-1.23) és Regime_Trending (d=-1.19) diszkriminálnak — de körkörösek
- Nincsenek Short-specifikus feature-ök

## JAVASLAT:
1. Regime filter eltávolítása labelingből
2. Szimmetrikus PT (PT_Short=1.2$)
3. Short-specifikus feature-ök (bearish rejection, volume imbalance, momentum)
4. Regime_ADX kivenni feature-ökből és tesztelni mi marad

## Fájlok:
- Diagnosztika: /data/Brain/_qwen_analysis/SHORT_DIAGNOSTIKA_V5_GYOKEROK.md
- Script: /data/mcp_server/state/short_diag.py
- Labeling kód: /data/dev/projects/z-ai-copilot/src/dom_labeler_v5.py (96-99. sor a hiba)