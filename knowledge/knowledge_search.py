"""
Knowledge Space Search — lightweight search in copilot knowledge base
No FAISS needed — searches decision trees, code templates, digests, anti-patterns
"""
import json
from pathlib import Path

KS_PATH = Path("/data/LGBM_copilot/knowledge")

def search(query_text: str, top_k: int = 5) -> list:
    """Search the copilot knowledge space."""
    if not KS_PATH.exists():
        return []
    
    results = []
    ql = query_text.lower()
    
    # Search decision trees (L0)
    for f in (KS_PATH / "decision_trees").glob("*.json"):
        try:
            data = json.load(open(f))
            content = json.dumps(data).lower()
            if ql in content:
                results.append({"source": f"decision_tree/{f.name}", "level": "L0", "relevance": "HIGH"})
        except: pass
    
    # Search code templates (L1)
    for f in (KS_PATH / "code_templates").glob("*.py"):
        try:
            content = f.read_text().lower()
            if ql in content:
                results.append({"source": f"code_template/{f.name}", "level": "L1", "relevance": "HIGH"})
        except: pass
    
    # Search reference digests (L2)
    for f in (KS_PATH / "reference_digests").glob("*.md"):
        try:
            content = f.read_text().lower()
            if ql in content:
                results.append({"source": f"digest/{f.name}", "level": "L2", "relevance": "MEDIUM"})
        except: pass
    
    # Search anti-patterns (L0)
    for f in (KS_PATH / "anti_patterns").glob("*.json"):
        try:
            data = json.load(open(f))
            content = json.dumps(data).lower()
            if ql in content:
                results.append({"source": f"anti_pattern/{f.name}", "level": "L0", "relevance": "HIGH"})
        except: pass
    
    # Search checklists (L0)
    for f in (KS_PATH / "checklists").glob("*.json"):
        try:
            data = json.load(open(f))
            content = json.dumps(data).lower()
            if ql in content:
                results.append({"source": f"checklist/{f.name}", "level": "L0", "relevance": "MEDIUM"})
        except: pass
    
    # Search pipeline chain (L0)
    for f in (KS_PATH / "pipeline_chain").glob("*.json"):
        try:
            data = json.load(open(f))
            content = json.dumps(data).lower()
            if ql in content:
                results.append({"source": f"pipeline/{f.name}", "level": "L0", "relevance": "MEDIUM"})
        except: pass
    
    return results[:top_k]


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "triple barrier"
    results = search(query)
    print(f"Query: '{query}' → {len(results)} results")
    for r in results:
        print(f"  [{r['level']}] {r['source']} ({r['relevance']})")
