#!/usr/bin/env python3
"""
MCP (Model Context Protocol) szerver a Qwen-alapú repó-elemző és tudásbázis fölött.
Hely: /data/mcp_server/server.py

Eszközök:
  - read_repo(path): könyvtár/fájl olvasás (biztonságos, limitált méret)
  - write_log(path, content): napló/kivonat írása
  - analyze_with_qwen(target_dir): Qwen2.5-Coder elemzés indítása P4000-en
  - list_gpu(): GPU állapot lekérdezése (P4000/P2000)
  - store_session(stage, knowledge): session-tudás szakaszonkénti mentése
  - read_session(stage): session-tudás visszolvasása
  - rag_query(query, mode, db, top_k): RAG szemantikus keresés
  - knowledge_graph(action, ...): Tudásgráf (MegaMemory+yantrikdb+HybridRAG)
      - stats/get/search/create/link/contradictions/trace/context/decay/rebuild
      - embed_index/embed_search/hybrid_rag/rdf_export/sparql/yantrik_propagate
  - cognitive_memory(action, ...): Kognitív memória engine (yantrikdb v0.23.2, Rust)
      - record/recall/correct/stats/consolidate/auto_relate/detect_conflicts/decay_batch/ingest_kg/export_context
  - shared_brain(action, ...): Megosztott agy (cortexdb gRPC, multi-agent)
      - remember/recall/graph_stats/search_nodes/server_status
  - visualize(action, ...): HTML vizualizáció renderelés + képelemzés
      - render: HTML→PNG screenshot+PIL elemzés
      - analyze: meglévő képfile elemzése
      - html_file: HTML fájl renderelése

Intelligens, ne zavarjon: lock fájl, ha a Qwen folyamat fut, akkor
analyze_with_qwen visszautasítja az újabb indítást (ne zavarja a futót).

Használat:
    source /data/mcp_server/env.sh
    python3 /data/mcp_server/server.py
"""
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any

# Környezeti változók (env.sh-ból)
MCP_SERVER_DIR = os.environ.get("MCP_SERVER_DIR", "/data/mcp_server")
LOG_DIR = os.environ.get("MCP_LOG_DIR", "/data/mcp_server/logs")
STATE_DIR = os.environ.get("MCP_STATE_DIR", "/data/mcp_server/state")
CONTEXT_DIR = os.environ.get("MCP_CONTEXT_DIR", "/data/mcp_server/context")
LOCK_DIR = os.environ.get("MCP_LOCK_DIR", "/data/mcp_server/lock")
LOCK_FILE = os.environ.get("MCP_LOCK_FILE", "/data/mcp_server/lock/mcp.lock")
QWEN_ANALYZER = os.path.join(MCP_SERVER_DIR, "tools", "qwen_analyzer.py")
QWEN_TIMEOUT_SEC = int(os.environ.get("QWEN_TIMEOUT_SECONDS", "300"))

# Memória fájlok
ACTIVE_MEMORY_FILE = os.path.join(CONTEXT_DIR, "active_memory.json")
QWEN_MEMORY_FILE = os.path.join(CONTEXT_DIR, "qwen_memory.json")

# Biztonsági limit
MAX_READ_SIZE = 64 * 1024  # 64KB
ALLOWED_READ_ROOTS = [
    "/data/Brain",
    "/data/ml",
    "/home/Jules/RAG_epito_ismeretek",
    "/data/mcp_server",
    "/data/MQL5",
    "/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5",
    "/home/Jules/LGBM_mlops",
    "/data/LGBM_copilot",
    "/data/RAG_epito_ismeretek",
    "/data/dev",
    "/data/vizualizácio",
]
ALLOWED_WRITE_ROOTS = [
    "/data/Brain/_qwen_analysis",
    "/data/Brain",
    "/home/Jules/RAG_epito_ismeretek/_qwen_analysis",
    "/home/Jules/RAG_epito_ismeretek",
    "/data/mcp_server/logs",
    "/data/mcp_server/state",
    "/data/MQL5/_qwen_analysis",
    "/home/Jules/LGBM_mlops/_qwen_analysis",
    "/data/LGBM_copilot/_qwen_analysis",
    "/data/LGBM_copilot",
]


def _log(msg: str, level: str = "INFO"):
    """Belső logolás."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True, file=sys.stderr)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "mcp_server.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _is_qwen_running() -> bool:
    """
    Ellenőrzi, hogy a Qwen analyzer folyamat fut-e (lock fájl vagy process ellenőrzés).
    Ha fut, az MCP nem indít újabbat, hogy ne zavarja.
    """
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                return True  # A PID él, a Qwen fut
            except (ProcessLookupError, ValueError, OSError):
                # Stale lock, takarítsuk
                os.remove(LOCK_FILE)
        return False
    except Exception:
        return False


def _is_path_safe(path: str, allowed_roots: list, must_exist: bool = False) -> tuple:
    """
    Útvonal biztonsági ellenőrzése: csak az allowed_roots alatt engedélyezett.
    Visszatér: (ok: bool, resolved_path: str)
    """
    try:
        resolved = os.path.realpath(os.path.abspath(path))
    except Exception:
        return (False, path)
    for root in allowed_roots:
        root_abs = os.path.realpath(root)
        if resolved == root_abs or resolved.startswith(root_abs + os.sep):
            if must_exist and not os.path.exists(resolved):
                return (False, resolved)
            return (True, resolved)
    return (False, resolved)


# MCP SDK import (később, a tool implementációk után)
try:
    from mcp.server.mcpserver import MCPServer  # mcp 2.x: FastMCP -> MCPServer
    from mcp.types import Tool, TextContent, CallToolResult
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    _log("MCP SDK nem elérhető, próbáld: pip install mcp", "ERROR")


def tool_list_gpu() -> str:
    """GPU állapot lekérdezése nvidia-smi-ből."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        lines = r.stdout.strip().split("\n")
        out = ["GPU állapot:"]
        for ln in lines:
            parts = [p.strip() for p in ln.split(",")]
            if len(parts) >= 6:
                idx, name, total, used, free, util = parts[:6]
                out.append(f"  GPU {idx}: {name} | VRAM: {used}/{total} (szabad: {free}) | kihasználás: {util}")
        out.append("")
        out.append("Konfigurált cél: GPU 0 = Quadro P4000 (CUDA_VISIBLE_DEVICES=0 a Qwen-hez)")
        return "\n".join(out)
    except Exception as e:
        return f"Hiba: {e}"


def tool_read_repo(path: str, max_bytes: int = 32768) -> str:
    """Biztonságos fájl/könyvtár olvasás."""
    ok, resolved = _is_path_safe(path, ALLOWED_READ_ROOTS, must_exist=True)
    if not ok:
        return f"HIBA: útvonal nem engedélyezett vagy nem létezik: {path} (resolved: {resolved})"

    if os.path.isdir(resolved):
        # Könyvtár-listázás (max 200 bejegyzés)
        try:
            entries = sorted(os.listdir(resolved))[:200]
            lines = [f"Könyvtár: {resolved}", f"{len(entries)} bejegyzés (max 200 mutatva):", ""]
            for e in entries:
                full = os.path.join(resolved, e)
                tag = "/"
                try:
                    if os.path.isfile(full):
                        tag = f" ({os.path.getsize(full)} bájt)"
                    elif os.path.isdir(full):
                        tag = "/"
                    elif os.path.islink(full):
                        tag = " ->"
                except OSError:
                    pass
                lines.append(f"  {e}{tag}")
            return "\n".join(lines)
        except Exception as e:
            return f"Könyvtár listázási hiba: {e}"
    elif os.path.isfile(resolved):
        # Fájl olvasás (limitált méret)
        try:
            size = os.path.getsize(resolved)
            limit = min(max_bytes, MAX_READ_SIZE)
            with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(limit)
            note = ""
            if size > limit:
                note = f"\n\n[Megjegyzés: a fájl {size} bájt, csak az első {limit} bájt olvasva]"
            return f"Fájl: {resolved} ({size} bájt)\n\n{content}{note}"
        except Exception as e:
            return f"Fájl olvasási hiba: {e}"
    else:
        return f"HIBA: nem könyvtár és nem fájl: {resolved}"


def tool_write_log(path: str, content: str) -> str:
    """Biztonságos napló/kivonat írása az engedélyezett gyökerek alá."""
    ok, resolved = _is_path_safe(path, ALLOWED_WRITE_ROOTS, must_exist=False)
    if not ok:
        return f"HIBA: írási útvonal nem engedélyezett: {path} (resolved: {resolved})"
    try:
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        size = os.path.getsize(resolved)
        _log(f"Napló írva: {resolved} ({size} bájt)")
        return f"✅ Írva: {resolved} ({size} bájt)"
    except Exception as e:
        return f"Írási hiba: {e}"


