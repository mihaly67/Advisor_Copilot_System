#!/usr/bin/env python3
"""
Qwen2.5-Coder-7B-Instruct GGUF (Q5_K_M) elemző wrapper - P4000 (GPU 0) kényszerítve
P2000 elzárva a CUDA_VISIBLE_DEVICES=0 környezeti változóval.

A Qwen elemzi a célkönyvtárakat és Markdown naplókat ír azokba.
Nem RAG keresést végez - csak strukturált könyvtár-elemzést és kivonatot ír.

Használat:
    source /data/mcp_server/env.sh
    python3 /data/mcp_server/tools/qwen_analyzer.py <target_dir> [--max-files N] [--max-tokens T]
"""
import os
import sys
import gc
import time
import signal
import argparse
import json
from pathlib import Path
from datetime import datetime

# GPU izoláció MÁR az env.sh-ban be van állítva, de duplán biztosítjuk
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")

# LD_LIBRARY_PATH javítása - P4000 GPU kényszerítése
ld_paths = [
    "/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib",
    "/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cublas/lib",
    "/usr/local/cuda/lib64",  # System CUDA path
]
existing_ld = os.environ.get("LD_LIBRARY_PATH", "")
for p in ld_paths:
    if p not in existing_ld:
        existing_ld = p + ":" + existing_ld
os.environ["LD_LIBRARY_PATH"] = existing_ld.rstrip(":")

# CUDA_VISIBLE_DEVICES kényszerítése P4000-re (GPU 0)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

# Konfiguráció a környezeti változókból
MODEL_PROFILE = os.environ.get("QWEN_MODEL_PROFILE", "7B")
MODEL_ID = os.environ.get("QWEN_MODEL_ID", "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
MODEL_FILE = os.environ.get("QWEN_MODEL_FILE", "qwen2.5-coder-7b-instruct-q5_k_m.gguf")
GPU_LAYERS = int(os.environ.get("QWEN_GPU_LAYERS", "-1"))
CONTEXT_SIZE = int(os.environ.get("QWEN_CONTEXT_SIZE", "8192"))
N_THREADS = int(os.environ.get("QWEN_N_THREADS", "4"))
TIMEOUT_SEC = int(os.environ.get("QWEN_TIMEOUT_SECONDS", "300"))
LOCK_FILE = os.environ.get("MCP_LOCK_FILE", "/data/mcp_server/lock/mcp.lock")
GPU_PAUSE_FILE = os.environ.get("QWEN_GPU_PAUSE_FILE", "/data/mcp_server/lock/qwen_gpu_paused.flag")
GPU_CHECK_INTERVAL = int(os.environ.get("QWEN_GPU_CHECK_INTERVAL", "5"))
LOG_DIR = os.environ.get("MCP_LOG_DIR", "/data/mcp_server/logs")


def log(msg: str, level: str = "INFO"):
    """Időbélyegzett logolás."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "qwen_analyzer.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def acquire_lock() -> bool:
    """Intelligens lock: ha már fut egy Qwen folyamat, ne zavarjon."""
    try:
        os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, "r") as f:
                    pid = int(f.read().strip())
                # Ellenőrizzük, hogy a PID él-e
                os.kill(pid, 0)
                log(f"❌ Már fut egy Qwen folyamat (PID {pid}). Lock aktív, kilépek, hogy ne zavarjak.")
                return False
            except (ProcessLookupError, ValueError, OSError):
                # A PID már nem él - stale lock, törljük
                log("⚠️  Stale lock fájl találat, eltávolítom.")
                os.remove(LOCK_FILE)
        # Új lock létrehozása
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        log(f"❌ Lock hiba: {e}", "ERROR")
        return False


def release_lock():
    """Lock feloldása hibabiztosan."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass


def verify_gpu() -> bool:
    """P4000 azonosítás és P2000 elzárás ellenőrzése."""
    try:
        import torch
        if not torch.cuda.is_available():
            log("❌ CUDA nem elérhető!")
            return False
        n = torch.cuda.device_count()
        if n != 1:
            log(f"❌ Hiba: {n} GPU látható (1-nek kellene - csak P4000). P2000 elzárás sikertelen!")
            return False
        name = torch.cuda.get_device_name(0)
        if "P4000" not in name:
            log(f"❌ Hiba: GPU 0 nem P4000, hanem: {name}")
            return False
        log(f"✅ GPU izoláció OK: 1 GPU látható = {name} (P2000 elzárva)")
        return True
    except Exception as e:
        log(f"❌ GPU verifikáció hiba: {e}", "ERROR")
        return False


def resolve_model_path() -> str:
    """A letöltött GGUF modell pontos útvonalának feloldása HF cache-ből."""
    cache_root = os.environ.get("HUGGINGFACE_HUB_CACHE", "/data/ml/hf_cache")
    repo_dir = os.path.join(cache_root, "models--" + MODEL_ID.replace("/", "--"))
    if os.path.isdir(repo_dir):
        snapshots = os.path.join(repo_dir, "snapshots")
        if os.path.isdir(snapshots):
            for snap in os.listdir(snapshots):
                candidate = os.path.join(snapshots, snap, MODEL_FILE)
                if os.path.isfile(candidate):
                    return candidate
    # HF cache fájl nélkül -> letöltés indítása
    log(f"⚠️  Modell nem található a cache-ben. Indítom a letöltést: {MODEL_ID}/{MODEL_FILE}")
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(
        repo_id=MODEL_ID,
        filename=MODEL_FILE,
        cache_dir=cache_root,
    )
    return p


# Globális Llama példány (lazy load)
_LLAMA = None


def get_llama():
    """Lazy betölti a Qwen modellt P4000-re. Egyszer töltődik csak."""
    global _LLAMA
    if _LLAMA is not None:
        return _LLAMA

    if not verify_gpu():
        raise RuntimeError("GPU verifikáció sikertelen - P4000 nem elérhető vagy P2000 nem lett elzárva.")

    model_path = resolve_model_path()
    size_mb = os.path.getsize(model_path) // (1024 * 1024)
    log(f"🧠 Modell betöltése: {model_path} ({size_mb} MB)")

    from llama_cpp import Llama
    t0 = time.time()
    _LLAMA = Llama(
        model_path=model_path,
        n_gpu_layers=GPU_LAYERS,  # -1 = MINDEN réteg GPU-ra kényszerítve (CPU kizárva)
        n_ctx=CONTEXT_SIZE,
        n_threads=N_THREADS,
        verbose=False,
        tensor_split=[0],  # P4000 (GPU 0) kényszerítve
        main_gpu=0,  # Fő GPU explicit
        chat_format="qwen",  # Qwen chat template
    )
    log(f"✅ Modell betöltve {time.time()-t0:.1f}s alatt, GPU rétegek: {GPU_LAYERS}")

    # VRAM használat riport - nvidia-smi segítseggel (torch nem méri a llama_cpp allokációit)
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits', '-i', '0'],
            capture_output=True, text=True, timeout=5
        )
        vram_mb = int(result.stdout.strip())
        log(f"📊 P4000 VRAM használat: {vram_mb} MB (nvidia-smi)")
    except Exception:
        pass
    return _LLAMA


