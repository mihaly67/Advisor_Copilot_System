#!/usr/bin/env python3
import sys, json
sys.path.insert(0, "/data/mcp_server/tools")
from kg_hybrid_layers import EmbeddingSearch, HybridRAGRetriever, yantrikdbBridge, RDFExporter
from knowledge_graph_tools import KnowledgeGraphDB

db = "/data/mcp_server/data/knowledge_graph.db"
kg = KnowledgeGraphDB(db)

print("1. Embedding Re-index")
es = EmbeddingSearch(db, lazy=False)
print(f"   {json.dumps(es.index_all(force=True))}")

print("\n2. Embedding Search")
queries = ["triple barrier labeling", "cognitive memory RAG", "regime detection",
           "pipeline architecture", "risk tail", "yantrikdb cortexdb",
           "overfitting prevention", "meta-labeling contradiction"]
for q in queries:
    r = es.search(q, top_k=3)
    if r:
        print(f"   {q}: {r[0]['score']:.3f} -> {r[0]['name']}")
    else:
        print(f"   {q}: none")

print("\n3. HybridRAG")
hrag = HybridRAGRetriever(kg, es, alpha=0.6)
for q in ["meta-labeling contradiction", "regime pipeline", "RAG architecture"]:
    hr = hrag.retrieve(q, top_k=3)
    vr = len(hr["vector_results"])
    gr = len(hr["graph_expansion"])
    cr = len(hr["contradictions"])
    print(f"   {q}: V={vr} G={gr} C={cr}")

print("\n4. yantrikdb Bridge")
yt = yantrikdbBridge(kg)
print(f"   Engine: {yt.engine_type}")
cp = yt.propagate_conflicts("meta-labeling", depth=2)
print(f"   Propagate: visited={cp['visited']} conflicts={len(cp['conflicts'])}")

print("\n5. RDF")
exp = RDFExporter(kg).export_to_rdf()
print(f"   Triples: {exp['triples']}, Concepts: {exp['concepts']}, Edges: {exp['edges']}")

es.close()
kg.close()
print("\n✅ RE-INDEX COMPLETE!")