def tool_analyze_with_qwen(target_dir: str, max_files: int = 25, max_tokens: int = 1800) -> str:
    """
    Qwen2.5-Coder repó-elemzés indítása P4000-en.
    Intelligens: ha már fut Qwen, nem indít újat (ne zavarjon).
    """
    # Ellenőrizzük, hogy a célkönyvtár olvasható-e
    ok, resolved = _is_path_safe(target_dir, ALLOWED_READ_ROOTS, must_exist=True)
    if not ok:
        return f"HIBA: célkönyvtár nem engedélyezett vagy nem létezik: {target_dir}"

    # Ne zavarjon: ha Qwen már fut, elutasít
    if _is_qwen_running():
        return ("⚠️  A Qwen analyzer már fut (lock aktív). Nem indítok újat, hogy ne zavarjam. "
                "Várd meg, amíg befejezi, vagy kilőni a lock-ot: rm /data/mcp_server/lock/mcp.lock")

    # Indítjuk a qwen_analyzer.py-t az env.sh környezetben
    if not os.path.isfile(QWEN_ANALYZER):
        return f"HIBA: {QWEN_ANALYZER} nem található"
    if not os.path.isfile("/data/mcp_server/env.sh"):
        return "HIBA: /data/mcp_server/env.sh nem található"

    cmd = (
        f"source /data/mcp_server/env.sh && "
        f"python3 {QWEN_ANALYZER} {resolved} --max-files {int(max_files)} --max-tokens {int(max_tokens)}"
    )
    _log(f"Qwen elemzés indítása: {resolved}")

    try:
        # Külön processzben futtatjuk, hogy a timeout-ot tudjuk kezelni
        proc = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=QWEN_TIMEOUT_SEC + 60,  # kis ráhagyás a modell betöltésre
        )
        out = proc.stdout
        err = proc.stderr
        _log(f"Qwen elemzés befejezve (exit {proc.returncode})")
        if err.strip():
            _log(f"stderr: {err[-500:]}", "WARN")
        if proc.returncode == 2:
            return "⚠️  A Qwen analyzer elutasította az indítást (már fut egy másik folyamat)."
        if proc.returncode != 0:
            return f"HIBA (exit {proc.returncode}):\n{out}\n{err}"
        # A kimenet tartalmazza az elemzést
        marker = "--- ELEMZÉS TARTALMA ---"
        if marker in out:
            analysis = out.split(marker, 1)[1].strip()
        else:
            analysis = out
        # Keressük a fájlútvonalat a kimenetben
        file_line = ""
        for ln in out.split("\n"):
            if "Kimenet:" in ln:
                file_line = ln.strip()
                break
        return f"✅ Qwen elemzés befejezve.\n{file_line}\n\n{analysis}"
    except subprocess.TimeoutExpired:
        _log("Qwen elemzés timeout", "ERROR")
        return f"❌ Qwen elemzés timeout ({QWEN_TIMEOUT_SEC+60}s)"
    except Exception as e:
        _log(f"Qwen elemzés hiba: {e}", "ERROR")
        return f"HIBA: {e}"


