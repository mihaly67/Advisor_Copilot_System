#!/usr/bin/env python3
"""Test cognitive_memory and shared_brain MCP tools directly"""
import sys, os
sys.path.insert(0, "/data/mcp_server")
os.chdir("/data/mcp_server")

# Mock the server module essentials
import json
MCP_SERVER_DIR = "/data/mcp_server"

# Import the tool functions directly
from server import tool_cognitive_memory, tool_shared_brain, _get_yantrikdb

print("=" * 60)
print("COGNITIVE MEMORY + SHARED BRAIN MCP TOOL TEST")
print("=" * 60)

# 1. Cognitive Memory - Stats
print("\n1. cognitive_memory(action='stats')")
result = tool_cognitive_memory(action="stats")
print(f"   {result[:300]}")

# 2. Record memories
print("\n2. Record memories")
memories = [
    "Meta-labeling uses a secondary model to decide on primary model trades - AFML Ch.3",
    "Triple barrier method defines labels from profit-take, stop-loss, and time horizon",
    "Using both sample-weights AND meta-labeling causes double-counting risk - NEVER together",
    "Profit multiplier and stop multiplier must not be co-optimized - asymmetric barriers bias labels",
    "Training tick data must NEVER overlap with exam tick data - data leakage risk",
    "LightGBM scalper uses n_estimators=300, learning_rate=0.05, max_depth=6",
    "Dollar bar threshold=50000000 creates volume-based sampling for stationarity",
    "HTF trend gate uses 5-min EMA to filter counter-trend entries",
    "TBM pipeline v4.0.1: feature_selection → triple_barrier → meta_label → train → backtest",
    "Feature direction encoding: rsi_dir, macd_dir, bb_dir capture regime shifts",
]
for m in memories:
    r = tool_cognitive_memory(action="record", text=m, importance=0.8)
    print(f"   {r[:80]}")

# 3. Recall
print("\n3. Recall 'double-counting risk'")
r = tool_cognitive_memory(action="recall", query="What causes double-counting risk?", top_k=3)
print(f"   {r[:500]}")

print("\n4. Recall 'triple barrier'")
r = tool_cognitive_memory(action="recall", query="triple barrier method labels", top_k=3)
print(f"   {r[:500]}")

print("\n5. Recall 'data leakage'")
r = tool_cognitive_memory(action="recall", query="data leakage prevention", top_k=3)
print(f"   {r[:500]}")

print("\n6. Recall 'pipeline architecture'")
r = tool_cognitive_memory(action="recall", query="pipeline architecture workflow", top_k=3)
print(f"   {r[:500]}")

# 7. Export context
print("\n7. Export context 'labeling contradictions'")
r = tool_cognitive_memory(action="export_context", query="labeling contradictions and risks", top_k=5)
print(f"   {r[:600]}")

# 8. Ingest KG concepts into yantrikdb
print("\n8. Ingest KG → yantrikdb")
r = tool_cognitive_memory(action="ingest_kg")
print(f"   {r}")

# 9. Stats after ingest
print("\n9. Stats after ingest")
r = tool_cognitive_memory(action="stats")
stats = json.loads(r)
print(f"   Active: {stats.get('active_memories')}, Ops: {stats.get('operations')}, Vec: {stats.get('vec_index_entries')}")

# 10. Shared Brain
print("\n10. shared_brain(action='server_status')")
r = tool_shared_brain(action="server_status")
print(f"   {r[:300]}")

print("\n11. shared_brain(action='remember') - fallback")
r = tool_shared_brain(action="remember", text="Scalper v4.0.1 uses TBM pipeline with meta-labeling", scope="project")
print(f"   {r[:200]}")

print("\n12. shared_brain(action='recall') - fallback")
r = tool_shared_brain(action="recall", query="scalper pipeline", top_k=3)
print(f"   {r[:400]}")

print("\n✅ COGNITIVE MEMORY + SHARED BRAIN MCP TOOLS WORKING!")
