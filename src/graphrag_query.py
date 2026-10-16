#!/usr/bin/env python3
"""GraphRAG Integration — Scalper Copilot tudásgráf

Microsoft GraphRAG: Entity + Relationship + Community gráf
Hierarchical Leiden clustering → community detekció
Local search (entity-környezet) + Global search (community-összefoglaló)

Használat:
    python3 graphrag_query.py --index          # Indexelés (egyszer)
    python3 graphrag_query.py --local "meta labeling"  # Lokális keresés
    python3 graphrag_query.py --global "milyen feature-k kellenek?"  # Globális
"""
import subprocess, sys, json
from pathlib import Path

GRAPH_DIR = Path('/data/LGBM_copilot/graphrag_data')

def run_index():
    """GraphRAG indexelés — entity/relationship/community gráf építés."""
    print("📊 GraphRAG indexelés...")
    print(f"   Input: {GRAPH_DIR/'input'} ({len(list((GRAPH_DIR/'input').glob('*')))} fájl)")
    cmd = f"cd {GRAPH_DIR} && graphrag index --root ."
    print(f"   Cmd: {cmd}")
    subprocess.run(cmd, shell=True)

def run_query(method: str, query: str):
    """GraphRAG keresés — local vagy global."""
    print(f"🔍 GraphRAG {method} search: {query}")
    cmd = f"cd {GRAPH_DIR} && graphrag query --root . --method {method} --query \"{query}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"⚠️ {result.stderr}", file=sys.stderr)

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--index' in args:
        run_index()
    elif '--local' in args:
        i = args.index('--local')
        run_query('local', args[i+1] if i+1 < len(args) else 'dollar bar')
    elif '--global' in args:
        i = args.index('--global')
        run_query('global', args[i+1] if i+1 < len(args) else 'features')
    else:
        print(__doc__)
