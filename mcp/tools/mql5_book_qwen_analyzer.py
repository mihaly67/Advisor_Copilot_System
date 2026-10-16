#!/usr/bin/env python3
"""
mql5_book_qwen_analyzer.py — MQL5 szakkönyv Qwen mélyelemzése

A mql5book.md (102K sor, 4.2MB) és mql5.md (272K sor, 7.6MB) könyveket
darabolja fejezetenként, és Qwen-nel elemzi az egyes szekciókat.
Emellett lekérdezi az mql5_native_knowledge.db SQLite RAG adatbázist
kulcstémákra, és az eredményeket strukturált Markdown-ba írja.

Használat:
    source /data/mcp_server/env.sh
    python3 /data/mcp_server/tools/mql5_book_qwen_analyzer.py [--max-chunks N]

Kimenet:
    /data/MQL5/_qwen_analysis/mql5_book_analysis.md
"""
import os
import sys
import re
import gc
import time
import sqlite3
import argparse
from datetime import datetime

# GPU izoláció (P4000 kényszerítése)
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")

MODEL_PROFILE = os.environ.get("QWEN_MODEL_PROFILE", "7B")
MODEL_ID = os.environ.get("QWEN_MODEL_ID", "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
MODEL_FILE = os.environ.get("QWEN_MODEL_FILE", "qwen2.5-coder-7b-instruct-q5_k_m.gguf")
GPU_LAYERS = int(os.environ.get("QWEN_GPU_LAYERS", "-1"))
CONTEXT_SIZE = int(os.environ.get("QWEN_CONTEXT_SIZE", "8192"))
N_THREADS = int(os.environ.get("QWEN_N_THREADS", "4"))
TIMEOUT_SEC = int(os.environ.get("QWEN_TIMEOUT_SECONDS", "300"))
GPU_PAUSE_FILE = os.environ.get("QWEN_GPU_PAUSE_FILE", "/data/mcp_server/lock/qwen_gpu_paused.flag")
GPU_CHECK_INTERVAL = int(os.environ.get("QWEN_GPU_CHECK_INTERVAL", "5"))

MQL5_DIR = "/data/MQL5"
BOOK_FILE = os.path.join(MQL5_DIR, "mql5book.md")
BOOK2_FILE = os.path.join(MQL5_DIR, "mql5.md")
NEURO_FILE = os.path.join(MQL5_DIR, "neuronetworksbook.md")
RAG_DB = os.path.join(MQL5_DIR, "mql5_native_knowledge.db")
OUT_DIR = os.path.join(MQL5_DIR, "_qwen_analysis")

# Qwen modell (lazy load)
_LLAMA = None

def is_gpu_paused():
    """Ellenőrzi, hogy a GPU pause flag aktív-e."""
    return os.path.isfile(GPU_PAUSE_FILE)


def wait_for_gpu_available(max_wait=3600):
    """Vár, amíg a GPU felszabadul (pause flag eltűnik)."""
    waited = 0
    while is_gpu_paused():
        if waited == 0:
            print(f"⏸️  GPU pause aktív — várakozás...")
        time.sleep(GPU_CHECK_INTERVAL)
        waited += GPU_CHECK_INTERVAL
        if waited >= max_wait:
            print(f"⚠️  GPU várakozás timeout ({max_wait}s) — folytatom.")
            return False
        if waited % 30 == 0:
            print(f"⏸️  GPU még foglalt... ({waited}s)")
    if waited > 0:
        print(f"▶️  GPU felszabadult {waited}s után — folytatom.")
    return True


def get_llama():
    global _LLAMA
    if _LLAMA is not None:
        return _LLAMA
    cache_root = os.environ.get("HUGGINGFACE_HUB_CACHE", "/data/ml/hf_cache")
    repo_dir = os.path.join(cache_root, "models--" + MODEL_ID.replace("/", "--"))
    model_path = None
    if os.path.isdir(repo_dir):
        snapshots = os.path.join(repo_dir, "snapshots")
        if os.path.isdir(snapshots):
            for snap in os.listdir(snapshots):
                candidate = os.path.join(snapshots, snap, MODEL_FILE)
                if os.path.isfile(candidate):
                    model_path = candidate
                    break
    if not model_path:
        print(f"❌ Modell nem található: {MODEL_ID}/{MODEL_FILE}")
        sys.exit(1)
    print(f"🧠 Modell betöltése [{MODEL_PROFILE}]: {model_path}")
    from llama_cpp import Llama
    _LLAMA = Llama(
        model_path=model_path,
        n_gpu_layers=GPU_LAYERS,
        n_ctx=CONTEXT_SIZE,
        n_threads=N_THREADS,
        verbose=False,
        tensor_split=[0],
        main_gpu=0,
        chat_format="qwen",
    )
    print(f"✅ Modell betöltve [{MODEL_PROFILE}, GPU layers: {GPU_LAYERS}]")
    try:
        import subprocess
        r = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits', '-i', '0'],
                           capture_output=True, text=True, timeout=5)
        print(f"📊 P4000 VRAM: {r.stdout.strip()} MB")
    except Exception:
        pass


