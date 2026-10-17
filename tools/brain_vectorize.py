#!/usr/bin/env python3
"""
brain_vectorize.py — Brain repo vektorizáció + szemantikus/logikai keresés.

3 réteg: CHUNK (jsonl+sqlite) → EMBEDDING (vektor) → GRAPH (logikai kapcsolatok)

Használat:
    python3 brain_vectorize.py --all          # Minden: chunk+embed+graph
    python3 brain_vectorize.py --chunk         # Csak chunking
    python3 brain_vectorize.py --embed         # Csak embedding
    python3 brain_vectorize.py --graph         # Csak graph építés
    python3 brain_vectorize.py --search "q"    # Szemantikus keresés
    python3 brain_vectorize.py --search "q" --repo "Light*" --depth 1 --breadth
    python3 brain_vectorize.py --info          # Statisztika
"""
import os, sys, re, ast, json, sqlite3, argparse, time, glob
import numpy as np
from datetime import datetime
from collections import defaultdict

BRAIN_DIR = "/data/Brain"
OUT_DIR = "/data/Brain/_vectorized"
DB_PATH = os.path.join(OUT_DIR, "brain_rag.db")
JSONL_PATH = os.path.join(OUT_DIR, "chunks.jsonl")
LOG_PATH = os.path.join(OUT_DIR, "vectorize_log.txt")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 128
MAX_CHUNK_CHARS = 8000
MIN_CHUNK_CHARS = 100
CHUNK_OVERLAP = 200

# Kizárandó kiterjesztések
EXCLUDE_EXTS = {
    '.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico', '.webp', '.bmp',
    '.csv', '.parquet', '.arrow', '.feather', '.tsv',
    '.bin', '.onnx', '.gguf', '.so', '.o', '.wasm', '.map', '.lock',
    '.zip', '.tar', '.gz', '.whl', '.egg', '.7z', '.rar',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flv',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.pyc', '.pyo', '.class', '.jar',
}
# Kizárandó könyvtárak
EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv', '.env',
    'dist', 'build', '.next', 'target', '.cache', '.pytest_cache',
    '.mypy_cache', '.tox', '.eggs', 'site-packages',
    'vendor', '.idea', '.vscode', 'coverage', '.nyc_output',
    '__snapshots__', '__tests__', 'fixtures', 'mocks',
}

