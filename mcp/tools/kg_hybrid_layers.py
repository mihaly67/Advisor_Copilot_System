#!/usr/bin/env python3
"""
Embedding + HybridRAG + RDF layers for Knowledge Graph

1. EmbeddingSearch   - all-MiniLM-L6-v2 cosine similarity search
2. HybridRAGRetriever - vector + graph hybrid retrieval
3. RDFExporter       - rdflib SPARQL/RDF export for multi-agent memory
4. yantrikdbBridge   - Python bridge to Rust contradiction engine (stub + fallback)
"""
import sqlite3, json, time, math, os, struct
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict


class EmbeddingSearch:
    """Embedding-based semantic search over KG concepts. all-MiniLM-L6-v2 (384-dim)."""

    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBED_DIM = 384

    def __init__(self, db_path: str, model_name: str = None, lazy: bool = True):
        self.db_path = db_path
        self.model_name = model_name or self.MODEL_NAME
        self._model = None
        self._conn = None
        if not lazy:
            self._ensure_model()

    def _ensure_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device="cpu")
        except ImportError:
            raise ImportError("sentence-transformers not installed. pip install sentence-transformers")

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    concept_id TEXT PRIMARY KEY, embedding BLOB NOT NULL,
                    model_name TEXT NOT NULL, updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_emb_model ON embeddings(model_name);
            """)
            self._conn.commit()
        return self._conn

    def _encode(self, texts: List[str]) -> List[List[float]]:
        self._ensure_model()
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    @staticmethod
    def _blob_to_vec(blob: bytes) -> List[float]:
        n = len(blob) // 4
        return list(struct.unpack(f'{n}f', blob))

    @staticmethod
    def _vec_to_blob(vec: List[float]) -> bytes:
        return struct.pack(f'{len(vec)}f', *vec)

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def index_all(self, force: bool = False) -> Dict:
        conn = self._get_conn()
        rows = conn.execute("SELECT id, name, summary, why FROM concepts WHERE removed_at IS NULL").fetchall()
        if not rows:
            return {"indexed": 0, "skipped": 0, "errors": 0}
        if not force:
            existing = set(r[0] for r in conn.execute(
                "SELECT concept_id FROM embeddings WHERE model_name=?", (self.model_name,)).fetchall())
            to_index = [r for r in rows if r[0] not in existing]
        else:
            to_index = list(rows)
        if not to_index:
            return {"indexed": 0, "skipped": len(rows), "errors": 0}
        texts = [" | ".join([r[1] or "", r[2] or ""] + ([r[3]] if r[3] else [])) for r in to_index]
        try:
            vectors = self._encode(texts)
        except Exception as e:
            return {"indexed": 0, "skipped": 0, "errors": len(to_index), "error": str(e)}
        now = time.time()
        for row, vec in zip(to_index, vectors):
            conn.execute("INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?)",
                         (row[0], self._vec_to_blob(vec), self.model_name, now))
        conn.commit()
        return {"indexed": len(to_index), "skipped": len(rows) - len(to_index),
                "errors": 0, "model": self.model_name, "dim": len(vectors[0]) if vectors else 0}

    def search(self, query: str, top_k: int = 10, min_score: float = 0.3) -> List[Dict]:
        conn = self._get_conn()
        query_vec = self._encode([query])[0]
        rows = conn.execute(
            """SELECT e.concept_id, e.embedding, c.name, c.kind, c.summary, c.importance
               FROM embeddings e JOIN concepts c ON e.concept_id=c.id AND c.removed_at IS NULL
               WHERE e.model_name=?""", (self.model_name,)).fetchall()
        results = []
        for r in rows:
            score = self._cosine_sim(query_vec, self._blob_to_vec(r[1]))
            if score >= min_score:
                results.append({"concept_id": r[0], "score": round(score, 4),
                                "name": r[2], "kind": r[3], "summary": r[4], "importance": r[5]})
        results.sort(key=lambda x: (x["score"], x.get("importance", 0)), reverse=True)
        return results[:top_k]

    def get_stats(self) -> Dict:
        conn = self._get_conn()
        try:
            count = conn.execute("SELECT COUNT(*) FROM embeddings WHERE model_name=?", (self.model_name,)).fetchone()[0]
        except Exception:
            count = 0
        return {"model": self.model_name, "indexed_concepts": count, "dim": self.EMBED_DIM}

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


class HybridRAGRetriever:
    """Hybrid retrieval: vector similarity + graph traversal + contradiction detection."""

    def __init__(self, kg, embedding_search: EmbeddingSearch,
                 alpha: float = 0.6, graph_hops: int = 2, max_chars: int = 4000):
        self.kg = kg
        self.es = embedding_search
        self.alpha = alpha
        self.graph_hops = graph_hops
        self.max_chars = max_chars

    def retrieve(self, query: str, top_k: int = 5) -> Dict:
        vector_results = self.es.search(query, top_k=top_k * 2, min_score=0.25)
        graph_concepts = set()
        graph_expansion = []
        for vr in vector_results[:top_k]:
            cid = vr["concept_id"]
            graph_concepts.add(cid)
            for n in self._graph_expand(cid, self.graph_hops):
                if n["concept_id"] not in graph_concepts:
                    graph_concepts.add(n["concept_id"])
                    graph_expansion.append(n)
        all_c = self.kg.detect_contradictions()
        rel_c = [{"a": c.concept_a, "b": c.concept_b, "relation": c.relation,
                  "reason": c.reason, "severity": c.severity}
                 for c in all_c if c.concept_a in graph_concepts or c.concept_b in graph_concepts]
        scores = {}
        for vr in vector_results:
            gs = self._graph_centrality(vr["concept_id"])
            scores[vr["concept_id"]] = round(self.alpha * vr["score"] + (1 - self.alpha) * gs, 4)
        ctx = self._build_context(query, vector_results[:top_k], graph_expansion, rel_c)
        return {"query": query, "vector_results": vector_results[:top_k],
                "graph_expansion": graph_expansion[:top_k * 3],
                "contradictions": rel_c, "context": ctx, "scores": scores}

    def _graph_expand(self, cid: str, max_hops: int) -> List[Dict]:
        visited = {cid}; frontier = [cid]; result = []
        for _ in range(max_hops):
            nf = []
            for c in frontier:
                if c in visited and c != cid: continue
                visited.add(c)
                for r in self.kg.conn.execute("SELECT to_id, relation FROM edges WHERE from_id=?", (c,)).fetchall():
                    if r[0] not in visited:
                        visited.add(r[0]); nf.append(r[0])
                        co = self.kg.get_concept(r[0])
                        if co: result.append({"concept_id": r[0], "relation_from": c, "relation": r[1],
                                              "name": co["name"], "kind": co["kind"], "summary": co["summary"]})
                for r in self.kg.conn.execute("SELECT from_id, relation FROM edges WHERE to_id=?", (c,)).fetchall():
                    if r[0] not in visited:
                        visited.add(r[0]); nf.append(r[0])
                        co = self.kg.get_concept(r[0])
                        if co: result.append({"concept_id": r[0], "relation_to": c, "relation": r[1],
                                              "name": co["name"], "kind": co["kind"], "summary": co["summary"]})
            frontier = nf
        return result

    def _graph_centrality(self, cid: str) -> float:
        od = self.kg.conn.execute("SELECT COUNT(*) FROM edges WHERE from_id=?", (cid,)).fetchone()[0]
        id_ = self.kg.conn.execute("SELECT COUNT(*) FROM edges WHERE to_id=?", (cid,)).fetchone()[0]
        return min((od + id_) / 10.0, 1.0)

    def _build_context(self, query, vr, ge, co) -> str:
        lines = [f"## Query: {query}\n"]
        if vr:
            lines.append("### Relevant Concepts (semantic)")
            for v in vr:
                lines.append(f"- **{v['name']}** [{v['kind']}] (sim={v.get('score',0):.2f}): {v['summary']}")
        if ge:
            lines.append("\n### Graph Context")
            for g in ge[:15]:
                lines.append(f"- {g['name']} --{g.get('relation','')}--> expanded")
        if co:
            lines.append("\n### ⚠️ Contradictions")
            for c in co:
                lines.append(f"- **{c['a']} ↔ {c['b']}**: {c['reason']} (sev={c['severity']})")
        ctx = "\n".join(lines)
        return ctx[:self.max_chars] + ("\n...[truncated]" if len(ctx) > self.max_chars else "")



class RDFExporter:
    """Export KG to RDF for SPARQL queries and multi-agent sharing."""

    NS_SCALPER = "http://lgbm-copilot.org/scalper/"
    NS_REL = "http://lgbm-copilot.org/relation/"

    def __init__(self, kg):
        self.kg = kg; self._graph = None; self._rl = None

    def _get_graph(self):
        if self._graph is not None: return self._graph, self._rl
        from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
        self._rl = type('RL', (), {'Graph': Graph, 'Namespace': Namespace, 'RDF': RDF,
                                    'RDFS': RDFS, 'Literal': Literal, 'URIRef': URIRef})()
        self._graph = Graph()
        return self._graph, self._rl

    def export_to_rdf(self) -> Dict:
        g, rl = self._get_graph()
        g.remove((None, None, None))
        NS = rl.Namespace(self.NS_SCALPER); REL = rl.Namespace(self.NS_REL)
        rows = self.kg.conn.execute(
            "SELECT id, name, kind, summary, importance, domain FROM concepts WHERE removed_at IS NULL").fetchall()
        for r in rows:
            s = NS[r[0]]
            g.add((s, rl.RDF.type, NS[r[2]])); g.add((s, rl.RDFS.label, rl.Literal(r[1])))
            g.add((s, rl.RDFS.comment, rl.Literal(r[3])))
            if r[4]: g.add((s, NS.importance, rl.Literal(r[4])))
            if r[5]: g.add((s, NS.domain, rl.Literal(r[5])))
        edges = self.kg.conn.execute("SELECT from_id, to_id, relation, description FROM edges").fetchall()
        for e in edges:
            g.add((NS[e[0]], REL[e[2]], NS[e[1]]))
            if e[3]: g.add((NS[e[0]], REL[f"{e[2]}_desc"], rl.Literal(e[3])))
        return {"triples": len(g), "concepts": len(rows), "edges": len(edges)}

    def sparql_query(self, query: str) -> List[Dict]:
        g, rl = self._get_graph()
        try: return [dict(row.asdict()) for row in g.query(query)]
        except Exception as e: return [{"error": str(e)}]

    def serialize(self, format: str = "turtle") -> str:
        g, rl = self._get_graph()
        return g.serialize(format=format)

    def get_stats(self) -> Dict:
        g, rl = self._get_graph()
        return {"triples": len(g), "namespaces": [str(ns) for ns, _ in list(g.namespaces())[:5]]}



class yantrikdbBridge:
    """Bridge to yantrikdb Rust-based contradiction engine. Falls back to Python."""

    def __init__(self, kg, half_life_hours: float = 168.0):
        self.kg = kg; self.half_life_hours = half_life_hours; self._rust = None
        try:
            import yantrikdb_py
            self._rust = yantrikdb_py.ContradictionChecker()
        except ImportError: pass

    @property
    def engine_type(self) -> str:
        return "rust" if self._rust else "python_fallback"

    def detect_contradictions_fast(self, concept_ids: List[str] = None) -> List[Dict]:
        if self._rust:
            try:
                # Push concepts + their edge relations to Rust checker
                cids = concept_ids or [r[0] for r in self.kg.conn.execute(
                    "SELECT id FROM concepts WHERE removed_at IS NULL").fetchall()]
                for cid in cids:
                    c = self.kg.get_concept(cid)
                    if not c: continue
                    # Build enriched summary with edge relations
                    parts = [c["summary"]]
                    for e in self.kg.conn.execute(
                        "SELECT relation, to_id, description FROM edges WHERE from_id=?", (cid,)).fetchall():
                        parts.append(f"{e[0]} {e[1]}")
                        if e[2]: parts.append(e[2])
                    for e in self.kg.conn.execute(
                        "SELECT relation, from_id, description FROM edges WHERE to_id=?", (cid,)).fetchall():
                        parts.append(f"{e[0]} {e[1]}")
                        if e[2]: parts.append(e[2])
                    self._rust.add(cid, " | ".join(parts))
                return [{"a": x[0], "b": x[1], "reason": x[2], "severity": 0.7,
                         "relation": "rust_detected"} for x in self._rust.check()]
            except Exception: pass
        all_c = self.kg.detect_contradictions()
        if concept_ids:
            cs = set(concept_ids); all_c = [c for c in all_c if c.concept_a in cs or c.concept_b in cs]
        return [{"a": c.concept_a, "b": c.concept_b, "relation": c.relation,
                 "reason": c.reason, "severity": c.severity} for c in all_c]

    def propagate_conflicts(self, source_id: str, depth: int = 3) -> Dict:
        visited = set(); conflicts = []; frontier = [source_id]
        for _ in range(depth):
            nf = []
            for cid in frontier:
                if cid in visited: continue
                visited.add(cid)
                direct = self.detect_contradictions_fast([cid])
                seen = {tuple(sorted([c["a"], c["b"]])) for c in conflicts}
                for d in direct:
                    if tuple(sorted([d["a"], d["b"]])) not in seen: conflicts.append(d)
                for d in self.kg.conn.execute(
                    "SELECT to_id FROM edges WHERE from_id=? AND relation IN ('depends_on','influences','requires')",
                    (cid,)).fetchall():
                    if d[0] not in visited: nf.append(d[0])
            frontier = nf
        return {"source": source_id, "depth": depth, "visited": len(visited),
                "conflicts": conflicts, "engine": self.engine_type}

    def temporal_decay_batch(self, concept_ids: List[str] = None, ref_time: float = None) -> Dict:
        if ref_time is None: ref_time = time.time()
        hls = self.half_life_hours * 3600
        rows = self.kg.conn.execute(
            "SELECT id, importance, updated_at FROM concepts WHERE removed_at IS NULL").fetchall()
        if concept_ids:
            cs = set(concept_ids); rows = [r for r in rows if r[0] in cs]
        decayed = []
        for r in rows:
            age = ref_time - r[2]; df = 0.5 ** (age / hls)
            decayed.append({"concept_id": r[0], "original": r[1], "decay": round(df, 4),
                            "new": round(r[1] * df, 4), "age_h": round(age / 3600, 1)})
        return {"half_life_h": self.half_life_hours, "decayed": len(decayed), "details": decayed}



def build_hybrid_system(db_path="/data/mcp_server/data/knowledge_graph.db", model_name="all-MiniLM-L6-v2"):
    """Build complete hybrid system: KG + Embedding + HybridRAG + RDF + yantrikdb."""
    from knowledge_graph_tools import KnowledgeGraphDB, build_scalper_knowledge_graph
    kg = KnowledgeGraphDB(db_path)
    es = EmbeddingSearch(db_path, model_name=model_name)
    hrag = HybridRAGRetriever(kg, es)
    rdf = RDFExporter(kg)
    yantrik = yantrikdbBridge(kg)
    stats = kg.get_stats()
    if stats["concepts"] == 0: build_scalper_knowledge_graph(kg)
    return {"kg": kg, "embedding": es, "hybrid_rag": hrag, "rdf": rdf, "yantrik": yantrik, "stats": stats}


if __name__ == "__main__":
    print("=" * 60)
    print("EMBEDDING + HYBRIDRAG + RDF + yantrikdb LAYERS")
    print("=" * 60)
    db_path = "/data/mcp_server/data/knowledge_graph.db"
    from knowledge_graph_tools import KnowledgeGraphDB
    kg = KnowledgeGraphDB(db_path)
    print("\n1. Embedding Search")
    es = EmbeddingSearch(db_path)
    print(f"   Index: {es.index_all()}")
    for r in es.search("triple barrier labeling", top_k=3):
        print(f"   - {r['name']} (score={r['score']:.3f})")
    print("\n2. HybridRAG")
    hrag = HybridRAGRetriever(kg, es)
    hr = hrag.retrieve("meta-labeling double counting", top_k=3)
    print(f"   V:{len(hr['vector_results'])} G:{len(hr['graph_expansion'])} C:{len(hr['contradictions'])}")
    print("\n3. RDF Export")
    rdf = RDFExporter(kg)
    print(f"   {rdf.export_to_rdf()}")
    print("\n4. yantrikdb Bridge")
    yt = yantrikdbBridge(kg)
    p = yt.propagate_conflicts("meta-labeling", depth=2)
    print(f"   Engine={yt.engine_type} visited={p['visited']} conflicts={len(p['conflicts'])}")
    kg.close(); es.close()
    print("\n✅ All layers working!")