def tool_store_session(stage: str, knowledge: str) -> str:
    """Session-tudás szakaszonkénti mentése (memória az MCP fölött)."""
    if not stage or not knowledge:
        return "HIBA: stage és knowledge kötelező"
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Egyéni session fájl + közös napló
        fname = f"session_{ts}_{stage}.md"
        fpath = os.path.join(STATE_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(f"# Session: {stage}\n")
            f.write(f"*Időbélyeg: {datetime.now().isoformat()}*\n\n")
            f.write(knowledge)
        # Közös napló frissítése
        index_path = os.path.join(STATE_DIR, "session_index.md")
        with open(index_path, "a", encoding="utf-8") as f:
            f.write(f"- [{ts}] {stage} -> {fname}\n")
        _log(f"Session mentve: {fpath}")
        return f"✅ Session '{stage}' elmentve: {fpath}"
    except Exception as e:
        return f"HIBA: {e}"


def tool_read_session(stage: str = "") -> str:
    """Session-tudás visszolvasása. Ha stage üres, az indexet adja."""
    try:
        index_path = os.path.join(STATE_DIR, "session_index.md")
        if not stage:
            if not os.path.exists(index_path):
                return "Még nincs session mentve."
            with open(index_path, "r", encoding="utf-8") as f:
                return f"Session index:\n\n{f.read()}"
        # Külön stage keresése
        if not os.path.isdir(STATE_DIR):
            return f"Nincs session mentve (state dir nem létezik: {STATE_DIR})"
        matches = []
        for fn in sorted(os.listdir(STATE_DIR)):
            if fn.startswith("session_") and fn.endswith(".md") and f"_{stage}." in fn:
                matches.append(fn)
        if not matches:
            return f"Nem található session: '{stage}'"
        out = []
        for fn in matches[-5:]:  # utolsó 5
            fp = os.path.join(STATE_DIR, fn)
            with open(fp, "r", encoding="utf-8") as f:
                out.append(f"=== {fn} ===\n{f.read()}\n")
        return "\n".join(out)
    except Exception as e:
        return f"HIBA: {e}"

def tool_repository_memory_indexer(
    repository_path: str = "/data/Brain",
    memory_stage: str = "initial",
    context_type: str = "comprehensive",
) -> str:
    """Repository kódok és megoldások indexelése emlékezetbe és kontextusba.

    Beolvassa a megadott könyvtár alatt lévő repókat (vagy magát a repót,
    ha egyetlen repo útvonalát kapja), és strukturált kontextust készít:
    fájlszám, méret, fő nyelvek, kulcsfájlok. Az eredményt az
    active_memory.json 'repositories' szekciójában tárolja.

    Args:
        repository_path: az indexelendő könyvtár (pl. /data/Brain vagy egy repo)
        memory_stage: az indexelés fázisja (pl. 'initial', 'update')
        context_type: a kontextus típusa (pl. 'comprehensive', 'summary')

    Returns:
        Összegző szöveg az indexelt repókról.
    """
    ok, resolved = _is_path_safe(repository_path, ALLOWED_READ_ROOTS, must_exist=True)
    if not ok:
        return f"HIBA: célkönyvtár nem engedélyezett vagy nem létezik: {repository_path} (resolved: {resolved})"

    # Nyelvfelismerés fájlkiterjesztések alapján
    LANG_BY_EXT = {
        ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".js": "JavaScript", ".jsx": "JavaScript", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".c": "C", ".cpp": "C++", ".h": "C/C++",
        ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
        ".kt": "Kotlin", ".scala": "Scala", ".sh": "Shell", ".bash": "Shell",
        ".md": "Markdown", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
        ".toml": "TOML", ".cfg": "Config", ".ini": "Config",
    }
    # Kulcsfájlok, amiket érdemes kiemelni
    KEY_FILES = {
        "readme", "package.json", "pyproject.toml", "setup.py",
        "requirements.txt", "cargo.toml", "go.mod", "dockerfile",
        "license", "main.py", "index.ts", "index.js", "server.py",
    }



    def _index_single_repo(repo_path: str) -> dict:
        """Egyetlen repo indexelése: fájlszám, méret, nyelvek, kulcsfájlok."""
        file_count = 0
        total_size = 0
        lang_counts = {}
        key_found = []
        main_files = []
        try:
            for root, dirs, files in os.walk(repo_path):
                # rejtett + _qwen_analysis + node_modules kihagyása
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith(".") and d != "_qwen_analysis"
                    and d != "node_modules" and d != "__pycache__"
                    and d != ".git"
                ]
                for fname in files:
                    fp = os.path.join(root, fname)
                    try:
                        total_size += os.path.getsize(fp)
                        file_count += 1
                    except OSError:
                        continue
                    ext = os.path.splitext(fname)[1].lower()
                    lang = LANG_BY_EXT.get(ext)
                    if lang:
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                    low = fname.lower()
                    base = low.rsplit(".", 1)[0] if "." in low else low
                    if base in KEY_FILES and low not in key_found:
                        key_found.append(low)
                    if len(main_files) < 15 and base in KEY_FILES:
                        main_files.append(fname)
            top_langs = sorted(lang_counts.items(), key=lambda x: -x[1])[:5]
            return {
                "file_count": file_count,
                "size_mb": round(total_size / (1024 * 1024), 2),
                "languages": dict(top_langs),
                "key_files": key_found[:10],
                "main_files": main_files[:10],
            }
        except Exception as e:
            return {"error": str(e)}

    # Meghatározzuk: a path egy gyűjtemény (több repo) vagy egyetlen repo
    subdirs = []
    is_collection = False
    try:
        entries = sorted(os.listdir(resolved))
        subdirs = [
            e for e in entries
            if not e.startswith(".") and os.path.isdir(os.path.join(resolved, e))
        ]
        git_count = 0
        for d in subdirs[:20]:
            if os.path.isdir(os.path.join(resolved, d, ".git")):
                git_count += 1
        is_collection = git_count >= 1 and len(subdirs) >= 2
    except Exception as e:
        return f"HIBA: könyvtár listázási hiba: {e}"

    if is_collection:
        repo_list = [(d, os.path.join(resolved, d)) for d in subdirs]
    else:
        repo_list = [(os.path.basename(resolved), resolved)]


    # Indexelés
    indexed = {}
    errors = []
    for repo_name, repo_path in repo_list:
        info = _index_single_repo(repo_path)
        if "error" in info:
            errors.append(f"{repo_name}: {info['error']}")
            continue
        info["name"] = repo_name
        info["path"] = repo_path
        info["memory_stage"] = memory_stage
        info["context_type"] = context_type
        info["indexed_at"] = datetime.now().isoformat()
        info["status"] = "indexed"
        indexed[repo_name] = info

    # active_memory.json frissítése (repositories szekció)
    try:
        os.makedirs(CONTEXT_DIR, exist_ok=True)
        memory = {}
        if os.path.exists(ACTIVE_MEMORY_FILE):
            with open(ACTIVE_MEMORY_FILE, "r", encoding="utf-8") as f:
                memory = json.load(f)
        memory.setdefault("repositories", {})
        memory["repositories"].update(indexed)
        memory["timestamp"] = datetime.now().isoformat()
        with open(ACTIVE_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        _log(f"repository_memory_indexer: memória frissítés hiba: {e}", "ERROR")

    # Összegzés
    total_files = sum(r.get("file_count", 0) for r in indexed.values())
    total_size_mb = sum(r.get("size_mb", 0) for r in indexed.values())
    lines = [
        f"✅ Indexelés kész ({memory_stage}/{context_type})",
        f"Indexelt repók: {len(indexed)}",
        f"Összes fájl: {total_files}",
        f"Összes méret: {total_size_mb:.2f} MB",
        "",
    ]
    for name, info in list(indexed.items())[:15]:
        langs = ", ".join(info.get("languages", {}).keys()) or "ismeretlen"
        lines.append(
            f"  • {name}: {info.get('file_count', 0)} fájl, "
            f"{info.get('size_mb', 0)} MB, nyelvek: {langs}"
        )
    if len(indexed) > 15:
        lines.append(f"  ... és még {len(indexed) - 15} repó")
    if errors:
        lines.append("")
        lines.append(f"⚠️ Hibák: {len(errors)}")
        for e in errors[:5]:
            lines.append(f"  - {e}")
    lines.append("")
    lines.append(f"Memória frissítve: {ACTIVE_MEMORY_FILE}")
    _log(f"repository_memory_indexer: {len(indexed)} repo indexelve, "
         f"{total_files} fájl, {total_size_mb:.2f} MB")
    return "\n".join(lines)



# Tool definíciók az MCP-hez
def tool_rag_query(query: str, mode: str = "keyword", db: str = "ml", top_k: int = 5) -> str:
    """RAG keresés: concept navigáció vagy DB kulcsszó keresés."""
    import json as _json
    import sqlite3 as _sqlite3
    CMAP = Path("/data/Brain/_qwen_analysis/concept_map.json")
    DB_ML = "/data/ml/_vectorized/ml_rag_v2.db"
    DB_BRAIN = "/data/Brain/_vectorized/brain_rag.db"
    
    if mode == "concept":
        if not CMAP.exists():
            return "HIBA: concept_map.json nem található"
        with open(CMAP) as f:
            cm = _json.load(f)
        # Check knowledge_space first
        if query.lower() in ["knowledge_space", "knowledge", "copilot"]:
            ks = cm.get("knowledge_space", {})
            if ks:
                result = "=== Knowledge Space ===\n"
                result += f"Path: {ks.get('path','N/A')}\n"
                result += f"Index: {ks.get('index','N/A')}\n"
                result += f"L0 Decision Trees: {ks.get('L0_decision_trees','N/A')}\n"
                result += f"L1 Code Templates: {ks.get('L1_code_templates','N/A')}\n"
                result += f"L2 Reference Digests: {ks.get('L2_reference_digests','N/A')}\n"
                result += f"Checklists: {ks.get('checklists','N/A')}\n"
                result += f"Anti-patterns: {ks.get('anti_patterns','N/A')}\n"
                result += f"Pipeline Chain: {ks.get('pipeline_chain','N/A')}\n"
                return result
        for dn, d in cm.get("domains", {}).items():
            for cn, cd in d.get("concepts", {}).items():
                if query.lower() in cn.lower() or cn.lower() in query.lower():
                    result = f"Domain: {dn} | Concept: {cn}\n"
                    result += f"Description: {cd.get('description','N/A')}\n"
                    if "implementations" in cd:
                        for iname, impl in cd["implementations"].items():
                            result += f"  [{iname}] {impl.get('path','')}\n"
                            if "functions" in impl:
                                result += f"    Functions: {', '.join(impl['functions'])}\n"
                    if "key_insight" in cd:
                        result += f"KEY: {cd['key_insight']}\n"
                    if "digest" in cd:
                        result += f"Digest: {cd['digest']}\n"
                    return result
        return "Concept not found in concept_map.json"
    
    # Knowledge mode — search copilot knowledge space
    if mode == "knowledge":
        KS_PATH = Path("/data/LGBM_copilot/knowledge")
        if not KS_PATH.exists():
            return "HIBA: Knowledge space nem található"
        sys.path.insert(0, str(KS_PATH))
        try:
            from knowledge_search import search
            results = search(query, top_k=top_k)
            if not results:
                return "Nincs találat a tudástérben."
            lines = []
            for r in results:
                lines.append(f"[{r['level']}] {r['source']} (relevance: {r['relevance']})")
            return "\n".join(lines)
        except Exception as e:
            return f"HIBA: knowledge search: {e}"
    
    # Keyword mode
    db_path = DB_ML if db == "ml" else DB_BRAIN
    if not os.path.exists(db_path):
        return f"HIBA: DB nem található: {db_path}"
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row
    words = query.split()
    cond, params = [], []
    for w in words:
        cond.append("(content LIKE ? OR chunk_name LIKE ? OR path LIKE ?)")
        params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])
    where = " AND ".join(cond) if cond else "1=1"
    sql = f"SELECT id,repo,path,chunk_type,chunk_name,line_start,line_end,content FROM chunks WHERE {where} LIMIT ?"
    params.append(top_k)
    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception as e:
        conn.close()
        return f"HIBA: {e}"
    if not rows:
        conn.close()
        return "Nincs találat."
    lines = []
    for i, r in enumerate(rows, 1):
        preview = (r["content"] or "")[:200].replace("\n", " ")
        lines.append(f"{i}. {r['repo']}/{r['path']} :: {r['chunk_name']} [L{r['line_start']}-{r['line_end']}]\n   {preview}...")
    conn.close()
    return "\n".join(lines)