# Feldolgozandó kiterjesztések → nyelv mapping
EXT_LANG = {
    '.py': 'python', '.js': 'javascript', '.mjs': 'javascript',
    '.ts': 'typescript', '.jsx': 'javascript', '.tsx': 'typescript',
    '.rs': 'rust', '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
    '.h': 'cpp', '.hpp': 'cpp', '.hxx': 'cpp',
    '.go': 'go', '.rb': 'ruby', '.java': 'java', '.kt': 'kotlin',
    '.swift': 'swift', '.cs': 'csharp', '.scala': 'scala',
    '.sh': 'shell', '.bash': 'shell',
    '.md': 'markdown', '.rst': 'markdown',
    '.yaml': 'config', '.yml': 'config', '.toml': 'config',
    '.json': 'config', '.ini': 'config', '.cfg': 'config',
    '.sql': 'sql', '.graphql': 'graphql', '.proto': 'proto',
}

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo TEXT, path TEXT, ext TEXT, lang TEXT,
            chunk_type TEXT, chunk_name TEXT,
            line_start INTEGER, line_end INTEGER,
            content TEXT, dependencies TEXT, exports TEXT,
            embedding BLOB,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_chunk INTEGER, to_chunk INTEGER,
            edge_type TEXT,
            FOREIGN KEY(from_chunk) REFERENCES chunks(id),
            FOREIGN KEY(to_chunk) REFERENCES chunks(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_repo ON chunks(repo);
        CREATE INDEX IF NOT EXISTS idx_chunks_lang ON chunks(lang);
        CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type);
        CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
        CREATE INDEX IF NOT EXISTS idx_chunks_name ON chunks(chunk_name);
        CREATE INDEX IF NOT EXISTS idx_chunks_embed ON chunks(embedding) WHERE embedding IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_graph_from ON graph_edges(from_chunk);
        CREATE INDEX IF NOT EXISTS idx_graph_to ON graph_edges(to_chunk);
    """)
    conn.commit()
    conn.close()


# ============================================================================
# FÁJLGYŰJTÉS
# ============================================================================
def collect_files():
    """Visszaadja az összes feldolgozandó fájlt."""
    files = []
    skipped = 0
    for root, dirs, fnames in os.walk(BRAIN_DIR):
        # Kizárás: .git, node_modules, etc.
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        # Kizárás: _vectorized maga
        if '_vectorized' in root:
            continue
        for fname in fnames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in EXCLUDE_EXTS:
                skipped += 1
                continue
            if ext not in EXT_LANG:
                skipped += 1
                continue
            fpath = os.path.join(root, fname)
            # Relatív út a Brain-en belül
            rel_path = os.path.relpath(fpath, BRAIN_DIR)
            # Repo = első könyvtárkomponens
            parts = rel_path.split(os.sep)
            repo = parts[0] if len(parts) > 1 else ""
            # _vectorized kizárás
            if repo == '_vectorized':
                continue
            # .git maradék kizárás
            if '.git' in parts:
                skipped += 1
                continue
            try:
                fsize = os.path.getsize(fpath)
            except:
                skipped += 1
                continue
            if fsize < 50:  # Üres/triviális
                skipped += 1
                continue
            if fsize > 500000:  # 500KB felett kihagy
                skipped += 1
                continue
            files.append({
                'fpath': fpath,
                'rel_path': rel_path,
                'repo': repo,
                'ext': ext,
                'lang': EXT_LANG[ext],
                'size': fsize,
            })
    return files, skipped


# ============================================================================
# CHUNKING — nyelvenként
# ============================================================================
def chunk_python(source, rel_path):
    """Python AST: function, class, method."""
    chunks = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Ha nem parse-olható, egész fájl egy chunk
        return [(source, 'module', rel_path, 1, source.count('\n')+1, [], [])]
    lines = source.splitlines(keepends=True)
    # Top-level functions és classes
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno if hasattr(node, 'end_lineno') else start + 50
            content = ''.join(lines[start-1:end])
            if len(content) >= MIN_CHUNK_CHARS:
                deps = [a.module for a in ast.walk(node) if isinstance(a, ast.ImportFrom) and a.module]
                deps += [a.names[0].name for a in ast.walk(node) if isinstance(a, ast.Import)]
                chunks.append((content, 'function', node.name, start, end, deps[:20], [node.name]))
        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = node.end_lineno if hasattr(node, 'end_lineno') else start + 100
            content = ''.join(lines[start-1:end])
            if len(content) >= MIN_CHUNK_CHARS:
                deps = []
                exports = [node.name]
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        exports.append(f"{node.name}.{item.name}")
                chunks.append((content, 'class', node.name, start, end, deps[:20], exports))
    # Ha nincs chunk (üres/only imports), egész fájl
    if not chunks:
        content = source[:MAX_CHUNK_CHARS]
        if len(content) >= MIN_CHUNK_CHARS:
            imports = [a.names[0].name for a in tree.body if isinstance(a, ast.Import)]
            chunks.append((content, 'module', rel_path, 1, len(lines), imports[:20], []))
    return chunks


def chunk_regex(source, rel_path, lang):
    """Regex chunking JS/TS/Rust/C++/Go/Java/etc."""
    chunks = []
    patterns = {
        'javascript': r'(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\s+(\w+)|class\s+(\w+))\s*[\({<]',
        'typescript': r'(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\s+(\w+)|class\s+(\w+)|interface\s+(\w+)|type\s+(\w+))\s*[\({<]',
        'rust': r'(?:pub\s+)?fn\s+(\w+)|(?:pub\s+)?struct\s+(\w+)|(?:pub\s+)?trait\s+(\w+)|impl\s+(\w+)',
        'cpp': r'(?:[\w:*&]+\s+)?(\w+)\s*\([^)]*\)\s*\{|\bclass\s+(\w+)|\bstruct\s+(\w+)',
        'go': r'func\s+(?:\([^)]*\)\s+)?(\w+)|type\s+(\w+)\s+(?:struct|interface)',
        'ruby': r'def\s+(?:self\.)?(\w+)|class\s+(\w+)|module\s+(\w+)',
        'java': r'(?:public|private|protected|static|final)*\s*(?:class|void|int|String|boolean)\s+(\w+)\s*\(|class\s+(\w+)',
        'csharp': r'(?:public|private|static|virtual|override|async)*\s*(?:class|void|int|string|bool|Task)\s+(\w+)\s*\(|class\s+(\w+)',
    }
    pattern = patterns.get(lang)
    if not pattern:
        # Config/markdown/shell: egész fájl
        content = source[:MAX_CHUNK_CHARS]
        if len(content) >= MIN_CHUNK_CHARS:
            return [(content, 'file', rel_path, 1, source.count('\n')+1, [], [])]
        return []
    # Regex darabolás
    lines = source.splitlines()
    matches = []
    for i, line in enumerate(lines):
        m = re.search(pattern, line)
        if m:
            name = next((g for g in m.groups() if g), f"block_{i}")
            matches.append((i, name))
    # Chunk-ok a match pozíciók között
    for idx, (line_idx, name) in enumerate(matches):
        start = line_idx
        end = matches[idx+1][0] if idx+1 < len(matches) else len(lines)
        content = '\n'.join(lines[start:end])
        if len(content) >= MIN_CHUNK_CHARS:
            chunks.append((content[:MAX_CHUNK_CHARS], 'block', name, start+1, end, [], [name]))
    # Ha nincs chunk, egész fájl
    if not chunks:
        content = source[:MAX_CHUNK_CHARS]
        if len(content) >= MIN_CHUNK_CHARS:
            chunks.append((content, 'file', rel_path, 1, len(lines), [], []))
    return chunks


def chunk_markdown(source, rel_path):
    """Markdown: heading-ek szerinti darabolás."""
    chunks = []
    lines = source.splitlines()
    sections = []
    current_start = 0
    current_heading = rel_path
    for i, line in enumerate(lines):
        if re.match(r'^#{1,3}\s+', line):
            if i > current_start:
                content = '\n'.join(lines[current_start:i])
                if len(content) >= MIN_CHUNK_CHARS:
                    sections.append((content, 'section', current_heading, current_start+1, i, [], []))
            current_start = i
            current_heading = re.sub(r'^#+\s+', '', line).strip()[:80]
    # Utolsó section
    if current_start < len(lines):
        content = '\n'.join(lines[current_start:])
        if len(content) >= MIN_CHUNK_CHARS:
            sections.append((content, 'section', current_heading, current_start+1, len(lines), [], []))
    if not sections:
        content = source[:MAX_CHUNK_CHARS]
        if len(content) >= MIN_CHUNK_CHARS:
            sections.append((content, 'section', rel_path, 1, len(lines), [], []))
    return sections


def split_large_chunk(content, chunk_type, name, start, deps, exports):
    """Nagy chunk felosztása overlap-pal."""
    result = []
    if len(content) <= MAX_CHUNK_CHARS:
        return [(content, chunk_type, name, start, start + content.count('\n'), deps, exports)]
    # 8000 char-onként, 200 overlap
    step = MAX_CHUNK_CHARS - CHUNK_OVERLAP
    for i in range(0, len(content), step):
        part = content[i:i+MAX_CHUNK_CHARS]
        if len(part) >= MIN_CHUNK_CHARS:
            line_offset = content[:i].count('\n')
            result.append((part, chunk_type, f"{name}_part{i//step+1}", start+line_offset, start+line_offset+part.count('\n'), deps, exports))
        if i + MAX_CHUNK_CHARS >= len(content):
            break
    return result


# ============================================================================
# CHUNKING PARANCS
# ============================================================================
def cmd_chunk():
    t0 = time.time()
    init_db()
    log("=" * 60)
    log("FASE 1: CHUNKING — Brain repo-k feldolgozása")
    log("=" * 60)
    files, skipped = collect_files()
    log(f"📁 {len(files)} fájl találva ({skipped} kihagyva)")
    repos = set(f['repo'] for f in files)
    log(f"📦 {len(repos)} repo")

    conn = get_db()
    # Tiszta tábla
    conn.execute("DELETE FROM chunks")
    conn.execute("DELETE FROM graph_edges")
    conn.commit()

    jsonl_file = open(JSONL_PATH, "w", encoding="utf-8")
    total_chunks = 0
    stats = defaultdict(lambda: defaultdict(int))

    for i, finfo in enumerate(files):
        if (i+1) % 100 == 0 or i == 0:
            log(f"  [{i+1}/{len(files)}] {finfo['repo']}/{os.path.basename(finfo['rel_path'])} ({finfo['lang']})")

        try:
            with open(finfo['fpath'], 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except:
            continue

        # Chunking nyelv szerint
        if finfo['lang'] == 'python':
            raw_chunks = chunk_python(source, finfo['rel_path'])
        elif finfo['lang'] == 'markdown':
            raw_chunks = chunk_markdown(source, finfo['rel_path'])
        elif finfo['lang'] in ('config', 'shell', 'sql', 'graphql', 'proto'):
            content = source[:MAX_CHUNK_CHARS]
            raw_chunks = [(content, 'config', finfo['rel_path'], 1, source.count('\n')+1, [], [])] if len(content) >= MIN_CHUNK_CHARS else []
        else:
            raw_chunks = chunk_regex(source, finfo['rel_path'], finfo['lang'])

        # Split nagy chunk-ok
        final_chunks = []
        for chunk in raw_chunks:
            content, ctype, cname, start, end, deps, exports = chunk
            final_chunks.extend(split_large_chunk(content, ctype, cname, start, deps, exports))

        # Insert DB + JSONL
        for content, ctype, cname, start, end, deps, exports in final_chunks:
            row = {
                'repo': finfo['repo'],
                'path': finfo['rel_path'],
                'ext': finfo['ext'],
                'lang': finfo['lang'],
                'chunk_type': ctype,
                'chunk_name': cname[:200],
                'line_start': start,
                'line_end': end,
                'content': content,
                'dependencies': json.dumps(deps),
                'exports': json.dumps(exports),
            }
            jsonl_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            conn.execute(
                """INSERT INTO chunks (repo, path, ext, lang, chunk_type, chunk_name,
                   line_start, line_end, content, dependencies, exports)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (row['repo'], row['path'], row['ext'], row['lang'],
                 row['chunk_type'], row['chunk_name'], row['line_start'],
                 row['line_end'], row['content'], row['dependencies'], row['exports'])
            )
            total_chunks += 1
            stats[finfo['lang']][ctype] += 1

    jsonl_file.close()
    conn.commit()
    conn.close()

    log(f"\n✅ Chunking kész: {total_chunks} chunk, {time.time()-t0:.1f}s")
    log(f"   JSONL: {JSONL_PATH}")
    log(f"   DB: {DB_PATH}")
    log(f"   Nyelvek:")
    for lang, types in sorted(stats.items()):
        total = sum(types.values())
        log(f"     {lang}: {total} chunk ({', '.join(f'{k}:{v}' for k,v in sorted(types.items()))})")


