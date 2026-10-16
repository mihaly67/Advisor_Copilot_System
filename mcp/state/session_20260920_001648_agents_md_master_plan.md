# Session: agents_md_master_plan
*Időbélyeg: 2026-09-20T00:16:48.292480*

VEZÉRTERVEZET LÉTREHOZVA: /home/Jules/zhipu_projekt/agents.md (296 sor)

PROJEKT CÉL: MT5 EA + LightGBM + LSTM Copilot rendszer — Dollar Bar ($444K), Triple Barrier (Prado), PyQt5 HUD, MT5 EA ZMQ/TCP socket kommunikáció. Bizonyított >65% Win Rate vakteszten.

3 FÁZISÚ VEZÉRTERVEZET:
- FÁZIS 1: MT5 Wine környezet mélyelemzése — /home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/ (Include, Experts, Scripts). Merkava_Behavioral_Profiler v1.2-v2.6, SimplePortTester (TCP socket:5555), AI_Labeled_Data_Exporter_v8.1, Feature_Exporter_Script_v4, DataMiner_TickExporter.
- FÁZIS 2: MQL5 nyelv feldolgozása — Include/Trade/ (Trade.mqh), Include/Expert/ (Expert.mqh, Signal, Money, Trailing), Include/Indicators/, Include/Math/Stat/, Include/Math/Alglib/. RAG már létezik: /home/Jules/LGBM_mlops/query_mql5_rag.py (FAISS). Programozói szakkönyvek megvannak.
- FÁZIS 3: /data/ml 112 repó feldolgozása — Kritikusak: barrier-method-main + triple_barrier-main (triple barrier), LightGBM-main + LightGBM-Quant-Model-master, LSTM repók (Stock-Prediction-with-LSTM-GRU, LSTM-Autoencoders, Anomaly_Detect_LSTM), FinRL-master, vectorbt-main, qlib-main, mt5linux-master, mql-zmq, ta-lib-main, optuna-master, shap-master.

SUDO: Passwordless beállítva (/etc/sudoers.d/jules, Jules ALL=(ALL) NOPASSWD: ALL). Jelszó fájl: /data/mcp_server/secure/.sudo_key (1104, chmod 600).

LGBM_MLOPS ÁLLAPOT: A Copilot rendszer már működik — Dollar Bar, Triple Barrier, 3MTF (M15+M30), Feature Fusion (ZigZag+Stochastic+Dollar Bar), 4D Asymmetric Threshold, PyQt5 HUD. Rendszer: /home/Jules/LGBM_mlops/ (FINAL_COPILOT_METHODOLOGY_3MTF.md, prado_methodology_3MTF.md, LIVE_ARCHITECTURE_3MTF.md, MILESTONE_LIVE_ARCHITECTURE.md).

QWEN MCP INFRA: 19 modul, 3 réteg (Backend, MCTS Pipeline, QA/Memória). 239 Qwen elemzés 86 repóban. MCTS+HeterogeneousBackend+BeamSearch. Anti-hallucination 15+ validátor. Démonok: memory_event_watcher (root, fix-elve), hardware_monitor_v2 (Jules).