"""
FAISS Semantic Search Bridge for RAG
Connects the existing ml.index + brain_rag.index to knowledge space
Uses sentence-transformers (all-MiniLM-L6-v2) on P4000

Based on: /data/RAG_epito_ismeretek/advanced_rag_search.py
"""
import os
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

# Paths
ML_DB = Path("/data/ml/_vectorized/ml_rag_v2.db")
ML_INDEX = Path("/data/ml/ml.index")
BRAIN_DB = Path("/data/Brain/_vectorized/brain_rag.db")

# Config
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
EMBEDDING_GPU = 0  # P4000
TOP_K = 10
DISTANCE_THRESHOLD = 1.25


def search(query_text: str, top_k: int = TOP_K, 
           db: str = 'ml', use_gpu: bool = True) -> List[Dict]:
    """
    FAISS semantic search in ML or Brain RAG database.
    
    Args:
        query_text: Natural language query
        top_k: Number of results
        db: 'ml' or 'brain'
        use_gpu: Use P4000 for embedding (faster)
        
    Returns:
        List of dicts with repo, path, name, content preview, distance
    """
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return [{"error": "pip install faiss-cpu sentence-transformers"}]
    
    # Select DB and index
    db_path = ML_DB if db == 'ml' else BRAIN_DB
    # Brain index may not exist yet
    index_path = ML_INDEX if db == 'ml' else Path("/data/Brain/_vectorized/brain_rag.index")
    
    if not index_path.exists():
        return [{"error": f"FAISS index not found: {index_path}. Run vectorization first."}]
    
    # Load model and encode
    device = f'cuda:{EMBEDDING_GPU}' if use_gpu else 'cpu'
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    query_vec = model.encode([query_text], normalize_embeddings=True)
    
    # Load FAISS index
    index = faiss.read_index(str(index_path))
    
    # Search
    distances, ids = index.search(query_vec.astype('float32'), top_k)
    
    # Fetch from DB
    results = []
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        for rank, (dist, doc_id) in enumerate(zip(distances[0], ids[0]), 1):
            if doc_id < 0 or dist > DISTANCE_THRESHOLD:
                continue
            try:
                row = conn.execute(
                    "SELECT repo,path,chunk_name,line_start,line_end,content FROM chunks WHERE id=?",
                    (int(doc_id),)
                ).fetchone()
                if row:
                    results.append({
                        "rank": rank,
                        "distance": round(float(dist), 4),
                        "repo": row["repo"],
                        "path": row["path"],
                        "name": row["chunk_name"],
                        "lines": f"{row['line_start']}-{row['line_end']}",
                        "preview": (row["content"] or "")[:200],
                    })
            except Exception as e:
                results.append({"error": str(e)})
        conn.close()
    
    # Cleanup GPU
    del model
    if use_gpu:
        import torch
        torch.cuda.empty_cache()
    
    return results


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "triple barrier method"
    results = search(query, db='ml')
    for r in results:
        if "error" in r:
            print(f"ERROR: {r['error']}")
            continue
        print(f"#{r['rank']} (d={r['distance']:.3f}) {r['repo']}/{r['path']}::{r['name']}")
        print(f"  {r['preview'][:100]}...")
