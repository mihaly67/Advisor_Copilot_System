#!/usr/bin/env python3
"""KG Seed Expansion: 30 → 100+ concepts."""
import sys; sys.path.insert(0, "/data/mcp_server/tools")
from knowledge_graph_tools import KnowledgeGraphDB, NodeKind, RelationType, ConceptNode

DB = "/data/mcp_server/data/knowledge_graph.db"
kg = KnowledgeGraphDB(DB)
s = kg.get_stats(); print(f"Before: {s['concepts']} concepts, {s['edges']} edges")

N=NodeKind; R=RelationType; C=ConceptNode
DATA = [
  # AFML
  ("afml-ch1","AFML Ch1",N.REFERENCE,"Bars, multi-product","financial"),
  ("afml-ch2","AFML Ch2",N.REFERENCE,"Dollar/time/tick/volume bars","financial"),
  ("afml-ch3","AFML Ch3",N.REFERENCE,"Triple Barrier, Meta-Labeling","financial"),
  ("afml-ch4","AFML Ch4",N.REFERENCE,"Sample weights, uniqueness","financial"),
  ("afml-ch5","AFML Ch5",N.REFERENCE,"Ensemble methods, bagging","financial"),
  ("afml-ch7","AFML Ch7",N.REFERENCE,"Purged K-fold CV","financial"),
  ("afml-ch9","AFML Ch9",N.REFERENCE,"Feature importance MDA/SHAP","financial"),
  ("afml-ch10","AFML Ch10",N.REFERENCE,"Bet sizing","financial"),
  ("frac-diff-theory","Fractional Differentiation",N.METHOD,"d=0.4 memory+stationarity","financial"),
  ("info-bars","Information-Driven Bars",N.METHOD,"Tick/dollar imbalance bars","financial"),
  ("avg-uniqueness","Average Uniqueness",N.CONCEPT,"Mean sample uniqueness","financial"),
  # Pipeline
  ("data-ingestion","Data Ingestion",N.MODULE,"Tick data, MQL5 reader","pipeline"),
  ("bar-construction","Bar Construction",N.MODULE,"Dollar/time/tick bar builder","pipeline"),
  ("feature-selection","Feature Selection",N.MODULE,"MDA/MFI+threshold pruning","pipeline"),
  ("feature-direction","Feature Direction",N.METHOD,"rsi_dir,macd_dir,bb_dir","pipeline"),
  ("label-generation","Label Generation",N.MODULE,"TB+meta-label pipeline","pipeline"),
  ("model-training","Model Training",N.MODULE,"LightGBM+purged CV","pipeline"),
  ("backtesting","Backtesting",N.MODULE,"Walk-forward with metrics","pipeline"),
  ("htf-trend-gate","HTF Trend Gate",N.METHOD,"5min EMA counter-trend filter","pipeline"),
  ("optuna-tuning","Optuna Tuning",N.METHOD,"Bayesian opt for barriers+model","pipeline"),
  # Model
  ("lgbm-classifier","LightGBM Classifier",N.MODULE,"Primary GBDT model","model"),
  ("lgbm-regressor","LightGBM Regressor",N.MODULE,"Regression variant","model"),
  ("meta-label-model","Meta-Label Model",N.MODULE,"Secondary: follow primary?","model"),
  ("feat-imp-mda","MDA Importance",N.METHOD,"Mean decrease accuracy","model"),
  ("feat-imp-shap","SHAP Values",N.METHOD,"Shapley explanations","model"),
  ("purged-kfold","Purged K-Fold",N.METHOD,"CV with embargo","model"),
  ("scoring-metric","Scoring Metric",N.CONFIG,"Weighted acc+recall+Sharpe","model"),
  ("early-stopping","Early Stopping",N.CONFIG,"Stop on val degradation","model"),
  # RAG/Infra
  ("yantrikdb-engine","yantrikdb Engine",N.MODULE,"Rust cognitive memory","rag"),
  ("cortexdb-grpc","cortexdb gRPC",N.MODULE,"Go shared-brain server","rag"),
  ("embedding-model","Embedding Model",N.METHOD,"MiniLM-6v2(384d)+potion-8M(256d)","rag"),
  ("hybrid-rag","HybridRAG",N.METHOD,"alpha*vec+(1-a)*graph+contra","rag"),
  ("kg-db","Knowledge Graph DB",N.MODULE,"SQLite WAL concepts/edges","rag"),
  ("seq-thinker","Sequential Thinker",N.METHOD,"5-phase reasoning","rag"),
  ("ctx-compressor","Context Compressor",N.METHOD,"Token-optimal context","rag"),
  ("mcp-server","MCP Server",N.MODULE,"12 tools, stdio transport","infra"),
  ("qwen-analyzer","Qwen Analyzer",N.MODULE,"Qwen2.5-Coder-7B P4000","infra"),
  ("rag-vdb","RAG Vector DB",N.MODULE,"ml_rag+brain_rag vectors","infra"),
  # Trading/Risk
  ("scalper-strat","Scalper Strategy",N.METHOD,"Ultra-short TBM pipeline","trading"),
  ("position-sizing","Position Sizing",N.CONFIG,"Kelly/fixed/vol-adjusted","trading"),
  ("exec-algo","Execution Algorithm",N.METHOD,"Market/limit, slippage","trading"),
  ("risk-mgmt","Risk Management",N.MODULE,"Drawdown/loss limits","risk"),
  ("tail-risk","Tail Risk",N.CONCEPT,"Fat tails, VaR violations","risk"),
  ("regime-detect","Regime Detection",N.METHOD,"HMM/CLF regime changes","trading"),
  ("latency-opt","Latency Optimization",N.CONFIG,"Co-loc, pre-computed, zero-copy","infra"),
  ("mql5-integ","MQL5 Integration",N.MODULE,"MT5 signal/orders/ticks","infra"),
]

