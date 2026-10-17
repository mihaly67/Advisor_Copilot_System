#!/usr/bin/env python3
"""
Knowledge Graph Tools - MegaMemory + yantrikdb + HybridRAG

1. KnowledgeGraphDB - SQLite concept/edge store (MegaMemory pattern)
2. ContradictionDetector - yantrikdb-style contradiction detection
3. SequentialThinker - structured multi-step thinking
4. ContextCompressor - yantrikdb temporal decay + token optimization
"""
import sqlite3, json, time, math
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

class NodeKind(Enum):
    FEATURE="feature"; MODULE="module"; PATTERN="pattern"
    CONFIG="config"; DECISION="decision"; PARAMETER="parameter"
    METHOD="method"; INSTRUMENT="instrument"; REFERENCE="reference"
    CONCEPT="concept"; DATA="data"

class RelationType(Enum):
    DEPENDS_ON="depends_on"; CONFLICTS_WITH="conflicts_with"
    INFLUENCES="influences"; REQUIRES="requires"
    REFERENCES="references"; CONFIGURED_BY="configured_by"
    VALIDATED_BY="validated_by"; IMPLEMENTS="implements"
    PRODUCES="produces"; USED_BY="used_by"
    RISK_OF="risk_of"; NEVER_WITH="never_with"

@dataclass
class ConceptNode:
    id: str; name: str; kind: NodeKind; summary: str
    why: Optional[str]=None; file_refs: Optional[list]=None
    parent_id: Optional[str]=None; importance: float=0.5
    created_at: float=0.0; updated_at: float=0.0
    removed_at: Optional[float]=None; removed_reason: Optional[str]=None
    domain: Optional[str]=None
    def __post_init__(self):
        if self.created_at==0.0:
            self.created_at=time.time(); self.updated_at=self.created_at

@dataclass
class Contradiction:
    concept_a: str; concept_b: str; relation: str; reason: str
    severity: float; resolution_hint: Optional[str]=None

