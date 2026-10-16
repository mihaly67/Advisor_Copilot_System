"""
Knowledge Space Vectorizer — index LGBM_copilot/knowledge/ into ml_rag_v2.db
Uses sentence-transformers (all-MiniLM-L6-v2) on P4000
Only indexes new files, does not re-vectorize existing repos.

Usage:
  python3 knowledge_vectorize.py --dry-run    # Preview what would be indexed
  python3 knowledge_vectorize.py              # Index and vectorize
"""
import os
import sqlite3
import json
import numpy as np
from pathlib import Path
from datetime import datetime

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Paths
KS_PATH = Path("/data/LGBM_copilot/knowledge")
DB_PATH = Path("/data/ml/_vectorized/ml_rag_v2.db")
INDEX_PATH = Path("/data/ml/ml.index")

# Config
MODEL_NAME = 'all-MiniLM-L6-v2'
BATCH_SIZE = 64
CHUNK_SIZE = 800  # chars per chunk
CHUNK_OVERLAP = 100
REPO_NAME = "LGBM_copilot_knowledge"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def get_files_to_index() -> list:
    """Get all files in knowledge space."""
    files = []
    
    # JSON files (decision trees, checklists, anti_patterns, pipeline_chain)
    for subdir in ['decision_trees', 'checklists', 'anti_patterns', 'pipeline_chain']:
        for f in (KS_PATH / subdir).glob("*.json"):
            files.append(("json", f))
    
    # Python files (code templates)
    for f in (KS_PATH / "code_templates").glob("*.py"):
        files.append(("python", f))
    
    # Markdown files (reference digests)
    for f in (KS_PATH / "reference_digests").glob("*.md"):
        files.append(("markdown", f))
    
    # Index file
    idx = KS_PATH / "KNOWLEDGE_INDEX.md"
    if idx.exists():
        files.append(("markdown", idx))
    
    return files


def index_to_db(files: list, dry_run: bool = False) -> int:
    """Index files into ml_rag_v2.db."""
    if dry_run:
        print(f"DRY RUN: {len(files)} files to index")
        for ftype, fpath in files:
            print(f"  [{ftype}] {fpath.name} ({fpath.stat().st_size} bytes)")
        return len(files)
    
    # Connect to DB
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo TEXT, path TEXT, chunk_type TEXT, chunk_name TEXT,
            line_start INTEGER, line_end INTEGER,
            content TEXT, lang TEXT, created TEXT
        )
    ''')
    
    total_chunks = 0
    
    for ftype, fpath in files:
        try:
            content = fpath.read_text(errors='replace')
        except Exception as e:
            print(f"  SKIP {fpath.name}: {e}")
            continue
        
        # Chunk the content
        chunks = chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            cursor.execute('''
                INSERT INTO chunks (repo, path, chunk_type, chunk_name, line_start, line_end, content, lang, created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                REPO_NAME,
                str(fpath.relative_to(KS_PATH.parent)),
                ftype,
                fpath.stem + f"_chunk{i}",
                i * (CHUNK_SIZE - CHUNK_OVERLAP),
                (i + 1) * CHUNK_SIZE,
                chunk,
                ftype,
                datetime.now().isoformat(),
            ))
            total_chunks += 1
        
        print(f"  ✓ {fpath.name}: {len(chunks)} chunks")
    
    conn.commit()
    conn.close()
    
    print(f"\nTotal chunks indexed: {total_chunks}")
    return total_chunks


def build_faiss_index(dry_run: bool = False):
    """Build FAISS index from all chunks in DB (requires GPU)."""
    if dry_run:
        print("DRY RUN: Would build FAISS index")
        return
    
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: pip install faiss-cpu sentence-transformers")
        return
    
    print(f"Loading model {MODEL_NAME} on P4000...")
    model = SentenceTransformer(MODEL_NAME, device='cuda:0')
    
    # Load all chunks
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    rows = cursor.execute("SELECT id, content FROM chunks ORDER BY id").fetchall()
    conn.close()
    
    print(f"Encoding {len(rows)} chunks...")
    texts = [r[1] or "" for r in rows]
    ids = [r[0] for r in rows]
    
    # Batch encode
    embeddings = model.encode(texts, batch_size=BATCH_SIZE, 
                              normalize_embeddings=True, show_progress_bar=True)
    
    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product (cosine with normalized vectors)
    index.add(embeddings.astype('float32'))
    
    # Save
    faiss.write_index(index, str(INDEX_PATH))
    print(f"FAISS index saved: {INDEX_PATH} ({index.ntotal} vectors, dim={dim})")
    
    # Cleanup
    del model
    import torch
    torch.cuda.empty_cache()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--index-only", action="store_true", help="DB only, no FAISS")
    a = p.parse_args()
    
    files = get_files_to_index()
    print(f"Knowledge Space Vectorizer")
    print(f"Files to index: {len(files)}")
    
    count = index_to_db(files, dry_run=a.dry_run)
    
    if not a.index_only and not a.dry_run:
        build_faiss_index()
    
    print("\nDone!")