created=skipped=0
for cid,name,kind,summary,dom in DATA:
  if kg.get_concept(cid): skipped+=1; continue
  kg.create_concept(C(id=cid,name=name,kind=kind,summary=summary,domain=dom,importance=0.6))
  created+=1
print(f"Created: {created}, Skipped: {skipped}")

EDGES = [
  ("afml-ch2","dollar-bar",R.IMPLEMENTS),("afml-ch3","meta-labeling",R.IMPLEMENTS),
  ("afml-ch3","triple-barrier",R.IMPLEMENTS),("afml-ch4","sample-weights",R.IMPLEMENTS),
  ("afml-ch4","avg-uniqueness",R.REQUIRES),("afml-ch5","lgbm-classifier",R.REFERENCES),
  ("afml-ch7","purged-kfold",R.IMPLEMENTS),("afml-ch7","walk-forward-cv",R.REFERENCES),
  ("afml-ch9","feat-imp-mda",R.IMPLEMENTS),("afml-ch9","feat-imp-shap",R.IMPLEMENTS),
  ("frac-diff-theory","frac-diff",R.IMPLEMENTS),
  ("data-ingestion","bar-construction",R.DEPENDS_ON),("bar-construction","feature-engineering",R.PRODUCES),
  ("feature-engineering","feature-selection",R.PRODUCES),("feature-selection","label-generation",R.REQUIRES),
  ("label-generation","model-training",R.PRODUCES),("model-training","backtesting",R.PRODUCES),
  ("htf-trend-gate","scalper-strat",R.CONFIGURED_BY),("optuna-tuning","model-training",R.CONFIGURED_BY),
  ("feature-direction","feature-engineering",R.IMPLEMENTS),
  ("lgbm-classifier","n-estimators",R.CONFIGURED_BY),("lgbm-classifier","learning-rate",R.CONFIGURED_BY),
  ("lgbm-classifier","early-stopping",R.CONFIGURED_BY),
  ("meta-label-model","meta-labeling",R.IMPLEMENTS),
  ("purged-kfold","leakage",R.VALIDATED_BY),
  ("scoring-metric","backtesting",R.CONFIGURED_BY),
  ("yantrikdb-engine","cortexdb-grpc",R.REFERENCES),
  ("embedding-model","hybrid-rag",R.REQUIRES),("hybrid-rag","kg-db",R.REQUIRES),
  ("mcp-server","yantrikdb-engine",R.DEPENDS_ON),("mcp-server","cortexdb-grpc",R.DEPENDS_ON),
  ("mcp-server","qwen-analyzer",R.DEPENDS_ON),("mcp-server","rag-vdb",R.DEPENDS_ON),
  ("scalper-strat","triple-barrier",R.REQUIRES),("scalper-strat","meta-labeling",R.REQUIRES),
  ("scalper-strat","htf-trend-gate",R.CONFIGURED_BY),
  ("position-sizing","risk-mgmt",R.VALIDATED_BY),("exec-algo","latency-opt",R.DEPENDS_ON),
  ("regime-detect","scalper-strat",R.INFLUENCES),("tail-risk","risk-mgmt",R.INFLUENCES),
  ("mql5-integ","exec-algo",R.IMPLEMENTS),("mql5-integ","data-ingestion",R.PRODUCES),
  ("regime-detect","label-distribution",R.INFLUENCES,"Regime invalidates labels"),
  ("tail-risk","overfitting",R.INFLUENCES,"Tail events overfit normal"),
  ("early-stopping","overfitting",R.VALIDATED_BY),
]
linked=0
for e in EDGES:
  fid,tid,rel=e[0],e[1],e[2]; desc=e[3] if len(e)>3 else None
  if not kg.get_concept(fid) or not kg.get_concept(tid): continue
  try: kg.link(fid,tid,rel,description=desc); linked+=1
  except: pass
print(f"Linked: {linked} edges")

s=kg.get_stats(); cc=kg.detect_contradictions()
print(f"\nFinal: {s['concepts']} concepts, {s['edges']} edges, {s['domains']} domains")
print(f"Contradictions: {s['unresolved_contradictions']}")
for c in cc: print(f"  {c.concept_a} <-> {c.concept_b}: {c.reason}")
kg.close()
print("\n✅ KG EXPANDED!")