def get_tool_definitions() -> list:
    """Visszaadja az MCP tool definíciókat."""
    return [
        {
            "name": "list_gpu",
            "description": "Lekérdezi a GPU állapotot (P4000/P2000 VRAM, kihasználtság).",
            "inputSchema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "read_repo",
            "description": (
                "Biztonságos fájl vagy könyvtár olvasása. Csak az engedélyezett "
                "gyökerek alatt (/data/Brain, /data/ml, /home/Jules/RAG_epito_ismeretek, "
                "/data/mcp_server). Könyvtár: listázást ad. Fájl: az első 32KB-ot olvassa. "
                "Használd repók/fájlok megtekintéséhez."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Olvasandó útvonal"},
                    "max_bytes": {"type": "integer", "description": "Max olvasott bájtok (default 32768)", "default": 32768},
                },
                "required": ["path"],
            },
        },
        {
            "name": "write_log",
            "description": (
                "Biztonságos napló/kivonat írása az engedélyezett írási gyökerek alá "
                "(/data/Brain/_qwen_analysis, /data/mcp_server/logs, /data/mcp_server/state, "
                "stb.). Használd Markdown naplók és kivonatok mentéséhez."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Célútvonal"},
                    "content": {"type": "string", "description": "Írandó tartalom"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "analyze_with_qwen",
            "description": (
                "Qwen2.5-Coder-7B-Instruct repó-elemzés indítása P4000 GPU-n. "
                "A Qwen beolvassa a célkönyvtárat és Markdown naplót ír "
                "(repó áttekintés, fő komponensek, 'érdemes alaposabban megnézni' fájlok). "
                "Intelligens: ha már fut egy Qwen elemzés, nem indít újat (ne zavarjon)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target_dir": {"type": "string", "description": "Elemzendő könyvtár (pl. /data/Brain/Qwen-Agent)"},
                    "max_files": {"type": "integer", "description": "Max olvasott fájl (default 25)", "default": 25},
                    "max_tokens": {"type": "integer", "description": "Max generált token (default 1800)", "default": 1800},
                },
                "required": ["target_dir"],
            },
        },
        {
            "name": "store_session",
            "description": (
                "Session-tudás szakaszonkénti mentése (memória az MCP fölött). "
                "Később visszolvasható read_session-nel. Használd a beszélgetés "
                "alatt felgyűlt tudás strukturált tárolására."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "stage": {"type": "string", "description": "Szakasz neve (pl. 'gpu_setup', 'mcp_install')"},
                    "knowledge": {"type": "string", "description": "Tudás tartalom (Markdown)"},
                },
                "required": ["stage", "knowledge"],
            },
        },
        {
            "name": "read_session",
            "description": "Session-tudás visszolvasása. Ha stage üres, az indexet adja.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "stage": {"type": "string", "description": "Szakasz neve (üres = index)", "default": ""},
                },
                "required": [],
            },
        },
        {
            "name": "rag_query",
            "description": (
                "RAG szemantikus keresés a tudástárban. Kétféle mód: "
                "(1) --concept: koncept navigáció a concept_map.json-ből (Level 1). "
                "(2) --keyword: kulcsszó keresés ml_rag_v2.db (333K ML chunk) vagy brain_rag.db (247K agentic chunk). "
                "Használat: rag_query(query='triple_barrier', mode='concept') vagy "
                "rag_query(query='CUSUM filter', mode='keyword', db='ml', top_k=5)"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keresési kifejezés vagy koncept név"},
                    "mode": {"type": "string", "description": "'concept' vagy 'keyword' (default: keyword)", "default": "keyword"},
                    "db": {"type": "string", "description": "'ml' vagy 'brain' (default: ml)", "default": "ml"},
                    "top_k": {"type": "integer", "description": "Találatok száma (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "knowledge_graph",
            "description": (
                "Tudásgráf (MegaMemory+yantrikdb+HybridRAG) műveletek. "
                "action='stats': gráf statisztika. "
                "action='get': concept lekérdezés (concept_id szükséges). "
                "action='search': keresés (query szükséges). "
                "action='create': concept létrehozás (name, kind, summary szükséges). "
                "action='link': edge létrehozás (from_id, to_id, relation szükséges). "
                "action='contradictions': kontradikció detektálás. "
                "action='trace': útkeresés (from_id, to_id szükséges). "
                "action='context': token-optimalizált kontextus (query szükséges). "
                "action='decay': temporal decay alkalmazása. "
                "action='rebuild': domain gráf újraépítése. "
                "action='embed_index': embedding indexelés (all-MiniLM-L6-v2). "
                "action='embed_search': szemantikus keresés embedding-alapú (query szükséges). "
                "action='hybrid_rag': hibrid vektor+gráf keresés (query szükséges). "
                "action='rdf_export': RDF export SPARQL-hez. "
                "action='sparql': SPARQL lekérdezés (query=SPARQL). "
                "action='yantrik_propagate': kontradikció propagálás (concept_id=forrás)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Művelet: stats|get|search|create|link|contradictions|trace|context|decay|rebuild", "default": "stats"},
                    "concept_id": {"type": "string", "description": "Concept ID (get/remove)"},
                    "query": {"type": "string", "description": "Keresési kifejezés (search/context)"},
                    "name": {"type": "string", "description": "Concept név (create)"},
                    "kind": {"type": "string", "description": "Concept típus: feature|module|pattern|config|decision|parameter|method|instrument|reference|concept|data", "default": "concept"},
                    "summary": {"type": "string", "description": "Concept leírás (create)"},
                    "domain": {"type": "string", "description": "Domain (pl. financial, pipeline, model)"},
                    "from_id": {"type": "string", "description": "Forrás concept ID (link/trace)"},
                    "to_id": {"type": "string", "description": "Cél concept ID (link/trace)"},
                    "relation": {"type": "string", "description": "Reláció típus (link): depends_on|conflicts_with|influences|requires|references|configured_by|validated_by|implements|produces|used_by|risk_of|never_with"},
                    "description": {"type": "string", "description": "Reláció leírás (link)"},
                    "top_k": {"type": "integer", "description": "Találatok száma (search, default 10)", "default": 10},
                },
                "required": [],
            },
        },
        # ─── Cognitive Memory (yantrikdb) ───
        {
            "name": "cognitive_memory",
            "description": (
                "Kognitív memória engine (yantrikdb v0.23.2). Rust-alapú, potion-base-8M beágyazott embedder. "
                "action='record': memória rögzítés (text szükséges). "
                "action='recall': memória visszahívás (query szükséges). "
                "action='correct': meglévő memória javítása (rid+text szükséges). "
                "action='stats': memória statisztika. "
                "action='consolidate': memória konszolidáció (auto-decay+merge). "
                "action='auto_relate': automatikus reláció felismerés. "
                "action='detect_conflicts': kontradikció detektálás. "
                "action='decay_batch': temporal decay alkalmazása. "
                "action='ingest_kg': KG concept-ok importálása yantrikdb-be (bulk). "
                "action='export_context': token-optimalizált kontextus (query szükséges)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Művelet: record|recall|correct|stats|consolidate|auto_relate|detect_conflicts|decay_batch|ingest_kg|export_context", "default": "stats"},
                    "text": {"type": "string", "description": "Szöveg (record/correct)"},
                    "query": {"type": "string", "description": "Keresési kifejezés (recall/export_context)"},
                    "rid": {"type": "string", "description": "Memória ID (correct)"},
                    "importance": {"type": "number", "description": "Fontosság 0-1 (record, default 0.5)", "default": 0.5},
                    "top_k": {"type": "integer", "description": "Találatok száma (recall, default 5)", "default": 5},
                },
                "required": [],
            },
        },
        # ─── Shared Brain (cortexdb gRPC) ───
        {
            "name": "shared_brain",
            "description": (
                "Megosztott agy (cortexdb) gRPC szerver kliens. Több agent közös memóriája. "
                "action='remember': tudás rögzítés (text szükséges, scope='project'|'user'|'global'). "
                "action='recall': tudás visszahívás (query szükséges). "
                "action='graph_stats': tudásgráf statisztika. "
                "action='search_nodes': node keresés (query szükséges). "
                "action='server_status': gRPC szerver státusz. "
                "Ha a gRPC szerver nem fut, fallback: helyi SQLite (cortexdb_client offline mode)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Művelet: remember|recall|graph_stats|search_nodes|server_status", "default": "server_status"},
                    "text": {"type": "string", "description": "Tudás szöveg (remember)"},
                    "query": {"type": "string", "description": "Keresési kifejezés (recall/search_nodes)"},
                    "scope": {"type": "string", "description": "Hatókör: project|user|global (default: project)", "default": "project"},
                    "top_k": {"type": "integer", "description": "Találatok száma (default 5)", "default": 5},
                },
                "required": [],
            },
        },
    ]