def qwen_analyze(prompt, system=None, max_tokens=1200, temperature=0.2):
    """Qwen chat completion egy chunk elemzéshez. GPU pause-aware."""
    wait_for_gpu_available()
    llm = get_llama()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        t0 = time.time()
        resp = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
        )
        elapsed = time.time() - t0
        text = resp["choices"][0]["message"]["content"]
        tok = resp.get("usage", {}).get("completion_tokens", 0)
        tps = tok / elapsed if elapsed > 0 and tok > 0 else 0
        print(f"      ✅ {elapsed:.1f}s | {tok} tok | {tps:.1f} tok/s [{MODEL_PROFILE}]")
        return text
    except Exception as e:
        return f"[Qwen hiba: {e}]"


def split_book_into_chunks(filepath, chunk_pages=15):
    """
    A könyvet '## Page N' markerek szerint darabolja.
    chunk_pages oldal egy chunk (kb. 15 oldal = ~3K sor = ~15K karakter).
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # "## Page N" szerint szétválaszt
    pattern = r'(?=^## Page \d+)'
    pages = re.split(pattern, content, flags=re.MULTILINE)
    pages = [p for p in pages if p.strip()]

    # Chunk-okba grouping
    chunks = []
    for i in range(0, len(pages), chunk_pages):
        chunk = "\n".join(pages[i:i + chunk_pages])
        # Csonkítás ha túl hosszú (max 25K karakter)
        if len(chunk) > 25000:
            chunk = chunk[:25000] + "\n\n[... csonkítva ...]"
        # Oldaltartomány meghatározása
        start_page = i + 1
        end_page = min(i + chunk_pages, len(pages))
        chunks.append({
            "content": chunk,
            "start_page": start_page,
            "end_page": end_page,
            "char_count": len(chunk),
        })
    return chunks


SYSTEM_PROMPT = (
    "Te egy MQL5 programozási szakkönyv elemző asszisztens vagy. "
    "Feladatod egy MQL5 könyv egy szakaszának strukturált elemzése. "
    "Markdown formátumban írd le: milyen témák szerepelnek, milyen MQL5 függvények, "
    "típusok, osztályok, API-k szerepelnek, milyen programozási minták láthatók. "
    "Külön kiemeld a trading-releváns részeket (socket, trade, indikátor, EA). "
    "Rövid, tömör, strukturált Markdown formátumban válaszolj."
)


def analyze_book_chunks(filepath, name, max_chunks=None):
    """Egy könyv összes chunk-jának elemzése."""
    chunks = split_book_into_chunks(filepath)
    print(f"📚 {name}: {len(chunks)} chunk azonosítva")

    if max_chunks:
        chunks = chunks[:max_chunks]
        print(f"   Max chunks limit: {max_chunks}")

    analyses = []
    for i, chunk in enumerate(chunks):
        print(f"   [{i+1}/{len(chunks)}] Oldalak {chunk['start_page']}-{chunk['end_page']} ({chunk['char_count']} char)...")
        prompt = (
            f"Elemezd az MQL5 szakkönyv következő szakaszát (oldalak {chunk['start_page']}-{chunk['end_page']}):\n\n"
            f"{chunk['content']}\n\n"
            f"Írj strukturált Markdown elemzést a fenti szakaszról."
        )
        analysis = qwen_analyze(prompt, system=SYSTEM_PROMPT, max_tokens=1200)
        analyses.append({
            "start_page": chunk["start_page"],
            "end_page": chunk["end_page"],
            "analysis": analysis,
        })
        print(f"      ✅ Kész ({len(analysis)} char)")
        time.sleep(2)  # GPU hűtés

    return analyses


# ============================================================================
# SQLite RAG adatbázis lekérdezés
# ============================================================================
RAG_TOPICS = [
    "socket", "SocketCreate", "SocketSend", "SocketConnect", "SocketRead",
    "OnTick", "OnInit", "OnDeinit", "OnTimer", "OnChartEvent",
    "OrderSend", "OrderModify", "OrderClose", "PositionSelect", "PositionModify",
    "CopyTicks", "CopyRates", "CopyClose", "CopyOpen", "CopyHigh", "CopyLow",
    "iRSI", "iMACD", "iMA", "iCustom", "iStochastic", "iATR", "iBands",
    "CTrade", "CSymbolInfo", "CPositionInfo", "CAccountInfo",
    "MarketBookAdd", "MarketBookGet", "DepthOfMarket",
    "input", "sinput", "extern", "#property", "#include",
    "struct", "class", "template", "enum", "void",
    "ArraySetAsSeries", "ArrayResize", "ArrayCopy", "ArraySort",
    "FileOpen", "FileWrite", "FileRead", "FileClose",
    "ChartSetInteger", "ChartGetInteger", "ChartRedraw", "ObjectsCreateAll",
    "IndicatorCreate", "IndicatorRelease", "IndicatorSetInteger",
    "StringFormat", "StringReplace", "StringToCharArray", "CharArrayToString",
    "Print", "PrintFormat", "Comment", "Alert",
    "EventChartCustom", "EventSetTimer", "EventKillTimer",
    "ZigZag", "Pivot", "Support", "Resistance",
    "double", "int", "string", "bool", "datetime", "long", "ulong",
    "datetime", "PERIOD_M1", "PERIOD_M5", "PERIOD_M15", "PERIOD_M30", "PERIOD_H1",
]


def query_rag_database(topic, limit=5):
    """Lekérdezi az SQLite RAG adatbázist egy adott témára."""
    try:
        conn = sqlite3.connect(RAG_DB)
        cur = conn.cursor()
        sql = "SELECT filepath, content FROM rag_data WHERE content LIKE ? LIMIT ?"
        cur.execute(sql, (f"%{topic}%", limit))
        results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        return []


def analyze_rag_topics(max_topics=None):
    """Kulcstémák elemzése az RAG adatbázisból."""
    topics = RAG_TOPICS[:max_topics] if max_topics else RAG_TOPICS
    results = {}

    for i, topic in enumerate(topics):
        print(f"   [{i+1}/{len(topics)}] RAG lekérdezés: {topic}")
        matches = query_rag_database(topic, limit=3)
        if matches:
            # Összeállítjuk a találatokat
            combined = "\n---\n".join([m[1][:2000] for m in matches])
            prompt = (
                f"Az MQL5 RAG adatbázisban a '{topic}' témára a következő találatok vannak:\n\n"
                f"{combined}\n\n"
                f"Írj egy rövid, strukturált Markdown összefoglalót a '{topic}' MQL5 témáról "
                f"a fenti források alapján. Kiemeld a szintaxist, paramétereket, használati példákat."
            )
            analysis = qwen_analyze(prompt, system=SYSTEM_PROMPT, max_tokens=800)
            results[topic] = analysis
            print(f"      ✅ {len(analysis)} char")
        else:
            results[topic] = None
            print(f"      ⚪ Nincs találat")
        time.sleep(1)

    return results


# ============================================================================
# Fő program
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="MQL5 könyv Qwen elemzés")
    parser.add_argument("--max-chunks", type=int, default=None, help="Max chunk-ok száma könyvenként")
    parser.add_argument("--max-topics", type=int, default=None, help="Max RAG témák száma")
    parser.add_argument("--books-only", action="store_true", help="Csak könyv elemzés")
    parser.add_argument("--rag-only", action="store_true", help="Csak RAG adatbázis elemzés")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"📁 Kimenet: {OUT_DIR}")

    # 1. RAG adatbázis elemzés
    if not args.books_only:
        print("\n" + "=" * 60)
        print("PHASE 1: SQLite RAG adatbázis elemzés")
        print("=" * 60)
        rag_results = analyze_rag_topics(args.max_topics)

        # RAG eredmények írása
        rag_path = os.path.join(OUT_DIR, "mql5_rag_topic_analysis.md")
        with open(rag_path, "w", encoding="utf-8") as f:
            f.write("# MQL5 RAG Adatbázis Téma-elemzés\n\n")
            f.write(f"> **Forrás:** {RAG_DB} (9780 row)\n")
            f.write(f"> **Dátum:** {datetime.now().isoformat()}\n\n")
            for topic, analysis in rag_results.items():
                f.write(f"## {topic}\n\n")
                if analysis:
                    f.write(analysis + "\n\n")
                else:
                    f.write("*Nincs találat az RAG adatbázisban.*\n\n")

    # 2. Könyv chunk-elemzés
    if not args.rag_only:
        print("\n" + "=" * 60)
        print("PHASE 2: MQL5 könyv fejezet-elemzés")
        print("=" * 60)

        books = [
            (BOOK_FILE, "MQL5 Programming for Traders (mql5book)"),
            (BOOK2_FILE, "MQL5 Reference Documentation (mql5)"),
            (NEURO_FILE, "Neural Networks for Algorithmic Trading with MQL5"),
        ]

        for book_path, book_name in books:
            if not os.path.isfile(book_path):
                print(f"⚠️ {book_path} nem található, kihagyom")
                continue

            print(f"\n📖 Könyv: {book_name}")
            analyses = analyze_book_chunks(book_path, book_name, args.max_chunks)

            # Eredmény írása
            safe_name = book_name.split("(")[0].strip().replace(" ", "_").lower()
            out_path = os.path.join(OUT_DIR, f"{safe_name}_qwen_analysis.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {book_name} — Qwen Mélyelemzés\n\n")
                f.write(f"> **Forrás:** {book_path}\n")
                f.write(f"> **Dátum:** {datetime.now().isoformat()}\n")
                f.write(f"> **Chunk-ok száma:** {len(analyses)}\n\n")
                f.write("---\n\n")
                for a in analyses:
                    f.write(f"## Oldalak {a['start_page']}-{a['end_page']}\n\n")
                    f.write(a["analysis"] + "\n\n---\n\n")
            print(f"✅ Könyv elemzés elmentve: {out_path}")

    # 3. Összegzés
    print("\n" + "=" * 60)
    print("PHASE 3: Globális összegzés")
    print("=" * 60)

    summary_prompt = (
        "Készíts egy átfogó MQL5 tudás-struktúrát a következő témakörökből:\n"
        "- MQL5 szintaxis és adattípusok\n"
        "- EA fejlesztés (OnInit, OnTick, OnDeinit)\n"
        "- Socket kommunikáció (SocketCreate, SocketSend)\n"
        "- Trade műveletek (CTrade, OrderSend)\n"
        "- Technikai indikátorok (iRSI, iMACD)\n"
        "- Adatlekérdezés (CopyTicks, CopyRates)\n"
        "- Standard könyvtár (Trade, Expert, Indicators)\n"
        "- DOM / MarketBook (DepthOfMarket)\n"
        "- Neural Networks for Algorithmic Trading with MQL5\n\n"
        "Írj egy strukturált Markdown dokumentumot ami átfogja ezeket a témákat."
    )
    summary = qwen_analyze(summary_prompt, system=SYSTEM_PROMPT, max_tokens=1500)
    summary_path = os.path.join(OUT_DIR, "mql5_knowledge_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# MQL5 Tudás-struktúra — Globális Összegzés\n\n")
        f.write(f"> **Dátum:** {datetime.now().isoformat()}\n\n")
        f.write(summary)
    print(f"✅ Globális összegzés elmentve: {summary_path}")

    print("\n✅ Minden elemzés befejezve!")
    print(f"📁 Eredmények: {OUT_DIR}/")


if __name__ == "__main__":
    main()

