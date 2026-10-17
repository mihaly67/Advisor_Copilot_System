#!/usr/bin/env python3
"""Test yantrikdb full engine with bundled embedder"""
from yantrikdb import YantrikDB
import os, shutil

path = "/tmp/test_yantrik_full2"
if os.path.exists(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

# Use bundled embedder (potion-base-2M, runs in Rust, no Python deps)
db = YantrikDB(path, embedder="potion-base-2M")

# Record memories
rid1 = db.record_text("Meta-labeling uses a secondary model to decide whether to take the primary model trade")
rid2 = db.record_text("Triple barrier method defines labels based on profit-take, stop-loss, and time horizon")
rid3 = db.record_text("Using both sample-weights AND meta-labeling together causes double-counting risk")
rid4 = db.record_text("Profit multiplier and stop multiplier must not be optimized together - asymmetric barriers cause label bias")

print(f"Recorded 4 memories")

# Recall
rec = db.recall_text("What causes double-counting risk in labeling?")
print(f"\nRecall 'double-counting':")
print(f"  {str(rec)[:500]}")

rec2 = db.recall_text("triple barrier profit stop")
print(f"\nRecall 'triple barrier':")
print(f"  {str(rec2)[:300]}")

# Full API
full_dir = [x for x in dir(db) if not x.startswith("_")]
print(f"\nTotal API methods: {len(full_dir)}")
memory_ops = [x for x in full_dir if "record" in x or "recall" in x or "remember" in x]
conflict_ops = [x for x in full_dir if "conflict" in x or "contradict" in x]
decay_ops = [x for x in full_dir if "decay" in x or "consolid" in x]
graph_ops = [x for x in full_dir if "graph" in x or "edge" in x or "node" in x]
claim_ops = [x for x in full_dir if "claim" in x or "correct" in x]
print(f"  Memory: {memory_ops}")
print(f"  Conflict: {conflict_ops}")
print(f"  Decay: {decay_ops}")
print(f"  Graph: {graph_ops}")
print(f"  Claim: {claim_ops}")

# Stats
try:
    stats = db.stats()
    print(f"\nStats: {stats}")
except Exception as e:
    print(f"\nStats: {e}")

db.close()
print("\n✅ yantrikdb full engine with potion-base-2M working!")