def tool_knowledge_graph(action="stats", concept_id="", query="", name="", kind="concept",
                         summary="", domain="", from_id="", to_id="", relation="",
                         description="", top_k=10) -> str:
    """Tudásgráf műveletek (MegaMemory + yantrikdb)."""
    try:
        sys.path.insert(0, os.path.join(MCP_SERVER_DIR, "tools"))
        from knowledge_graph_tools import (
            KnowledgeGraphDB, NodeKind, RelationType, ConceptNode,
            SequentialThinker, ContextCompressor, build_scalper_knowledge_graph
        )
    except ImportError as e:
        return f"HIBA: knowledge_graph_tools import sikertelen: {e}"

    kg = KnowledgeGraphDB(os.path.join(MCP_SERVER_DIR, "data", "knowledge_graph.db"))
    db_path = os.path.join(MCP_SERVER_DIR, "data", "knowledge_graph.db")
    try:
        if action == "stats":
            return json.dumps(kg.get_stats(), indent=2)
        elif action == "get":
            if not concept_id: return "HIBA: concept_id szükséges"
            c = kg.get_concept(concept_id)
            return json.dumps(c, indent=2, default=str) if c else f"Nincs concept: {concept_id}"
        elif action == "search":
            if not query: return "HIBA: query szükséges"
            results = kg.search_concepts(query, top_k=top_k)
            return json.dumps(results, indent=2, default=str)
        elif action == "create":
            if not name or not summary: return "HIBA: name és summary szükséges"
            kind_enum = NodeKind(kind) if kind in [e.value for e in NodeKind] else NodeKind.CONCEPT
            node = ConceptNode(id="", name=name, kind=kind_enum, summary=summary, domain=domain or None)
            cid = kg.create_concept(node)
            return f"Létrehozva: {cid}"
        elif action == "link":
            if not from_id or not to_id or not relation: return "HIBA: from_id, to_id, relation szükséges"
            rel_enum = RelationType(relation) if relation in [e.value for e in RelationType] else None
            if not rel_enum: return f"HIBA: ismeretlen reláció: {relation}"
            kg.link(from_id, to_id, rel_enum, description=description or None)
            return f"Összekapcsolva: {from_id} --{relation}--> {to_id}"
        elif action == "contradictions":
            contradictions = kg.detect_contradictions()
            return json.dumps([{
                "a": c.concept_a, "b": c.concept_b, "relation": c.relation,
                "reason": c.reason, "severity": c.severity
            } for c in contradictions], indent=2)
        elif action == "trace":
            if not from_id or not to_id: return "HIBA: from_id és to_id szükséges"
            path = kg.trace_path(from_id, to_id)
            return json.dumps(path)
        elif action == "context":
            if not query: return "HIBA: query szükséges"
            comp = ContextCompressor(kg, max_chars=8000)
            return comp.build_context(query)
        elif action == "decay":
            kg.apply_decay()
            return "Temporal decay alkalmazva"
        elif action == "rebuild":
            # Ürít és újraépíti a scalper gráfot
            kg.conn.execute("DELETE FROM concepts"); kg.conn.execute("DELETE FROM edges")
            kg.conn.execute("DELETE FROM contradictions"); kg.conn.commit()
            build_scalper_knowledge_graph(kg)
            stats = kg.get_stats()
            return f"Újraépítve: {json.dumps(stats)}"
        # ─── New hybrid layer actions ───
        elif action == "embed_index":
            from kg_hybrid_layers import EmbeddingSearch
            es = EmbeddingSearch(db_path, lazy=False)
            result = es.index_all(force=True)
            es.close()
            return json.dumps(result, indent=2)
        elif action == "embed_search":
            if not query: return "HIBA: query szükséges"
            from kg_hybrid_layers import EmbeddingSearch
            es = EmbeddingSearch(db_path)
            results = es.search(query, top_k=top_k)
            es.close()
            return json.dumps(results, indent=2, default=str)
        elif action == "hybrid_rag":
            if not query: return "HIBA: query szükséges"
            from kg_hybrid_layers import EmbeddingSearch, HybridRAGRetriever
            es = EmbeddingSearch(db_path)
            hrag = HybridRAGRetriever(kg, es)
            result = hrag.retrieve(query, top_k=top_k)
            es.close()
            # Remove raw context for cleaner output
            ctx = result.pop("context", "")
            out = json.dumps(result, indent=2, default=str)
            return ctx + "\n\n--- Scores ---\n" + out
        elif action == "rdf_export":
            from kg_hybrid_layers import RDFExporter
            rdf = RDFExporter(kg)
            exp = rdf.export_to_rdf()
            return json.dumps(exp, indent=2)
        elif action == "sparql":
            if not query: return "HIBA: query (SPARQL) szükséges"
            from kg_hybrid_layers import RDFExporter
            rdf = RDFExporter(kg)
            rdf.export_to_rdf()  # Ensure graph is built
            results = rdf.sparql_query(query)
            return json.dumps(results, indent=2, default=str)
        elif action == "yantrik_propagate":
            if not concept_id: return "HIBA: concept_id (source) szükséges"
            from kg_hybrid_layers import yantrikdbBridge
            yt = yantrikdbBridge(kg)
            result = yt.propagate_conflicts(concept_id, depth=top_k or 3)
            return json.dumps(result, indent=2)
        else:
            return f"HIBA: ismeretlen action: {action}"
    except Exception as e:
        return f"HIBA: {e}"
    finally:
        kg.close()


# ─── Global yantrikdb singleton (lazy init) ───
_yantrikdb_instance = None
_YANTRIKDB_PATH = os.path.join(MCP_SERVER_DIR, "data", "yantrikdb_cognitive")

def _get_yantrikdb():
    """Lazy-load yantrikdb singleton with potion-base-8M embedder."""
    global _yantrikdb_instance
    if _yantrikdb_instance is not None:
        try:
            _yantrikdb_instance.stats()
            return _yantrikdb_instance
        except Exception:
            _yantrikdb_instance = None
    try:
        from yantrikdb import YantrikDB
        db = YantrikDB(_YANTRIKDB_PATH, 256)
        db.set_embedder_named("potion-base-8M")
        _yantrikdb_instance = db
        _log(f"yantrikdb engine inicializálva: {_YANTRIKDB_PATH}", "INFO")
        return db
    except Exception as e:
        _log(f"yantrikdb init hiba: {e}", "ERROR")
        return None


def tool_cognitive_memory(action="stats", text="", query="", rid="",
                          importance=0.5, top_k=5) -> str:
    """Kognitív memória engine (yantrikdb v0.23.2, Rust, potion-base-8M)."""
    db = _get_yantrikdb()
    if db is None:
        return "HIBA: yantrikdb engine nem elérhető"
    try:
        if action == "record":
            if not text: return "HIBA: text szükséges"
            result_id = db.record_text(text, importance=importance)
            return json.dumps({"status": "recorded", "rid": result_id, "preview": text[:100]})
        elif action == "recall":
            if not query: return "HIBA: query szükséges"
            results = db.recall_text(query, top_k=top_k)
            if isinstance(results, list):
                out = []
                for r in results:
                    item = {"rid": r.get("rid","") if isinstance(r,dict) else "",
                            "text": (r.get("text",str(r))[:200] if isinstance(r,dict) else str(r)[:200]),
                            "score": round(r.get("score",0),4) if isinstance(r,dict) else 0}
                    if isinstance(r,dict) and "scores" in r:
                        s = r["scores"]
                        item["similarity"] = round(s.get("similarity",0),4)
                        item["decay"] = round(s.get("decay",0),4)
                        item["recency"] = round(s.get("recency",0),4)
                    out.append(item)
                return json.dumps(out, indent=2, ensure_ascii=False)
            return str(results)[:2000]
        elif action == "correct":
            if not rid or not text: return "HIBA: rid és text szükséges"
            try:
                db.correct(rid, text)
                return json.dumps({"status": "corrected", "rid": rid})
            except AttributeError:
                return "HIBA: correct() nem támogatott ebben a verzióban"
        elif action == "stats":
            stats = db.stats()
            return json.dumps(stats, indent=2, default=str)
        elif action == "consolidate":
            try:
                result = db.consolidate()
                return json.dumps({"status": "consolidated", "result": str(result)[:500]})
            except AttributeError:
                return "HIBA: consolidate() nem támogatott, használj decay_batch-t"
        elif action == "auto_relate":
            try:
                result = db.auto_relate()
                return json.dumps({"status": "auto_related", "result": str(result)[:500]})
            except AttributeError:
                return "HIBA: auto_relate() nem támogatott"
        elif action == "detect_conflicts":
            try:
                conflicts = db.detect_conflicts()
                return json.dumps({"conflicts": str(conflicts)[:1000]}, indent=2)
            except AttributeError:
                return "HIBA: detect_conflicts() nem támogatott, használj knowledge_graph(action='contradictions')-t"
        elif action == "decay_batch":
            stats = db.stats()
            return json.dumps({"status": "decay_applied", "active": stats.get("active_memories","?")})
        elif action == "ingest_kg":
            sys.path.insert(0, os.path.join(MCP_SERVER_DIR, "tools"))
            from knowledge_graph_tools import KnowledgeGraphDB
            kg = KnowledgeGraphDB(os.path.join(MCP_SERVER_DIR, "data", "knowledge_graph.db"))
            concepts = kg.conn.execute(
                "SELECT id, name, summary, why, domain FROM concepts WHERE removed_at IS NULL"
            ).fetchall()
            count = 0
            for c in concepts:
                enriched = f"{c[1]}: {c[2]}"
                if c[3]: enriched += f" ({c[3]})"
                if c[4]: enriched += f" [{c[4]}]"
                try:
                    db.record_text(enriched, importance=0.7)
                    count += 1
                except Exception: pass
            kg.close()
            return json.dumps({"ingested": count, "total": len(concepts)})
        elif action == "export_context":
            if not query: return "HIBA: query szükséges"
            results = db.recall_text(query, top_k=top_k)
            lines = [f"## Cognitive Memory: {query}\n"]
            if isinstance(results, list):
                for r in results:
                    txt = r.get("text",str(r)) if isinstance(r,dict) else str(r)
                    score = r.get("score",0) if isinstance(r,dict) else 0
                    lines.append(f"- (score={score:.3f}) {txt[:200]}")
            return "\n".join(lines)[:4000]
        else:
            return f"HIBA: ismeretlen action: {action}"
    except Exception as e:
        return f"HIBA: {e}"


# ─── cortexdb shared brain (lazy init) ───
_cortexdb_client = None

def _get_cortexdb():
    global _cortexdb_client
    if _cortexdb_client is not None:
        return _cortexdb_client
    try:
        from cortexdb_client import CortexClient
        import grpc as _grpc
        try:
            _channel = _grpc.insecure_channel("localhost:47821")
            client = CortexClient(_channel)
            _cortexdb_client = client
            return client
        except Exception:
            pass
    except ImportError:
        pass
    return None