def is_gpu_paused() -> bool:
    """Ellenőrzi, hogy a GPU pause flag aktív-e (más feladat használja a GPU-t)."""
    return os.path.isfile(GPU_PAUSE_FILE)


def wait_for_gpu_available(max_wait: int = 3600) -> bool:
    """
    Vár, amíg a GPU felszabadul (pause flag eltűnik).
    Batch feldolgozásnál használjuk — ha más GPU feladat fut, szünetel.
    max_wait: maximális várakozás másodpercben (alapértelmezett 1 óra).
    """
    waited = 0
    while is_gpu_paused():
        if waited == 0:
            log("⏸️  GPU pause flag aktív — várakozás a GPU felszabadulására...")
        time.sleep(GPU_CHECK_INTERVAL)
        waited += GPU_CHECK_INTERVAL
        if waited >= max_wait:
            log(f"⚠️  GPU várakozás timeout ({max_wait}s) — folytatom erővel.", "WARN")
            return False
        if waited % 30 == 0:
            log(f"⏸️  GPU még foglalt, várakozás... ({waited}s)")
    if waited > 0:
        log(f"▶️  GPU felszabadult {waited}s várakozás után — folytatom a feldolgozást.")
    return True


def qwen_chat(prompt: str, system: str = None, max_tokens: int = 1500, temperature: float = 0.3) -> str:
    """
    Qwen chat completion. Timeout gátlóval, hogy ne loopoljon.
    GPU pause flag ellenőrzés: ha más GPU feladat fut, várakozik.
    """
    # GPU pause ellenőrzése — várakozik ha kell
    wait_for_gpu_available()

    llm = get_llama()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    # Timeout gátló: SIGALRM (csak main thread-ben működik)
    def _timeout_handler(signum, frame):
        raise TimeoutError(f"Qwen generálás timeout ({TIMEOUT_SEC}s)")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SEC)
    try:
        t0 = time.time()
        resp = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            repeat_penalty=1.1,
        )
        elapsed = time.time() - t0
        text = resp["choices"][0]["message"]["content"]
        tok_count = resp.get("usage", {}).get("completion_tokens", 0)
        tps = tok_count / elapsed if elapsed > 0 and tok_count > 0 else 0
        log(f"✅ Válasz generálva {elapsed:.1f}s alatt ({len(text)} karakter, {tok_count} tok, {tps:.1f} tok/s) [{MODEL_PROFILE}]")
        return text
    except TimeoutError as e:
        log(f"❌ {e}", "ERROR")
        return f"[TIMEOUT] {e}"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# =============================================================================
