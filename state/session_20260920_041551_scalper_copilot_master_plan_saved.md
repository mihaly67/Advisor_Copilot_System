# Session: scalper_copilot_master_plan_saved
*Időbélyeg: 2026-09-20T04:15:51.105969*

## Mesterterv elmentve: /data/LGBM_copilot/docs/scalper_copilot_master_plan.md (260 sor, 8.1KB)

### 12 Fázis:
1. PRIMARY DATA: M1 + London/NYC sessions
2. MULTI-TIMEFRAME: M1/M5/M15/H1
3. FEATURES: 20-25 (pivot, trend, momentum, volatility, volume, regime)
4. SCALPING IDABLAK: Long ≤1.5h, Short ≤50 perc (SCALPER HALÁLA = 2 ÓRA)
5. DYNAMIC DOLLAR BAR: $80K XAUUSD (nem $444K!)
6. GYŰJTŐ SCRIPT: MT5 független (AI_Data_Collector_v10.0.mq5)
7. TRIPLE BARRIER: ATR-alapú, anti-overlabeling (0.5×ATR)
8. DUAL/MULTI SYSTEM: LGBM+LSTM stacking ensemble (Option 1 AJÁNLOTT)
9. WALK-FORWARD CV: Purged k-fold CV (k=5, purge=10, embargo=5)
10. ÉLES BACKEND: Unified thresholds (P_SIGNAL_MIN=0.350, P_NOISE_MAX=0.470)
11. LIVE BACKEND: TCP 5555/5556 + ZMQ PUB 5557
12. PLAYBACK TESZTELÉS: Multi-day CSV

### Merkava EA hibrid indikátor hívások (NavSystem-en keresztül):
- HybridContextIndicator_v3.28 → GetMicP/R/S(), GetSecP/R/S(), GetTerP/R/S()
- HybridMomentum_Pulse_v1.05 → GetHybridMACD(), GetPulse(), GetWPR(), GetStochK()
- HybridFlowIndicator_v1.126 → GetFlowMFI(), GetFlowROC(), GetFlowDelta()
- GetTrendFast/Medium/Slow/Super() → EMA(25/50/150/300)
- GetRSI(), p.velocity, p.acceleration (PhysicsEngine)

### Qwen MQL5 könyv elemzés LEÁLLÍTVA:
- 60/137 RAG téma kész (44%) — 9780 sor a DB-ben
- Túl lassú volt (2.1 perc/téma, 124 perc futás)
- Log backup: /data/mcp_server/logs/mql5_book_qwen_INTERRUPTED_20260920.log
- DB backup: /data/MQL5/mql5_native_knowledge_INTERRUPTED_20260920.db
- Később újraindítjuk gyorsabb konfigurációval

### GPU állapot:
- P4000: 8 MiB / 8192 MiB (0% util) — SZABAD
- P2000: 495 MiB / 5120 MiB (31% util) — kisebb használat

### Jules rendszer kritikai hibái (miből tanulunk):
1. ZigZag repainting leakage
2. Feature mismatch (29 vs 10)
3. Fixed vs ATR barrier mismatch
4. Dollar Bar threshold túl magas ($444K)
5. Max bars túl hosszú