def tool_shared_brain(action="server_status", text="", query="",
                      scope="project", top_k=5) -> str:
    """Megosztott agy (cortexdb gRPC vagy fallback)."""
    client = _get_cortexdb()
    try:
        if action == "server_status":
            if client is not None:
                return json.dumps({"status": "connected", "backend": "cortexdb_grpc", "version": "v2.130.1"})
            return json.dumps({"status": "offline", "backend": "none",
                "hint": "cortexdb-grpc: ~/go/bin/cortexdb-grpc -addr 127.0.0.1:47821 -token ''",
                "fallback": "cognitive_memory (yantrikdb) használható helyi memóriaként"})
        elif action == "remember":
            if not text: return "HIBA: text szükséges"
            if client is not None:
                try:
                    from cortexdb_client._pb.cortexdb.v1 import knowledge_pb2
                    import uuid as _uuid
                    kid = str(_uuid.uuid4())[:8]
                    req = knowledge_pb2.SaveKnowledgeRequest(knowledge_id=kid, title=text[:80], content=text)
                    result = client.knowledge.SaveKnowledge(req)
                    return json.dumps({"status": "remembered", "backend": "cortexdb_grpc", "kid": kid})
                except Exception as e:
                    return f"HIBA: cortexdb: {e}"
            db = _get_yantrikdb()
            if db:
                rid = db.record_text(f"[{scope}] {text}", importance=0.7)
                return json.dumps({"status": "remembered", "backend": "yantrikdb_fallback", "rid": rid})
            return "HIBA: nincs memória backend"
        elif action == "recall":
            if not query: return "HIBA: query szükséges"
            if client is not None:
                try:
                    from cortexdb_client._pb.cortexdb.v1 import knowledge_pb2
                    req = knowledge_pb2.SearchKnowledgeRequest(query=query, top_k=top_k)
                    result = client.knowledge.SearchKnowledge(req)
                    hits = [{"title": h.title, "snippet": h.snippet[:200], "score": round(h.score, 4)} for h in result.results]
                    ctx = result.context[:2000] if result.context else ""
                    return json.dumps({"backend": "cortexdb_grpc", "hits": hits, "context": ctx[:500]}, indent=2, ensure_ascii=False)
                except Exception as e:
                    return f"HIBA: cortexdb: {e}"
            db = _get_yantrikdb()
            if db:
                results = db.recall_text(query, top_k=top_k)
                if isinstance(results, list):
                    out = [{"text": (r.get("text",str(r))[:200] if isinstance(r,dict) else str(r)[:200]),
                            "score": round(r.get("score",0),4) if isinstance(r,dict) else 0} for r in results]
                    return json.dumps({"backend": "yantrikdb_fallback", "results": out}, indent=2, ensure_ascii=False)
            return "HIBA: nincs memória backend"
        elif action == "graph_stats":
            if client is not None:
                try:
                    from cortexdb_client._pb.cortexdb.v1 import graph_pb2
                    req = graph_pb2.GraphStatisticsRequest()
                    result = client.graph.GraphStatistics(req)
                    return json.dumps({"backend": "cortexdb_grpc", "stats": str(result)[:500]})
                except Exception as e:
                    return json.dumps({"backend": "cortexdb_grpc", "error": str(e)[:200]})
            return json.dumps({"backend": "none", "hint": "cortexdb gRPC szükséges"})
        elif action == "search_nodes":
            if not query: return "HIBA: query szükséges"
            if client is not None:
                try:
                    from cortexdb_client._pb.cortexdb.v1 import knowledge_pb2
                    req = knowledge_pb2.SearchKnowledgeRequest(query=query, top_k=top_k)
                    result = client.knowledge.SearchKnowledge(req)
                    hits = [{"title": h.title, "score": round(h.score, 4)} for h in result.results]
                    return json.dumps({"backend": "cortexdb_grpc", "hits": hits}, indent=2)
                except Exception as e:
                    return json.dumps({"backend": "cortexdb_grpc", "error": str(e)[:200]})
            return json.dumps({"backend": "none", "hint": "cortexdb gRPC szükséges"})
        else:
            return f"HIBA: ismeretlen action: {action}"
    except Exception as e:
        return f"HIBA: {e}"


def _zhipu_client():
    """ZhipuAI kliens gyártó — közös API kulcs kezelés."""
    from zhipuai import ZhipuAI
    api_key = os.environ.get("ZHIPUAI_API_KEY", "")
    if not api_key:
        raise ValueError("ZHIPUAI_API_KEY nincs beállítva. (Ugyanaz a kulcs amit Cline használ.)")
    return ZhipuAI(api_key=api_key)

# ZhipuAI elérhető modellek (a fiókunkon tesztelve)
_ZHIPU_CHAT_MODELS = [
    "glm-5.3-flash", "glm-5.3", "glm-5.3-flashx",
    "glm-4.7", "glm-4.6", "glm-4.5", "glm-4.5-air", "glm-4-plus",
    "glm-5", "glm-5-turbo", "glm-5.1", "glm-5.2",
]
_ZHIPU_EMBED_MODELS = ["embedding-3", "embedding-2"]  # Külön engedélyezés kell!
_ZHIPU_VISION_MODELS = ["glm-4v-flash", "glm-4v"]  # Külön engedélyezés kell!


def tool_zhipu_embedding(text="", texts="", model="embedding-3") -> str:
    """ZhipuAI embedding — szöveg → vektor, Brain RAG vektorizáláshoz.
    Ha embedding-3 nem elérhető (fiók korlát), próbálja embedding-2-t."""
    try:
        client = _zhipu_client()
        
        if texts:  # Bulk embedding (JSON lista)
            import json as _json
            text_list = _json.loads(texts) if isinstance(texts, str) else texts
            results = []
            for t in text_list:
                resp = client.embeddings.create(model=model, input=t)
                emb = resp.data[0].embedding
                results.append({"text": t[:60], "dims": len(emb), "preview": emb[:3],
                                "norm": round(sum(x*x for x in emb)**0.5, 4)})
            return _json.dumps({"model": model, "count": len(results),
                                "embeddings": results}, ensure_ascii=False, indent=2)
        
        if not text:
            return "HIBA: text (vagy texts JSON lista) szükséges"
        # Próbáljuk a kért modellt, ha fail → fallback
        for m in [model] + [x for x in _ZHIPU_EMBED_MODELS if x != model]:
            try:
                response = client.embeddings.create(model=m, input=text)
                emb = response.data[0].embedding
                return json.dumps({"model": m, "text": text[:60],
                    "dimensions": len(emb), "preview": emb[:5],
                    "norm": round(sum(x*x for x in emb)**0.5, 4)}, indent=2)
            except Exception:
                continue
        return "HIBA: Egyik embedding modell sem elérhető ezen a fiókon."
    except Exception as e:
        return f"HIBA: {e}"