# KÖNYVTÁR-ELEMZŐ FUNKCIÓK
# =============================================================================

# Ezeket a fájlokat prioritizáljuk az elemzéshez (nem kódolunk, csak olvasunk)
PRIORITY_FILES = [
    "README.md", "README_CN.md", "README_EN.md", "readme.md",
    "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md",
    "setup.py", "pyproject.toml", "setup.cfg", "requirements.txt",
    "package.json", "Cargo.toml", "CMakeLists.txt",
    "LICENSE",
]
PRIORITY_EXTS = [".py", ".md", ".toml", ".cfg", ".txt", ".yaml", ".yml", ".json", ".sh"]
# Ezeket a könyvtárakat/típusokat átugorjuk (zaj)
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "build", "dist",
    ".cache", ".pytest_cache", ".mypy_cache", "site-packages", "vendor",
}
MAX_FILE_SIZE = 64 * 1024  # 64KB felett nem olvasunk (túl nagy)


def discover_repo_files(repo_dir: str, max_files: int = 30) -> list:
    """
    Egy repó könyvtárában felfedezi a prioritizált fájlokat az elemzéshez.
    Visszatér: [{path, relpath, size}, ...]
    """
    repo_path = Path(repo_dir)
    results = []

    # 1. Gyökérben lévő prioritizált fájlok
    for fname in PRIORITY_FILES:
        candidate = repo_path / fname
        if candidate.is_file() and candidate.stat().st_size <= MAX_FILE_SIZE:
            results.append({
                "path": str(candidate),
                "relpath": fname,
                "size": candidate.stat().st_size,
            })

    # 2. Bejárás prioritizált kiterjesztésekkel (mélységi limit 3)
    def walk(path: Path, depth: int = 0):
        if depth > 3 or len(results) >= max_files:
            return
        try:
            for entry in sorted(path.iterdir(), key=lambda p: p.name):
                if len(results) >= max_files:
                    return
                if entry.is_dir():
                    if entry.name in SKIP_DIRS or entry.name.startswith("."):
                        continue
                    walk(entry, depth + 1)
                elif entry.is_file():
                    if entry.stat().st_size > MAX_FILE_SIZE or entry.stat().st_size == 0:
                        continue
                    if entry.suffix.lower() in PRIORITY_EXTS:
                        rel = str(entry.relative_to(repo_path))
                        # ne duplikáljuk a gyökérfájlokat
                        if any(r["relpath"] == rel for r in results):
                            continue
                        results.append({
                            "path": str(entry),
                            "relpath": rel,
                            "size": entry.stat().st_size,
                        })
        except (PermissionError, OSError):
            pass

    walk(repo_path)
    return results[:max_files]


def read_file_sample(path: str, max_chars: int = 2000) -> str:
    """Egy fájl első N karakterének olvasása (biztonságos)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception as e:
        return f"[olvasási hiba: {e}]"


def analyze_repo(repo_dir: str, max_files: int = 30, max_tokens: int = 1500, memory_context: str = None) -> str:
    """
    Egy repó könyvtár elemzése Qwen-nel. A Qwen dönti el, mi érdemes alaposabban.
    """
    repo_dir = os.path.abspath(repo_dir)
    if not os.path.isdir(repo_dir):
        return f"HIBA: {repo_dir} nem könyvtár"

    log(f"📁 Repó felfedezése: {repo_dir}")
    files = discover_repo_files(repo_dir, max_files=max_files)
    log(f"   {len(files)} fájl azonosítva elemzésre")

    if not files:
        return "Nem találhatók elemzendő fájlok a könyvtárban."

    # Összeállítjuk a kontextust a Qwen-nek
    context_parts = []
    for f in files:
        sample = read_file_sample(f["path"], max_chars=1500)
        context_parts.append(
            f"### {f['relpath']} ({f['size']} bájt)\n```\n{sample}\n```"
        )
    context = "\n\n".join(context_parts)

    # Ha túl hosszú, csonkítjuk
    if len(context) > 6000:
        context = context[:6000] + "\n\n[... csonkítva ...]"

    system_prompt = (
        "Te egy ügyes kód-elemző asszisztens vagy. Feladatod egy szoftveres repó könyvtárának "
        "elemzése. Nem kódolsz, csak strukturált Markdown naplót írsz. "
        "Magyar nyelven válaszolj, de a kód-/fájlnév-/technológia-azonosítókat angolul hagyd."
    )

    context_block = ""
    if memory_context:
        context_block = f"""
