# Rendszerszintű Repo Katalógus — Scalper Copilot

> Generated: 2026-10-14 | 195 repo scanned (/data/ml: 120, /data/Brain: 75)

## 3 CRITICAL (kötelező)
- **financial-ml-toolkit** — TBM, CUSUM, dollar bars, features, weights, PurgedKFold
- **LightGBM** — elsődleges modell: GOSS, EFB, leaf-wise
- **optuna** — hyperopt: TPE, pruning, multi-objective

## 21 HIGH (közvetlenül használható)
| Kategória | Repók |
|-----------|-------|
| Trading rendszerek | freqtrade (architektúra), qlib (pipeline), vectorbt (backtest), xauusd-scalping-ai (versenytárs) |
| Data mérnökség | triple_barrier (OOP TBM), mql-zmq (MT5↔Python bridge) |
| Feature mérnökség | ta-lib (150+ indikátor), AlphaPy (boolean features), shap (explainability) |
| Kísérlet/Modell | LightGBM-Quant (kvant minták), river (streaming ML + drift) |
| Értékelés | quantstats (Sharpe/tearsheet), barrier-method (referencia) |
| Agent/RAG | Qwen-Agent, langgraph, deepagents, MCP spec, LightRAG, sentence-transformers, cline |

## Kulcs architektúra minták
1. **Pipeline** (qlib+freqtrade): DataHandler→FeatureEngine→LabelEngine→ModelTrainer→Backtester→Executor
2. **Strategy** (freqtrade): populate_indicators → populate_buy_trend → populate_sell_trend
3. **Online learning** (river): model.learn_one(x,y) → modell adaptáció concept drift ellen
4. **Vectorized backtest** (vectorbt): vbt.Portfolio.from_signals() → gyors OOS
5. **SHAP selection** (shap): TreeExplainer → feature importance → pruning

## RAG/Vektorizáció
| DB | Chunks | Tartalom |
|-----|--------|----------|
| ml_rag_v2.db | 333K+ | ML kód FAISS |
| brain_rag.db | 247K | Agent/RAG/MCP |
| knowledge | 966 | LGBM_copilot tudástér |

Eszözök: ml_vectorize_v2.py, brain_vectorize.py, knowledge_vectorize.py, faiss_search.py
Embedding: all-MiniLM-L6-v2 (384 dim, P4000 GPU)

## Vizualizáció
| Eszköz | Relevancia | Funkció |
|--------|-----------|---------|
| quantstats | HIGH | Sharpe, drawdown, tearsheet |
| shap viz | HIGH | Feature importance viz |
| pyqtgraph | MEDIUM | Desktop fast plotting |
| plotly | MEDIUM | Interactive web charts |

## 35 MEDIUM repo (referenciaként)
Data: findatapy, finmarketpy, ArcticDB, prefect, zenml, mt5linux
Feature: pyts, stumpy, hmmlearn
Kísérlet: mljar-supervised, tensorboard
Portfolio: PyPortfolioOpt, Riskfolio-Lib
Idősor: Time-Series-Library, Financial-TS-Forecast
Anomaly: dtaianomaly, hidden_markov
Agent: langchain, autogen, chroma, qdrant, mem0, graphrag
RAG: sqlite-vec, anubis-mcp, yggdrasil-mcp
Viz: chartpy, plotly, pyqtgraph