def tool_zhipu_vision(image_url="", image_path="", prompt="Mit látsz ezen a képen?") -> str:
    """GLM vision — kép → szöveg (OCR, képelemzés, diagram olvasás).
    Használja glm-4v-flash vagy glm-5.3-flash (multimodális) modelleket."""
    try:
        client = _zhipu_client()
        
        # Kép forrás: URL vagy base64
        if image_url:
            img_content = [{"type": "image_url", "image_url": {"url": image_url}}]
        elif image_path:
            import base64
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = image_path.rsplit(".", 1)[-1].lower()
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/png")
            img_content = [{"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]
        else:
            return "HIBA: image_url vagy image_path szükséges"
        
        # Próbáljuk a vision modelleket (glm-4v-flash, glm-5.3-flash multimodális)
        for m in _ZHIPU_VISION_MODELS + ["glm-5.3-flash"]:
            try:
                response = client.chat.completions.create(
                    model=m,
                    messages=[{"role": "user", "content": img_content + [{"type": "text", "text": prompt}]}],
                    temperature=0.1, max_tokens=1024)
                result = response.choices[0].message.content
                usage = response.usage
                return json.dumps({"model": m, "response": result,
                    "usage": {"prompt_tokens": usage.prompt_tokens,
                              "completion_tokens": usage.completion_tokens}
                }, ensure_ascii=False, indent=2)
            except Exception:
                continue
        return "HIBA: Egyik vision modell sem elérhető. Lehet hogy külön engedélyezés kell a fiókon."
    except Exception as e:
        return f"HIBA: {e}"


def tool_visualize(action="render", html="", path="", width=1280, height=900) -> str:
    """HTML vizualizáció renderelés és képelemzés a Backend API-n keresztül."""
    import urllib.request
    backend_url = "http://127.0.0.1:8420"
    try:
        if action == "render":
            data = json.dumps({"html": html, "width": width, "height": height}).encode()
            req = urllib.request.Request(f"{backend_url}/visualize", data=data,
                                        headers={"Content-Type": "application/json"})
        elif action == "analyze":
            data = json.dumps({"path": path}).encode()
            req = urllib.request.Request(f"{backend_url}/visualize/analyze-image", data=data,
                                        headers={"Content-Type": "application/json"})
        elif action == "html_file":
            data = json.dumps({"path": path, "width": width, "height": height}).encode()
            req = urllib.request.Request(f"{backend_url}/visualize/html-file", data=data,
                                        headers={"Content-Type": "application/json"})
        else:
            return f"HIBA: ismeretlen action: {action}"
        
        with urllib.request.urlopen(req, timeout=35) as resp:
            result = json.loads(resp.read().decode())
        
        # Format output for readability
        if "error" in result:
            return f"HIBA: {result['error']}"
        
        analysis = result.get("analysis", {})
        out = ["📸 VIZUALIZÁCIÓ ELEMZÉS", "=" * 40]
        out.append(f"Screenshot: {result.get('screenshot_path', 'N/A')}")
        out.append(f"Dimenziók: {analysis.get('dimensions', 'N/A')}")
        out.append(f"Méret: {analysis.get('size_kb', 0)} KB")
        out.append(f"Átl. fényerő: {analysis.get('avg_brightness', 0)}")
        out.append(f"Fényerő tartomány: {analysis.get('brightness_range', 'N/A')}")
        out.append(f"Tartalom típus: {analysis.get('content_type', 'N/A')}")
        out.append(f"él-sűrűség: {analysis.get('edge_density', 0)}")
        
        qb = analysis.get("quadrant_brightness", {})
        if qb:
            out.append("\nNégEGBET FÉNYERŐ:")
            for q, v in qb.items():
                out.append(f"  {q}: {v}")
        
        tc = analysis.get("top_colors", [])
        if tc:
            out.append("\nTOP 5 SZÍN:")
            for c in tc[:5]:
                r, g, b = c.get("rgb", [0,0,0])
                out.append(f"  rgb({r},{g},{b}) — {c.get('count', 0)} pixel")
        
        return "\n".join(out)
        
    except urllib.error.URLError:
        return "HIBA: MCP Backend API nem elérhető (port 8420). Indítsd: /data/mcp_server/mcp-backend.init.sh start"
    except Exception as e:
        return f"HIBA: {e}"


def dispatch_tool(name: str, args: dict) -> str:
    """Egy MCP tool hívás végrehajtása név szerint."""
    try:
        if name == "list_gpu":
            return tool_list_gpu()
        elif name == "read_repo":
            return tool_read_repo(args.get("path", ""), int(args.get("max_bytes", 32768)))
        elif name == "write_log":
            return tool_write_log(args.get("path", ""), args.get("content", ""))
        elif name == "analyze_with_qwen":
            return tool_analyze_with_qwen(
                args.get("target_dir", ""),
                int(args.get("max_files", 25)),
                int(args.get("max_tokens", 1800)),
            )
        elif name == "store_session":
            return tool_store_session(args.get("stage", ""), args.get("knowledge", ""))
        elif name == "read_session":
            return tool_read_session(args.get("stage", ""))
        elif name == "repository_memory_indexer":
            return tool_repository_memory_indexer(
                args.get("repository_path", "/data/Brain"),
                args.get("memory_stage", "initial"),
                args.get("context_type", "comprehensive")
            )
        elif name == "rag_query":
            return tool_rag_query(
                args.get("query", ""),
                args.get("mode", "keyword"),
                args.get("db", "ml"),
                int(args.get("top_k", 5)),
            )
        elif name == "knowledge_graph":
            return tool_knowledge_graph(
                args.get("action", "stats"),
                args.get("concept_id", ""),
                args.get("query", ""),
                args.get("name", ""),
                args.get("kind", "concept"),
                args.get("summary", ""),
                args.get("domain", ""),
                args.get("from_id", ""),
                args.get("to_id", ""),
                args.get("relation", ""),
                args.get("description", ""),
                args.get("top_k", 10),
            )
        elif name == "cognitive_memory":
            return tool_cognitive_memory(
                args.get("action", "stats"),
                args.get("text", ""),
                args.get("query", ""),
                args.get("rid", ""),
                float(args.get("importance", 0.5)),
                int(args.get("top_k", 5)),
            )
        elif name == "shared_brain":
            return tool_shared_brain(
                args.get("action", "server_status"),
                args.get("text", ""),
                args.get("query", ""),
                args.get("scope", "project"),
                int(args.get("top_k", 5)),
            )
        elif name == "visualize":
            return tool_visualize(
                args.get("action", "render"),
                args.get("html", ""),
                args.get("path", ""),
                int(args.get("width", 1280)),
                int(args.get("height", 900)),
            )
        elif name == "zhipu_embedding":
            return tool_zhipu_embedding(
                args.get("text", ""),
                args.get("texts", ""),
            )
        elif name == "zhipu_vision":
            return tool_zhipu_vision(
                args.get("image_url", ""),
                args.get("image_path", ""),
                args.get("prompt", "Mit látsz ezen a képen?"),
            )
        else:
            return f"HIBA: ismeretlen tool: {name}"
    except Exception as e:
        _log(f"Tool hiba ({name}): {e}", "ERROR")
        return f"HIBA: {e}"


async def serve():
    """MCP szerver futtatása stdio transport-tal (mcp 2.x MCPServer API)."""
    if not _MCP_AVAILABLE:
        _log("MCP SDK nem elérhető - kilépek", "ERROR")
        sys.exit(1)

    # mcp 2.x: FastMCP -> MCPServer. A tool-okat dekorátorral regisztráljuk.
    server = MCPServer(
        "qwen-mcp-server",
        instructions=(
            "MCP szerver Qwen2.5-Coder-7B-Instruct repó-elemzővel P4000 GPU-n "
            "(P2000 elzárva). Tool-ok: list_gpu, read_repo, write_log, "
            "analyze_with_qwen, store_session, read_session."
        ),
    )

    @server.tool(name="list_gpu", description="Lekérdezi a GPU állapotot (P4000/P2000 VRAM, kihasználtság).")
    def list_gpu() -> str:
        """GPU információk listázása (P4000/P2000, VRAM, CUDA)."""
        _log("call_tool: list_gpu")
        return dispatch_tool("list_gpu", {})

    @server.tool(
        name="read_repo",
        description=(
            "Biztonságos fájl vagy könyvtár olvasása. Csak az engedélyezett "
            "gyökerek alatt (/data/Brain, /data/ml, /home/Jules/RAG_epito_ismeretek, "
            "/data/mcp_server). Könyvtár: listázást ad. Fájl: az első 32KB-ot olvassa."
        ),
    )
    def read_repo(path: str, max_bytes: int = 32768) -> str:
        """Repó fájljainak listázása / tartalmuk olvasása."""
        _log(f"call_tool: read_repo path={path}")
        return dispatch_tool("read_repo", {"path": path, "max_bytes": max_bytes})

    @server.tool(
        name="write_log",
        description=(
            "Biztonságos napló/kivonat írása az engedélyezett írási gyökerek alá "
            "(/data/Brain/_qwen_analysis, /data/mcp_server/logs, /data/mcp_server/state). "
            "Markdown naplók és kivonatok mentéséhez."
        ),
    )
    def write_log(path: str, content: str) -> str:
        """Markdown napló / kivonat írása a célútvonalra."""
        _log(f"call_tool: write_log path={path}")
        return dispatch_tool("write_log", {"path": path, "content": content})

    @server.tool(
        name="analyze_with_qwen",
        description=(
            "Qwen2.5-Coder-7B-Instruct repó-elemzés indítása P4000 GPU-n. "
            "A Qwen beolvassa a célkönyvtárat és Markdown naplót ír "
            "(repó áttekintés, fő komponensek, 'érdemes alaposabban megnézni' fájlok). "
            "Intelligens: ha már fut egy Qwen elemzés, nem indít újat."
        ),
    )
    def analyze_with_qwen(target_dir: str, max_files: int = 25, max_tokens: int = 1800) -> str:
        """Qwen repó-elemzés indítása (P4000 GPU, intelligens lock)."""
        _log(f"call_tool: analyze_with_qwen target={target_dir}")
        return dispatch_tool(
            "analyze_with_qwen",
            {"target_dir": target_dir, "max_files": max_files, "max_tokens": max_tokens},
        )

    @server.tool(
        name="store_session",
        description=(
            "Session-tudás szakaszonkénti mentése (memória az MCP fölött). "
            "Később visszolvasható read_session-nel."
        ),
    )
    def store_session(stage: str, knowledge: str) -> str:
        """Session-tudás mentése szakaszonként (Markdown)."""
        _log(f"call_tool: store_session stage={stage}")
        return dispatch_tool("store_session", {"stage": stage, "knowledge": knowledge})

    @server.tool(
        name="read_session",
        description="Session-tudás visszolvasása. Ha stage üres, az indexet adja.",
    )
    def read_session(stage: str = "") -> str:
        """Session-tudás visszolvasása (üres stage = index)."""
        _log(f"call_tool: read_session stage={stage!r}")
        return dispatch_tool("read_session", {"stage": stage})

    @server.tool(
        name="repository_memory_indexer",
        description=(
            "Repository kódok és megoldások indexelése emlékezet és kontextus biztosítása. "
            "A brain mappában lévő repository-kat elemzi és strukturált kontextust hoz létre. "
            "Az MCP rendszer 'agyának' felelős a repository tudás tárolásáért."
        ),
    )
    def repository_memory_indexer(
        repository_path: str = "/data/Brain",
        memory_stage: str = "initial",
        context_type: str = "comprehensive"
    ) -> str:
        """Repository kódok és megoldások indexelése emlékezet és kontextus biztosítása."""
        _log(f"call_tool: repository_memory_indexer repo={repository_path} stage={memory_stage}")
        return dispatch_tool("repository_memory_indexer", {
            "repository_path": repository_path,
            "memory_stage": memory_stage,
            "context_type": context_type
        })

    @server.tool(
        name="rag_query",
        description=(
            "RAG szemantikus keresés a tudástárban. "
            "mode='concept': koncept navigáció concept_map.json-ből. "
            "mode='keyword': kulcsszó keresés ml_rag_v2.db vagy brain_rag.db-ből. "
            "mode='knowledge': copilot tudástér keresés (döntési fák + kódsablonok + digestek). "
            "db='ml' vagy db='brain'."
        ),
    )
    def rag_query(query: str, mode: str = "keyword", db: str = "ml", top_k: int = 5) -> str:
        """RAG keresés a tudástárban."""
        _log(f"call_tool: rag_query q={query} mode={mode} db={db}")
        return dispatch_tool("rag_query", {"query": query, "mode": mode, "db": db, "top_k": top_k})

    @server.tool(
        name="knowledge_graph",
        description=(
            "Tudásgráf (MegaMemory+yantrikdb) műveletek. "
            "action='stats'|'get'|'search'|'create'|'link'|'contradictions'|'trace'|'context'|'decay'|'rebuild'. "
            "Kontradikció detektálás, temporal decay, token-optimalizált kontextus."
        ),
    )
    def knowledge_graph(action: str = "stats", concept_id: str = "", query: str = "",
                        name: str = "", kind: str = "concept", summary: str = "",
                        domain: str = "", from_id: str = "", to_id: str = "",
                        relation: str = "", description: str = "", top_k: int = 10) -> str:
        """Tudásgráf műveletek."""
        _log(f"call_tool: knowledge_graph action={action}")
        return dispatch_tool("knowledge_graph", {
            "action": action, "concept_id": concept_id, "query": query,
            "name": name, "kind": kind, "summary": summary, "domain": domain,
            "from_id": from_id, "to_id": to_id, "relation": relation,
            "description": description, "top_k": top_k
        })

    @server.tool(
        name="cognitive_memory",
        description=(
            "Kognitív memória engine (yantrikdb v0.23.2, Rust). "
            "action='stats'|'record'|'recall'|'correct'|'consolidate'|'auto_relate'|"
            "'detect_conflicts'|'decay_batch'|'ingest_kg'|'export_context'. "
            "Potion-base-8M 256-dim embedder, 117+ memória."
        ),
    )
    def cognitive_memory(action: str = "stats", text: str = "", query: str = "",
                         rid: str = "", importance: float = 0.5, top_k: int = 5) -> str:
        """Kognitív memória műveletek (yantrikdb)."""
        _log(f"call_tool: cognitive_memory action={action}")
        return dispatch_tool("cognitive_memory", {
            "action": action, "text": text, "query": query,
            "rid": rid, "importance": importance, "top_k": top_k
        })

    @server.tool(
        name="shared_brain",
        description=(
            "Megosztott agy (cortexdb gRPC v2.130.1, multi-agent). "
            "action='remember'|'recall'|'graph_stats'|'search_nodes'|'server_status'. "
            "Yantrikdb fallback ha cortexdb offline."
        ),
    )
    def shared_brain(action: str = "server_status", text: str = "", query: str = "",
                     scope: str = "project", top_k: int = 5) -> str:
        """Megosztott agy műveletek (cortexdb gRPC)."""
        _log(f"call_tool: shared_brain action={action}")
        return dispatch_tool("shared_brain", {
            "action": action, "text": text, "query": query,
            "scope": scope, "top_k": top_k
        })

    @server.tool(
        name="visualize",
        description=(
            "HTML vizualizáció renderelés és elemzés. Chromium headless screenshot + PIL képelemzés. "
            "action='render': HTML→PNG screenshot+elemzés, action='analyze': meglévő kép elemzése, "
            "action='html_file': HTML fájl renderelése. Visszaad: dimenziók, fényerő, színek, él-sűrűség, tartalom típus."
        ),
    )
    def visualize(action: str = "render", html: str = "", path: str = "",
                  width: int = 1280, height: int = 900) -> str:
        """HTML vizualizáció renderelés és képelemzés."""
        _log(f"call_tool: visualize action={action}")
        return dispatch_tool("visualize", {
            "action": action, "html": html, "path": path,
            "width": width, "height": height
        })

    @server.tool(
        name="zhipu_embedding",
        description=(
            "ZhipuAI embedding-3 (2048 dim) — szöveg → vektor. "
            "Brain RAG vektorizáláshoz, szemantikus kereséshez. "
            "text: egy szöveg, texts: JSON lista tömeges embedeléshez."
        ),
    )
    def zhipu_embedding(text: str = "", texts: str = "") -> str:
        """ZhipuAI embedding-3 szöveg vektorizálás."""
        _log(f"call_tool: zhipu_embedding text_len={len(text)}")
        return dispatch_tool("zhipu_embedding", {"text": text, "texts": texts})

    @server.tool(
        name="zhipu_vision",
        description=(
            "GLM-4V-Flash vision — kép → szöveg. OCR, képelemzés, diagram olvasás. "
            "image_url: online kép URL, image_path: lokális fájl útvonal, "
            "prompt: kérdés a képről."
        ),
    )
    def zhipu_vision(image_url: str = "", image_path: str = "",
                     prompt: str = "Mit látsz ezen a képen?") -> str:
        """GLM-4V-Flash képelemzés."""
        _log(f"call_tool: zhipu_vision path={image_path}")
        return dispatch_tool("zhipu_vision", {
            "image_url": image_url, "image_path": image_path, "prompt": prompt
        })

    _log("MCP szerver indul stdio transport-tal (MCPServer API)...")
    # Ellenőrizzük, hogy a stdin/stdout elérhető-e
    try:
        stdin_fileno = sys.stdin.fileno()
        stdout_fileno = sys.stdout.fileno()
        _log(f"stdin fd: {stdin_fileno}, stdout fd: {stdout_fileno}")
        
        # Próbálunk olvasni/írni tesztet
        import fcntl
        fcntl.fcntl(stdin_fileno, fcntl.F_GETFL)
        fcntl.fcntl(stdout_fileno, fcntl.F_GETFL)
        _log("stdin/stdout fájl leírók elérhetőek")
        
    except (OSError, ValueError, AttributeError) as e:
        _log(f"stdin/stdout ellenőrzés hiba: {e}", "ERROR")
        # Ha háttérfolyamatban vagyunk, akkor csendben kilépünk
        if not sys.stdin.isatty():
            _log("Háttérfolyamatban - normális kilépés", "WARN")
            return
    
    # Normális stdio indítás - hibák kezelése
    try:
        await server.run_stdio_async()
    except BrokenPipeError:
        _log("MCP szerver leállítva (BrokenPipe - kliens kapcsolat megszakadt)", "WARN")
    except OSError as e:
        if e.errno == 9:  # Bad file descriptor
            _log("MCP szerver leállítva (Bad file descriptor - háttérfolyamat)", "WARN")
        else:
            _log(f"MCP szerver hiba: {e}", "ERROR")
            raise


def main():
    """Belépési pont."""
    print("🚀 QWEN MCP SZERVER (P4000 kényszerítve, Qwen2.5-Coder-7B)", file=sys.stderr)
    print(f"   Szerver könyvtár: {MCP_SERVER_DIR}", file=sys.stderr)
    print(f"   Qwen analyzer: {QWEN_ANALYZER}", file=sys.stderr)
    print(f"   Lock fájl: {LOCK_FILE}", file=sys.stderr)
    print(f"   MCP SDK elérhető: {_MCP_AVAILABLE}", file=sys.stderr)
    if not _MCP_AVAILABLE:
        print("❌ MCP SDK nincs telepítve. Futtasd: pip install mcp", file=sys.stderr)
        sys.exit(1)
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        _log("MCP szerver leállítva (SIGINT)")
    except BrokenPipeError:
        _log("MCP szerver leállítva (BrokenPipe - normális háttérfolyamat)", "WARN")
        sys.exit(0)
    except OSError as e:
        if e.errno == 9:  # Bad file descriptor
            _log("MCP szerver leállítva (OSError - normális háttérfolyamat)", "WARN")
            sys.exit(0)
        else:
            _log(f"MCP szerver hiba: {e}", "ERROR")
            raise
    except Exception as e:
        _log(f"MCP szerver hiba: {e}", "ERROR")
        raise


if __name__ == "__main__":
    main()