class KnowledgeGraphDB:
    """SQLite knowledge graph - MegaMemory architecture + yantrikdb decay"""
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS concepts (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,
        summary TEXT NOT NULL, why TEXT, file_refs TEXT,
        parent_id TEXT, importance REAL DEFAULT 0.5, domain TEXT,
        created_at REAL NOT NULL, updated_at REAL NOT NULL,
        removed_at REAL, removed_reason TEXT
    );
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id TEXT NOT NULL, to_id TEXT NOT NULL,
        relation TEXT NOT NULL, description TEXT,
        strength REAL DEFAULT 1.0, created_at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS contradictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concept_a TEXT NOT NULL, concept_b TEXT NOT NULL,
        relation TEXT NOT NULL, reason TEXT NOT NULL,
        severity REAL DEFAULT 0.5, resolution_hint TEXT,
        detected_at REAL NOT NULL, resolved_at REAL, resolved_how TEXT
    );
    CREATE TABLE IF NOT EXISTS thinking_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem TEXT NOT NULL, steps TEXT NOT NULL,
        conclusion TEXT, confidence REAL DEFAULT 0.0, created_at REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_concepts_kind ON concepts(kind);
    CREATE INDEX IF NOT EXISTS idx_concepts_domain ON concepts(domain);
    CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
    CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id);
    """

    def __init__(self, db_path="/data/mcp_server/data/knowledge_graph.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(self.SCHEMA); self.conn.commit()

    def make_id(self, name, parent_id=None):
        slug = name.lower().replace("_","-").replace(" ","-")
        slug = "".join(c for c in slug if c.isalnum() or c=="-")
        slug = "-".join(s for s in slug.split("-") if s)
        return f"{parent_id}/{slug}" if parent_id else slug

    def create_concept(self, node):
        if not node.id: node.id = self.make_id(node.name, node.parent_id)
        now = time.time()
        self.conn.execute(
            "INSERT OR REPLACE INTO concepts (id,name,kind,summary,why,file_refs,parent_id,importance,domain,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (node.id, node.name, node.kind.value, node.summary, node.why,
             json.dumps(node.file_refs) if node.file_refs else None,
             node.parent_id, node.importance, node.domain, now, now))
        self.conn.commit(); return node.id

    def get_concept(self, cid):
        cur = self.conn.execute("SELECT * FROM concepts WHERE id=? AND removed_at IS NULL", (cid,))
        row = cur.fetchone()
        if not row: return None
        cols = [d[0] for d in cur.description]; d = dict(zip(cols, row))
        if d.get("file_refs"): d["file_refs"] = json.loads(d["file_refs"])
        d["outgoing"] = self._edges_from(cid); d["incoming"] = self._edges_to(cid)
        d["children"] = self._children(cid); return d

    def update_concept(self, cid, summary=None, importance=None, why=None):
        sets, vals = [], []
        if summary: sets.append("summary=?"); vals.append(summary)
        if importance is not None: sets.append("importance=?"); vals.append(importance)
        if why: sets.append("why=?"); vals.append(why)
        sets.append("updated_at=?"); vals.append(time.time()); vals.append(cid)
        self.conn.execute(f"UPDATE concepts SET {', '.join(sets)} WHERE id=?", vals)
        self.conn.commit()

    def remove_concept(self, cid, reason):
        self.conn.execute("UPDATE concepts SET removed_at=?, removed_reason=? WHERE id=?",
                          (time.time(), reason, cid)); self.conn.commit()

    def list_roots(self):
        cur = self.conn.execute("SELECT id,name,kind,summary FROM concepts WHERE parent_id IS NULL AND removed_at IS NULL ORDER BY kind,name")
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    def search_concepts(self, query, top_k=10):
        cur = self.conn.execute(
            "SELECT id,name,kind,summary,importance FROM concepts WHERE removed_at IS NULL AND (name LIKE ? OR summary LIKE ? OR domain LIKE ?) ORDER BY importance DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query}%", top_k))
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    def _edges_from(self, cid):
        cur = self.conn.execute("SELECT e.relation,e.to_id,c.name as to_name,e.description,e.strength FROM edges e JOIN concepts c ON e.to_id=c.id WHERE e.from_id=?", (cid,))
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    def _edges_to(self, cid):
        cur = self.conn.execute("SELECT e.relation,e.from_id,c.name as from_name,e.description,e.strength FROM edges e JOIN concepts c ON e.from_id=c.id WHERE e.to_id=?", (cid,))
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    def _children(self, cid):
        cur = self.conn.execute("SELECT id,name,kind,summary FROM concepts WHERE parent_id=? AND removed_at IS NULL", (cid,))
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    def link(self, from_id, to_id, relation, description=None, strength=1.0):
        self.conn.execute("INSERT INTO edges (from_id,to_id,relation,description,strength,created_at) VALUES (?,?,?,?,?,?)",
                          (from_id, to_id, relation.value, description, strength, time.time()))
        self.conn.commit()
        if relation in (RelationType.CONFLICTS_WITH, RelationType.NEVER_WITH):
            self._record_contradiction(from_id, to_id, relation.value, description or "Explicit conflict", 0.9)

    def _record_contradiction(self, a, b, rel, reason, sev):
        self.conn.execute("INSERT INTO contradictions (concept_a,concept_b,relation,reason,severity,detected_at) VALUES (?,?,?,?,?,?)",
                          (a, b, rel, reason, sev, time.time())); self.conn.commit()

    def detect_contradictions(self):
        results = []
        cur = self.conn.execute("SELECT concept_a,concept_b,relation,reason,severity,resolution_hint FROM contradictions WHERE resolved_at IS NULL")
        for row in cur.fetchall(): results.append(Contradiction(*row))
        cur = self.conn.execute("SELECT e1.from_id,e2.from_id,e1.to_id FROM edges e1 JOIN edges e2 ON e1.to_id=e2.to_id WHERE e1.relation='influences' AND e2.relation='influences' AND e1.from_id!=e2.from_id")
        for a, b, tgt in cur.fetchall():
            ca, cb = self.get_concept(a), self.get_concept(b)
            if ca and cb and ca.get("domain")==cb.get("domain") and ca["domain"]:
                results.append(Contradiction(a, b, "implicit_conflict", f"Both influence '{tgt}' in '{ca['domain']}'", 0.4))
        return results

    def resolve_contradiction(self, a, b, how):
        self.conn.execute("UPDATE contradictions SET resolved_at=?, resolved_how=? WHERE concept_a=? AND concept_b=? AND resolved_at IS NULL",
                          (time.time(), how, a, b)); self.conn.commit()

    def apply_decay(self, half_life_hours=168.0):
        now = time.time(); factor = math.log(0.5)/(half_life_hours*3600)
        self.conn.execute("UPDATE concepts SET importance=importance*exp(?*(?-updated_at)/3600) WHERE removed_at IS NULL AND importance>0.01", (factor, now))
        self.conn.execute("UPDATE concepts SET removed_at=?, removed_reason='decayed' WHERE removed_at IS NULL AND importance<0.01", (now,)); self.conn.commit()

    def trace_path(self, start, end, max_depth=6):
        visited, queue = set(), [(start, [start])]
        while queue:
            cur, path = queue.pop(0)
            if cur==end: return path
            if cur in visited or len(path)>max_depth: continue
            visited.add(cur)
            for e in self._edges_from(cur):
                if e["to_id"] not in visited: queue.append((e["to_id"], path+[e["to_id"]]))
        return []

    def get_stats(self):
        nc = self.conn.execute("SELECT COUNT(*) FROM concepts WHERE removed_at IS NULL").fetchone()[0]
        ne = self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        ncon = self.conn.execute("SELECT COUNT(*) FROM contradictions WHERE resolved_at IS NULL").fetchone()[0]
        nd = self.conn.execute("SELECT COUNT(DISTINCT domain) FROM concepts WHERE domain IS NOT NULL").fetchone()[0]
        return {"concepts":nc,"edges":ne,"unresolved_contradictions":ncon,"domains":nd}

    def close(self): self.conn.close()

@dataclass
class ThinkStep:
    step_num: int; phase: str; content: str; confidence: float=0.0

class SequentialThinker:
    def __init__(self, kg):
        self.kg = kg; self.steps = []; self.problem = ""
    def start(self, problem):
        self.problem = problem; self.steps = [ThinkStep(1,"problem",problem,1.0)]; return self
    def analyze(self, text, conf=0.0):
        self.steps.append(ThinkStep(len(self.steps)+1,"analysis",text,conf)); return self
    def consider_options(self, options):
        n = len(self.steps)+1
        txt = "\n".join(f"  - {name}: {score:.2f}" for name,score in options)
        self.steps.append(ThinkStep(n,"options",txt,max(options,key=lambda x:x[1])[1])); return self
    def evaluate(self, chosen, reason, conf):
        self.steps.append(ThinkStep(len(self.steps)+1,"evaluation",f"CHOSEN: {chosen}\nREASON: {reason}",conf)); return self
    def conclude(self, conclusion):
        self.steps.append(ThinkStep(len(self.steps)+1,"conclusion",conclusion,self.steps[-1].confidence if self.steps else 0.0))
        self.kg.conn.execute("INSERT INTO thinking_sessions (problem,steps,conclusion,confidence,created_at) VALUES (?,?,?,?,?)",
            (self.problem, json.dumps([asdict(s) for s in self.steps]), conclusion, self.steps[-1].confidence, time.time()))
        self.kg.conn.commit()
        return {"problem":self.problem,"steps":len(self.steps),"conclusion":conclusion,
                "confidence":self.steps[-1].confidence,"contradictions":len(self.kg.detect_contradictions())}

class ContextCompressor:
    def __init__(self, kg, max_chars=8000):
        self.kg = kg; self.max_chars = max_chars
    def build_context(self, query):
        results = self.kg.search_concepts(query, top_k=20)
        if not results: return ""
        parts, total = [], 0
        for r in results:
            c = self.kg.get_concept(r["id"])
            if not c: continue
            s = f"## {c['name']} [{c['kind']}] (imp={c['importance']:.2f})\n{c['summary']}\n"
            if c.get("why"): s += f"WHY: {c['why']}\n"
            if c.get("outgoing"):
                s += "RELATIONS:\n"
                for e in c["outgoing"]:
                    s += f"  -> {e['relation']} -> {e['to_name']}"
                    if e.get("description"): s += f" ({e['description']})"
                    s += "\n"
            if total+len(s)>self.max_chars: break
            parts.append(s); total+=len(s)
        contradictions = self.kg.detect_contradictions()
        if contradictions:
            parts.append("\n## CONTRADICTIONS\n")
            for c in contradictions[:5]:
                parts.append(f"  {c.concept_a} <-> {c.concept_b}: {c.reason} [sev={c.severity:.1f}]\n")
        return "\n".join(parts)

def build_scalper_knowledge_graph(kg):
    """LGBM_copilot domain knowledge graph - 30+ entities, 50+ relations"""
    for pid,summ,imp,dom in [
        ("profit-mult","Profit multiplier for triple barrier",0.9,"financial"),
        ("stop-mult","Stop multiplier for triple barrier",0.9,"financial"),
        ("horizon-sec","Time horizon in seconds",0.8,"financial"),
        ("dollar-bar-threshold","Dollar bar threshold",0.85,"pipeline"),
        ("n-estimators","Number of LGBM trees",0.7,"model"),
        ("learning-rate","LGBM learning rate",0.7,"model"),
    ]:
        kg.create_concept(ConceptNode(id=pid,name=pid,kind=NodeKind.PARAMETER,summary=summ,importance=imp,domain=dom))
    for mid,summ,imp,dom in [
        ("triple-barrier","Triple barrier labeling (AFML Ch.3)",0.95,"financial"),
        ("meta-labeling","Meta-labeling secondary model (AFML Ch.3)",0.9,"financial"),
        ("sample-weights","Sample weights: uniqueness-based (AFML Ch.4)",0.85,"financial"),
        ("dollar-bar","Dollar bar sampling (AFML Ch.2)",0.9,"pipeline"),
        ("cusum-filter","CUSUM filter for events (AFML Ch.2)",0.8,"pipeline"),
        ("walk-forward-cv","Walk-forward CV (AFML Ch.7)",0.85,"model"),
        ("purged-cv","Purged embargoed CV (AFML Ch.7)",0.85,"model"),
        ("feature-engineering","Feature engineering pipeline",0.8,"pipeline"),
        ("frac-diff","Fractional differentiation (AFML Ch.5)",0.75,"pipeline"),
    ]:
        kg.create_concept(ConceptNode(id=mid,name=mid,kind=NodeKind.METHOD,summary=summ,importance=imp,domain=dom,why=summ))
    for fid,summ,imp,dom in [
        ("atr","Average True Range",0.85,"financial"),
        ("rsi","Relative Strength Index",0.7,"financial"),
        ("obi-zscore","Order Book Imbalance z-score",0.8,"financial"),
        ("hmm-state","HMM regime state",0.75,"financial"),
        ("macd","MACD",0.7,"financial"),
    ]:
        kg.create_concept(ConceptNode(id=fid,name=fid,kind=NodeKind.FEATURE,summary=summ,importance=imp,domain=dom))
    for did,summ,imp,dom in [
        ("training-tick","Training tick data (in-sample)",0.9,"pipeline"),
        ("exam-tick","Exam tick data (OOS, NEVER for training!)",0.95,"pipeline"),
    ]:
        kg.create_concept(ConceptNode(id=did,name=did,kind=NodeKind.DATA,summary=summ,importance=imp,domain=dom))
    for rid,summ,imp in [
        ("AFML-Ch2","Financial Data Structure",0.9),
        ("AFML-Ch3","Triple Barrier, Meta-Labeling",0.95),
        ("AFML-Ch4","Sample Weights",0.85),
        ("AFML-Ch7","Cross-Validation",0.85),
    ]:
        kg.create_concept(ConceptNode(id=rid,name=rid,kind=NodeKind.REFERENCE,summary=summ,importance=imp,domain="theory"))
    for cid,summ,imp,dom in [
        ("label-distribution","Distribution of labels",0.8,"financial"),
        ("class-imbalance","Class imbalance in labels",0.75,"model"),
        ("leakage","Information leakage",0.95,"model"),
        ("overfitting","Model overfitting",0.85,"model"),
    ]:
        kg.create_concept(ConceptNode(id=cid,name=cid,kind=NodeKind.CONCEPT,summary=summ,importance=imp,domain=dom))
    kg.link("triple-barrier","atr",RelationType.REQUIRES,"ATR for barrier width")
    kg.link("triple-barrier","dollar-bar",RelationType.REQUIRES,"Bars as input")
    kg.link("triple-barrier","profit-mult",RelationType.CONFIGURED_BY,"Profit barrier mult")
    kg.link("triple-barrier","stop-mult",RelationType.CONFIGURED_BY,"Stop barrier mult")
    kg.link("triple-barrier","horizon-sec",RelationType.CONFIGURED_BY,"Time barrier")
    kg.link("triple-barrier","AFML-Ch3",RelationType.REFERENCES)
    kg.link("triple-barrier","label-distribution",RelationType.PRODUCES,"Generates labels")
    kg.link("triple-barrier","leakage",RelationType.RISK_OF,"If barriers use future info")
    kg.link("meta-labeling","triple-barrier",RelationType.REQUIRES,"Primary labels")
    kg.link("meta-labeling","AFML-Ch3",RelationType.REFERENCES)
    kg.link("meta-labeling","class-imbalance",RelationType.INFLUENCES,"Reduces imbalance")
    kg.link("meta-labeling","sample-weights",RelationType.CONFLICTS_WITH,"Double-counting risk!")
    kg.link("sample-weights","AFML-Ch4",RelationType.REFERENCES)
    kg.link("sample-weights","class-imbalance",RelationType.INFLUENCES,"Weights address imbalance")
    kg.link("sample-weights","leakage",RelationType.RISK_OF,"If uniqueness uses future")
    kg.link("dollar-bar","dollar-bar-threshold",RelationType.CONFIGURED_BY,"Threshold")
    kg.link("dollar-bar","AFML-Ch2",RelationType.REFERENCES)
    kg.link("dollar-bar","training-tick",RelationType.REQUIRES,"Tick data input")
    kg.link("feature-engineering","atr",RelationType.PRODUCES)
    kg.link("feature-engineering","rsi",RelationType.PRODUCES)
    kg.link("feature-engineering","obi-zscore",RelationType.PRODUCES)
    kg.link("feature-engineering","leakage",RelationType.RISK_OF,"Feature window leakage")
    kg.link("walk-forward-cv","AFML-Ch7",RelationType.REFERENCES)
    kg.link("walk-forward-cv","purged-cv",RelationType.IMPLEMENTS,"Purged variant")
    kg.link("walk-forward-cv","leakage",RelationType.VALIDATED_BY,"Purging prevents leakage")
    kg.link("training-tick","exam-tick",RelationType.NEVER_WITH,"MUST NEVER overlap - data leakage!")
    kg.link("profit-mult","label-distribution",RelationType.INFLUENCES,"Higher profit -> fewer long labels")
    kg.link("stop-mult","label-distribution",RelationType.INFLUENCES,"Higher stop -> fewer short labels")
    kg.link("profit-mult","stop-mult",RelationType.CONFLICTS_WITH,"Asymmetric barriers -> label bias! Consider ATR-based")
    kg.link("dollar-bar-threshold","feature-engineering",RelationType.INFLUENCES,"Affects feature window")
    kg.link("n-estimators","overfitting",RelationType.RISK_OF,"Too many trees -> overfit")
    kg.link("learning-rate","overfitting",RelationType.INFLUENCES,"Lower LR -> less overfit")
    kg.link("frac-diff","AFML-Ch4",RelationType.REFERENCES)
    return kg

if __name__ == "__main__":
    print("=" * 60)
    print("KNOWLEDGE GRAPH TOOLS - MegaMemory + yantrikdb + HybridRAG")
    print("=" * 60)
    kg = KnowledgeGraphDB()
    print("\n1. Building scalper knowledge graph...")
    build_scalper_knowledge_graph(kg)
    s = kg.get_stats()
    print(f"   Concepts: {s['concepts']}, Edges: {s['edges']}, Domains: {s['domains']}")
    print("\n2. Detecting contradictions (yantrikdb)...")
    for c in kg.detect_contradictions():
        print(f"   WARNING: {c.concept_a} <-> {c.concept_b}: {c.reason} [sev={c.severity:.1f}]")
    print("\n3. Sequential thinking...")
    t = SequentialThinker(kg)
    r = t.start("Should we use meta-labeling with sample weights?").analyze("Both address imbalance but via different mechanisms. Together = double-counting.",0.85).consider_options([("meta-labeling only",0.80),("sample-weights only",0.70),("both",0.35)]).evaluate("meta-labeling only","Avoids double-counting, simpler",0.80).conclude("Use meta-labeling as primary. Do NOT combine with sample weights.")
    print(f"   Confidence: {r['confidence']:.2f}, Contradictions: {r['contradictions']}")
    print("\n4. Context for 'triple barrier'...")
    comp = ContextCompressor(kg, max_chars=2000)
    print(comp.build_context("triple barrier")[:500])
    print(f"\n5. Trace: meta-labeling -> AFML: {kg.trace_path('meta-labeling','AFML-Ch3')}")
    print(f"\n6. Stats: {kg.get_stats()}")
    kg.close()
    print("\nKnowledge graph tools ready!")