def embed_to_blob(vec):
    return vec.astype(np.float32).tobytes()

def blob_to_vec(blob):
    return np.frombuffer(blob, dtype=np.float32)


def cmd_embed():
    from sentence_transformers import SentenceTransformer
    t0 = time.time()
    log("=" * 60)
    log("FASE 2: EMBEDDING — GPU vektorizáció")
    log("=" * 60)
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    model = SentenceTransformer(MODEL_NAME, device="cuda")
    log(f"✅ Modell: {MODEL_NAME} ({model.get_sentence_embedding_dimension()}-dim)")

    conn = get_db()
    rows = conn.execute("SELECT id, content FROM chunks WHERE embedding IS NULL ORDER BY id").fetchall()
    total = len(rows)
    log(f"📊 Vektorizálandó: {total} chunk")
    if total == 0:
        log("✅ Minden chunk vektorizálva!")
        conn.close()
        return

    done = 0
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        ids = [r[0] for r in batch]
        texts = [r[1][:8000] for r in batch]
        embeddings = model.encode(texts, batch_size=len(batch), show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        conn.executemany("UPDATE chunks SET embedding = ? WHERE id = ?", [(embed_to_blob(embeddings[j]), ids[j]) for j in range(len(batch))])
        conn.commit()
        done += len(batch)
        if done % 1024 == 0 or done == total:
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed > 0 else 0
            log(f"  [{done}/{total}] {100*done/total:.0f}% ({rate:.0f} chunk/s)")

    conn.close()
    log(f"✅ Embedding kész: {total} chunk, {time.time()-t0:.1f}s")


def cmd_graph():
    t0 = time.time()
    log("=" * 60)
    log("FASE 3: GRAPH — Logikai kapcsolatok építése")
    log("=" * 60)
    conn = get_db()
    conn.execute("DELETE FROM graph_edges")
    conn.commit()

    # Chunk-ok betöltése: id, repo, path, dependencies, exports, chunk_name
    rows = conn.execute("SELECT id, repo, path, dependencies, exports, chunk_name FROM chunks").fetchall()
    log(f"📊 {len(rows)} chunk feldolgozása")

    # Index: (repo, name) → chunk_id
    name_index = {}
    for rid, repo, path, deps_json, exports_json, cname in rows:
        try:
            exports = json.loads(exports_json) if exports_json else []
        except:
            exports = []
        for exp in exports:
            name_index[(repo, exp)] = rid
            # Globális is: név → chunk_id (első találat)
            if exp not in name_index:
                name_index[exp] = rid

    edges_added = 0
    # contains edge: fájl → chunk (már benne van a path)
    # imports edge: chunk A importál B-t
    for rid, repo, path, deps_json, exports_json, cname in rows:
        try:
            deps = json.loads(deps_json) if deps_json else []
        except:
            deps = []
        for dep in deps:
            dep = dep.split('.')[0] if dep else ''
            if not dep:
                continue
            # Keresés: ugyanabban a repo-ban
            target_id = name_index.get((repo, dep))
            if target_id and target_id != rid:
                conn.execute("INSERT INTO graph_edges (from_chunk, to_chunk, edge_type) VALUES (?, ?, 'imports')", (rid, target_id))
                edges_added += 1
            # Globális keresés
            elif dep in name_index and name_index[dep] != rid:
                conn.execute("INSERT INTO graph_edges (from_chunk, to_chunk, edge_type) VALUES (?, ?, 'imports')", (rid, name_index[dep]))
                edges_added += 1

    conn.commit()
    conn.close()
    log(f"✅ Graph kész: {edges_added} él, {time.time()-t0:.1f}s")


def cmd_info():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    embedded = conn.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL").fetchone()[0]
    edges = conn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
    repos = conn.execute("SELECT COUNT(DISTINCT repo) FROM chunks").fetchone()[0]
    by_lang = conn.execute("SELECT lang, COUNT(*) FROM chunks GROUP BY lang ORDER BY COUNT(*) DESC").fetchall()
    by_type = conn.execute("SELECT chunk_type, COUNT(*) FROM chunks GROUP BY chunk_type ORDER BY COUNT(*) DESC").fetchall()
    top_repos = conn.execute("SELECT repo, COUNT(*) FROM chunks GROUP BY repo ORDER BY COUNT(*) DESC LIMIT 10").fetchall()
    db_size = os.path.getsize(DB_PATH) / 1024 / 1024 if os.path.exists(DB_PATH) else 0
    conn.close()
    print(f"📊 Brain RAG DB: {DB_PATH}")
    print(f"   DB méret: {db_size:.1f} MB")
    print(f"   Repo-k: {repos}")
    print(f"   Chunk-ok: {total}")
    print(f"   Vektorizált: {embedded}/{total} ({100*embedded/total:.0f}%)")
    print(f"   Graph élek: {edges}")
    print(f"   Nyelvenként:")
    for lang, cnt in by_lang:
        print(f"     {lang}: {cnt}")
    print(f"   Típusonként:")
    for ctype, cnt in by_type:
        print(f"     {ctype}: {cnt}")
    print(f"   Top repo-k:")
    for repo, cnt in top_repos:
        print(f"     {repo}: {cnt}")


def cmd_search(query, top_k=10, repo_filter=None, lang=None, chunk_type=None,
               depth=0, breadth=False, min_score=0.3):
    from sentence_transformers import SentenceTransformer
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    model = SentenceTransformer(MODEL_NAME, device="cuda")
    q_vec = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]

    conn = get_db()
    # SQL szűrés
    where = ["embedding IS NOT NULL"]
    params = []
    if repo_filter:
        # Glob támogatás: Light* → LIKE 'Light%'
        if '*' in repo_filter:
            where.append("repo LIKE ?")
            params.append(repo_filter.replace('*', '%'))
        else:
            where.append("repo = ?")
            params.append(repo_filter)
    if lang:
        where.append("lang = ?")
        params.append(lang)
    if chunk_type:
        where.append("chunk_type = ?")
        params.append(chunk_type)

    sql = f"SELECT id, repo, path, lang, chunk_type, chunk_name, line_start, line_end, content, embedding FROM chunks WHERE {' AND '.join(where)}"
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print("Nincs találat!")
        conn.close()
        return

    # Cosine sim
    scores = []
    for row in rows:
        vec = blob_to_vec(row[9])
        score = float(np.dot(q_vec, vec))
        if score >= min_score:
            scores.append((score, row))
    scores.sort(key=lambda x: -x[0])

    print(f'\n🔍 Keresés: "{query}"')
    filters = []
    if repo_filter: filters.append(f"repo={repo_filter}")
    if lang: filters.append(f"lang={lang}")
    if chunk_type: filters.append(f"type={chunk_type}")
    if filters: print(f"   Szűrő: {', '.join(filters)}")
    print(f"   {len(scores)} találat (min_score={min_score}), top {top_k}:\n")

    for rank, (score, row) in enumerate(scores[:top_k], 1):
        cid = row[0]
        print(f"  {rank}. [{score:.4f}] {row[1]}/{row[2]}")
        print(f"     {row[3]}/{row[4]}: {row[5]} (L{row[6]}-{row[7]})")
        print(f"     {row[8][:200].strip()}...")
        if depth > 0:
            # Ki hívja ezt? (imports edge)
            callers = conn.execute(
                "SELECT c.repo, c.path, c.chunk_name FROM graph_edges g JOIN chunks c ON g.from_chunk=c.id WHERE g.to_chunk=? AND g.edge_type='imports' LIMIT ?", (cid, depth*5)
            ).fetchall()
            if callers:
                print(f"     📎 Hívók (depth={depth}):")
                for c in callers[:depth*3]:
                    print(f"        ← {c[0]}/{c[1]} ({c[2]})")
        if breadth:
            # Ugyanez a pattern más repókban
            pattern_words = row[5].split('_')[:2]
            if pattern_words:
                pattern = '%'.join(pattern_words)
                cross = conn.execute(
                    "SELECT DISTINCT repo, path, chunk_name FROM chunks WHERE chunk_name LIKE ? AND repo != ? LIMIT 5", (f'%{pattern}%', row[1])
                ).fetchall()
                if cross:
                    print(f"     🔗 Cross-repo:")
                    for c in cross:
                        print(f"        → {c[0]}/{c[1]} ({c[2]})")
        print()

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Brain RAG vektorizáció")
    parser.add_argument("--all", action="store_true", help="Minden: chunk+embed+graph")
    parser.add_argument("--chunk", action="store_true", help="Csak chunking")
    parser.add_argument("--embed", action="store_true", help="Csak embedding")
    parser.add_argument("--graph", action="store_true", help="Csak graph")
    parser.add_argument("--search", type=str, help="Szemantikus keresés")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--repo", type=str, default=None, help="Repo szűrő (glob: Light*)")
    parser.add_argument("--lang", type=str, default=None)
    parser.add_argument("--type", type=str, default=None, help="chunk_type szűrő")
    parser.add_argument("--depth", type=int, default=0, help="Mélység: 0=none, 1=hívók, 2=hívó hívói")
    parser.add_argument("--breadth", action="store_true", help="Cross-repo minta keresés")
    parser.add_argument("--min-score", type=float, default=0.3)
    parser.add_argument("--info", action="store_true")
    args = parser.parse_args()

    if args.info:
        cmd_info()
    elif args.all:
        cmd_chunk()
        cmd_embed()
        cmd_graph()
        cmd_info()
    elif args.chunk:
        cmd_chunk()
    elif args.embed:
        cmd_embed()
    elif args.graph:
        cmd_graph()
    elif args.search:
        cmd_search(args.search, args.top_k, args.repo, args.lang, args.type,
                   args.depth, args.breadth, args.min_score)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
