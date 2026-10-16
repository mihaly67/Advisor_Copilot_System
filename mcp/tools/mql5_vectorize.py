#!/usr/bin/env python3
"""
mql5_vectorize.py — MQL5 RAG DB vektorizáció és szemantikus keresés.

Adatbázis: /data/MQL5/mql5_native_knowledge.db (rag_data tábla, 9780 sor)
Modell:    all-MiniLM-L6-v2 (384-dim, 22MB, GPU+CPU)
GPU:       P2000 (5GB) alapértelmezés

Használat:
    python3 mql5_vectorize.py --create        # embedding oszlop
    python3 mql5_vectorize.py --embed         # vektorizáció
    python3 mql5_vectorize.py --search "query"  # keresés
    python3 mql5_vectorize.py --info           # statisztika
"""
import os, sys, sqlite3, argparse
import numpy as np

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")  # P2000

DB_PATH = "/data/MQL5/mql5_native_knowledge.db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def embed_to_blob(vec):
    return vec.astype(np.float32).tobytes()

def blob_to_vec(blob):
    return np.frombuffer(blob, dtype=np.float32)

def cmd_create():
    conn = get_db()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(rag_data)").fetchall()]
    if "embedding" in cols:
        print("embedding oszlop mar letezik")
    else:
        conn.execute("ALTER TABLE rag_data ADD COLUMN embedding BLOB")
        conn.commit()
        print("embedding oszlop letrehozva")
    conn.close()


def cmd_embed():
    """sentence-transformers batch embedding GPU-n."""
    from sentence_transformers import SentenceTransformer
    device = "cuda"
    print(f"Modell: {MODEL_NAME}, device: {device}")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print(f"Modell betoltve ({model.get_sentence_embedding_dimension()}-dim)")

    conn = get_db()
    rows = conn.execute(
        "SELECT id, content FROM rag_data WHERE embedding IS NULL ORDER BY id"
    ).fetchall()
    total = len(rows)
    print(f"Vektorizalando: {total} sor")
    if total == 0:
        print("Minden sor vektorizalva!")
        conn.close()
        return

    done = 0
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        ids = [r[0] for r in batch]
        texts = [r[1][:8192] for r in batch]
        embeddings = model.encode(
            texts, batch_size=len(batch),
            show_progress_bar=False, convert_to_numpy=True,
            normalize_embeddings=True,
        )
        conn.executemany(
            "UPDATE rag_data SET embedding = ? WHERE id = ?",
            [(embed_to_blob(embeddings[j]), ids[j]) for j in range(len(batch))]
        )
        conn.commit()
        done += len(batch)
        if done % 256 == 0 or done == total:
            print(f"  [{done}/{total}] {100*done/total:.0f}%")
    conn.close()
    print(f"Kesz! {total} sor vektorizalva.")


def cmd_search(query, top_k=5):
    """Cosine similarity keresés."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME, device="cuda")
    q_vec = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]

    conn = get_db()
    rows = conn.execute(
        "SELECT id, filepath, content, embedding FROM rag_data WHERE embedding IS NOT NULL"
    ).fetchall()
    conn.close()
    if not rows:
        print("Nincs vektorizalt sor! Futtasd: --embed")
        return

    scores = []
    for row in rows:
        vec = blob_to_vec(row[3])
        score = float(np.dot(q_vec, vec))
        scores.append((score, row))
    scores.sort(key=lambda x: -x[0])

    print(f'\nKereses: "{query}"')
    print(f"{len(rows)} vektorizalt sor, top {top_k}:\n")
    for rank, (score, row) in enumerate(scores[:top_k], 1):
        print(f"  {rank}. [{score:.4f}] {row[1]}")
        print(f"     {row[2][:200].strip()}...")
        print()


def cmd_info():
    """DB statisztika."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM rag_data").fetchone()[0]
    embedded = conn.execute("SELECT COUNT(*) FROM rag_data WHERE embedding IS NOT NULL").fetchone()[0]
    sources = conn.execute(
        "SELECT SUBSTR(filepath,1,INSTR(filepath,'_Page')-1) as src, COUNT(*) "
        "FROM rag_data GROUP BY src ORDER BY COUNT(*) DESC"
    ).fetchall()
    total_mb = conn.execute("SELECT SUM(LENGTH(content))/1024.0/1024.0 FROM rag_data").fetchone()[0]
    conn.close()
    print(f"DB: {DB_PATH}")
    print(f"  Osszes sor:  {total}")
    print(f"  Vektorizalt: {embedded}/{total} ({100*embedded/total:.0f}%)")
    print(f"  Tartalom:   {total_mb:.1f} MB")
    print(f"  Forrasok:")
    for src, cnt in sources:
        print(f"    {src}: {cnt} sor")


def main():
    parser = argparse.ArgumentParser(description="MQL5 RAG vektorizacio")
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--embed", action="store_true")
    parser.add_argument("--search", type=str)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--info", action="store_true")
    args = parser.parse_args()

    if args.info:
        cmd_info()
    elif args.create:
        cmd_create()
    elif args.embed:
        cmd_embed()
    elif args.search:
        cmd_search(args.search, args.top_k)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()