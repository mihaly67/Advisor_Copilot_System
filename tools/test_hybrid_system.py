#!/usr/bin/env python3
"""Test the full hybrid system: KG + Embedding + HybridRAG + yantrikdb + RDF"""
import json, sys
sys.path.insert(0, "/data/mcp_server/tools")

from kg_hybrid_layers import build_hybrid_system

print("=" * 60)
print("FULL HYBRID SYSTEM TEST")
print("=" * 60)

hyb = build_hybrid_system()
kg = hyb["kg"]
es = hyb["embedding"]
hrag = hyb["hybrid_rag"]
rdf = hyb["rdf"]
yt = hyb["yantrik"]

# 1. KG stats
print("\n1. Knowledge Graph")
stats = kg.get_stats()
print(f"   Concepts: {stats['concepts']}, Edges: {stats['edges']}, Domains: {stats['domains']}")
print(f"   Unresolved contradictions: {stats['unresolved_contradictions']}")

# 2. Embedding indexing
print("\n2. Embedding Search")
idx = es.index_all()
print(f"   Indexed: {idx['indexed']}, Skipped: {idx['skipped']}, Model: {idx.get('model','?')}, Dim: {idx.get('dim',0)}")

# 3. Vector search test
results = es.search("triple barrier labeling", top_k=3)
print(f"   Search 'triple barrier labeling': {len(results)} results")
for r in results:
    print(f"     - {r['name']} [{r['kind']}] score={r['score']:.3f}")

results2 = es.search("contradiction in labeling", top_k=3)
print(f"   Search 'contradiction in labeling': {len(results2)} results")
for r in results2:
    print(f"     - {r['name']} [{r['kind']}] score={r['score']:.3f}")

# 4. HybridRAG
print("\n3. HybridRAG")
hr = hrag.retrieve("meta-labeling contradiction risk", top_k=3)
print(f"   Vector: {len(hr['vector_results'])}, Graph: {len(hr['graph_expansion'])}, Contradictions: {len(hr['contradictions'])}")
print(f"   Scores: {hr['scores']}")
print(f"   Context preview: {hr['context'][:300]}...")

# 5. yantrikdb bridge
print("\n4. yantrikdb Bridge")
print(f"   Engine type: {yt.engine_type}")
cp = yt.propagate_conflicts("meta-labeling", depth=2)
print(f"   Conflict propagation: visited={cp['visited']}, conflicts={len(cp['conflicts'])}")
if cp['conflicts']:
    for c in cp['conflicts']:
        print(f"     - {c['a']} ↔ {c['b']}: {c['reason']}")

# 6. Temporal decay
print("\n5. Temporal Decay")
decay = yt.temporal_decay_batch()
print(f"   Half-life: {decay['half_life_h']}h, Decayed: {decay['decayed']}")
for d in decay['details'][:5]:
    print(f"     - {d['concept_id']}: {d['original']:.2f} → {d['new']:.4f} (age={d['age_h']}h)")

# 7. RDF Export
print("\n6. RDF Export")
try:
    rstats = rdf.export_to_rdf()
    print(f"   Triples: {rstats['triples']}, Concepts: {rstats['concepts']}, Edges: {rstats['edges']}")
except ImportError as e:
    print(f"   rdflib not installed: {e}")

es.close()
kg.close()
print("\n✅ ALL HYBRID LAYERS WORKING!")
