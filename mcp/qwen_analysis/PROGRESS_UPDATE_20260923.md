# Progress Update — 2026.09.23.

## Kész ✅
- [x] CSV gyűjtő scriptek feltérképezése (6 CSV, 16 MQ5 script)
- [x] Jules tényleges pipeline azonosítása (2 MQ5 + 5 Python script)
- [x] Nem használt scriptek kizárása (Gemini&User, régi verziók, DOM, Macro)
- [x] Scalper_Copilot_Miner_v1 CSV (811 MB, 18 oszlop) pipeline-ba integrálhatóság bizonyítva
- [x] 3 lépcsős pipeline terv kidolgozva (Tick gyűjtő → Dollar bar → Feature engineering)
- [x] Feature felbontás: ki számolja mit (MQ5 makró vs Python mikro)
- [x] Dollár Bar elmélet rögzítve (López de Prado, $444k küszöb, időfüggetlenség)

## Folyamatban ⏳
- [ ] Pipeline terv kiegészítése (user inputra vár)
- [ ] prado_dollar_bars.py módosítása az új 18 oszlopos CSV-hez
- [ ] dom_feature_engineer_mtf.py módosítása
- [ ] Pipeline tesztfuttatás
- [ ] SHAP + Optuna feature szelekcó

## Terv mentve
- MCP session: `scalper_pipeline_terv_3lepcsos_20260923`
- Brain: `/data/Brain/_qwen_analysis/SCALPER_PIPELINE_PLAN_20260923.md`