## Releváns kontextus a rendszer-memóriából (prioritizált)

{memory_context}

---
"""

    prompt = f"""{context_block}Elemezd az alábbi repó könyvtárát: `{repo_dir}`

Az alábbi fájlokat találtam és beolvastam (részlet):

{context}

Készíts egy Markdown naplót a következő szerkezettel:

## Repó áttekintése
- Mi a repó célja (1-2 mondat)
- Milyen technológiát használ (nyelv, framework-ök)

## Fő komponensek
- A legfontosabb modulok/könyvtárak felsorolása és rövid leírása

## 🎯 Érdemes alaposabban megnézni
- Pontos fájlelérási utak (relatív a repó gyökeréhez) azokhoz a fájlokhoz, amiket érdemes részletesen tanulmányozni
- Minden fájlnál 1 mondat, hogy miért érdekes

## Kapcsolódó repók
- Ha látsz cross-references-t más repókhoz, említsd meg

A válasz VIZUÁLIS LEHETŐLEG LEGYEN PONTOS - csak valós fájlokat/jellemzőket említs, amit a kontextusban látsz.
"""
    return qwen_chat(prompt, system=system_prompt, max_tokens=max_tokens, temperature=0.3)


def write_analysis(target_dir: str, content: str, suffix: str = "_qwen_analysis"):
    """A Qwen által írt napló elmentése a célkönyvtár _qwen_analysis almappájába."""
    repo_name = os.path.basename(os.path.abspath(target_dir))
    out_dir = os.path.join(target_dir, suffix)
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"{repo_name}_analysis_{ts}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Qwen elemzés: {repo_name}\n")
        f.write(f"*Generálva: {datetime.now().isoformat()} | Modell: Qwen2.5-Coder-7B-Instruct Q5_K_M | GPU: P4000*\n\n")
        f.write(content)
    log(f"📝 Elemzés elmentve: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Qwen2.5-Coder repó-elemző (P4000)")
    parser.add_argument("target_dir", help="Elemzendő könyvtár (pl. /data/Brain)")
    parser.add_argument("--max-files", type=int, default=25, help="Max olvasott fájl (default: 25)")
    parser.add_argument("--max-tokens", type=int, default=1800, help="Max generált token (default: 1800)")
    parser.add_argument("--context-query", type=str, default=None,
                        help="Kontextus prioritas (memória injekció a promptba)")
    args = parser.parse_args()

    print("=" * 70)
    print("🤖 QWEN2.5-CODER-7B REPÓ-ELEMZŐ (P4000 kényszerítve, P2000 elzárva)")
    print("=" * 70)

    # Lock megszerzése (intelligens, ne zavarjon)
    if not acquire_lock():
        sys.exit(2)

    try:
        # GPU verifikáció
        if not verify_gpu():
            sys.exit(1)

        # Elemzés
        memory_context = None
        if args.context_query:
            try:
                from context_prioritizer import ContextPrioritizer
                cp = ContextPrioritizer()
                memory_context = cp.build_context(args.context_query)
            except Exception as e:
                log(f"Kontextus prioritás hiba (átugorva): {e}")
        content = analyze_repo(args.target_dir, max_files=args.max_files,
                               max_tokens=args.max_tokens,
                               memory_context=memory_context)
        out_path = write_analysis(args.target_dir, content)

        print("\n" + "=" * 70)
        print(f"✅ ELEMZÉS KÉSZ")
        print(f"📝 Kimenet: {out_path}")
        print("=" * 70)
        print("\n--- ELEMZÉS TARTALMA ---\n")
        print(content)
    finally:
        # Memória felszabadítás
        global _LLAMA
        if _LLAMA is not None:
            del _LLAMA
            _LLAMA = None
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
            log("GPU cache tisztítva")
        except Exception:
            pass
        release_lock()


if __name__ == "__main__":
    main()
