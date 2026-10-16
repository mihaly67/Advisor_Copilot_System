# Jules Gépe — Teljes Környezet (Anti-amnézia)
*Utolsó frissítés: 2026-09-23*
***EZ A FŐ REFERENCIA. Ha bármi hol van kérdés, IDE NÉZZ!***

## Hardver
- CPU: Intel Xeon E5-2673 v4 @ 2.30GHz, 20c/40t
- RAM: 62 GB
- GPU0: Quadro P4000 8GB (Qwen LLM)
- GPU1: Quadro P2000 5GB
- /data: 219GB (183 szabad)
- /home: 156GB (34 szabad)

## MT5 Wine
`/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/`
Scripts: .../MQL5/Scripts/ | Indicators: .../MQL5/Indicators/Indicators/ | Files: .../MQL5/Files/

## Python venv
`/home/Jules/jules_venv/` (python3, pip)
ta 0.11.0, lightgbm 4.7.0, optuna 5.0.0, scikit-learn 1.8.0, pandas 3.0.3, numpy 2.4.6, shap 0.51.0, joblib 1.5.3, pyzmq 27.2.0, PyQt5 5.15.10, pyqtgraph 0.14.0, matplotlib 3.11.1

## Munkaterület
- /data/dev/ — Git repo, központi dev workspace
- /data/dev/projects/scalper-copilot/ — Jules eredeti (MARAD, nézelődés)
- /data/dev/projects/z-ai-copilot/ — ÚJ projekt (LÉTREHOZANDÓ)
- /home/Jules/LGBM_mlops/ — Jules eredeti projekt (MARAD)

## Kulcs útvonalak
| Mi | Hol |
|---|---|
| Cline workspace | /home/Jules/zhipu_projekt/ |
| venv | /home/Jules/jules_venv/ |
| MT5 | /home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/ |
| Munkaterület | /data/dev/ |
| Jules projekt | /home/Jules/LGBM_mlops/ |
| Pipeline | /home/Jules/LGBM_mlops/Micro_LGBM/src/ |
| Master CSV | /home/Jules/LGBM_mlops/Master_csv/ |
| Z.ai Copilot (új) | /data/dev/projects/z-ai-copilot/ |
| Brain | /data/Brain/ |
| Qwen elemzések | /data/Brain/_qwen_analysis/ |
| MCP | /data/mcp_server/ |
| RAG DB | /data/Brain/_vectorized/brain_rag.db |

## Pipeline terv
1. Tick gyűjtő (MQ5): Scalper_Copilot_Miner_v1 ✅
2. Dollar bar (Python): prado_dollar_bars.py módosítva
3. Feature eng (Python): dom_feature_engineer_mtf.py + NavSystem v2.22
4. Labeling: dom_labeler_v5.py
5. Betanítás: train_lgbm_fusion_v5.py
6. SHAP + Optuna: feature szelekcó + 4D küszöb