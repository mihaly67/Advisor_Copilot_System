#!/usr/bin/env python3
"""KG Search helper - direct SQLite access, no MCP server needed."""
import sys, os, json
sys.path.insert(0, "/data/mcp_server/tools")
from knowledge_graph_tools import KnowledgeGraphDB

DB_PATH = "/data/mcp_server/data/knowledge_graph.db"
_kg = None

def get_kg():
    global _kg
    if _kg is None:
        _kg = KnowledgeGraphDB(DB_PATH)
    return _kg

def search(query, top_k=10):
    return get_kg().search_concepts(query, top_k=top_k)

def get_concept(concept_id):
    return get_kg().get_concept(concept_id)

def get_context(query, max_chars=8000):
    from knowledge_graph_tools import ContextCompressor
    kg = get_kg()
    return ContextCompressor(kg, max_chars=max_chars).build_context(query)

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('query')
    p.add_argument('--top-k', type=int, default=10)
    p.add_argument('--context', action='store_true')
    a = p.parse_args()
    if a.context:
        print(get_context(a.query))
    else:
        print(json.dumps(search(a.query, a.top_k), indent=2, default=str))
