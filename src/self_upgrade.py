"""
Self-Upgrade Module — Brain-alapú hatékonyság növelés

Koncepciók beépítése:
1. CRSM: Sparse-Gated Context Injection (prioritizált kontextus)
2. CRSM: Multi-Headed Consensus (többszörös validáció)
3. Yggdrasil: Deep Planning fázisok (init→clarify→explore→evaluate→finalize)
4. trace-wave: Decision Trace (döntés lánc dokumentálás)
5. LightRAG: Entity-Relation keresés (relációs tudás gráf)
"""

import json, time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# ═══════════════════════════════════════════════════════════════
# 1. CRSM: SPARSE-GATED CONTEXT INJECTION
# ═══════════════════════════════════════════════════════════════

class ContextGate(Enum):
    CRITICAL = 1.0    # Data governance, integritás
    HIGH = 0.8        # Pipeline konfig, feature eng
    MEDIUM = 0.5      # Chart, doc
    LOW = 0.2         # Historikus, debug
    IGNORE = 0.0

@dataclass
class ContextItem:
    key: str
    content: str
    gate: ContextGate = ContextGate.MEDIUM
    timestamp: float = 0.0
    ttl_hours: float = 24.0
    
    @property
    def freshness(self) -> float:
        if self.timestamp == 0: return 0.5
        age = (time.time() - self.timestamp) / 3600
        return max(0.0, 1.0 - age / self.ttl_hours)
    
    @property
    def injection_weight(self) -> float:
        return self.gate.value * self.freshness

class ContextPrioritizer:
    def __init__(self, max_tokens: int = 8000):
        self.items: list[ContextItem] = []
        self.max_tokens = max_tokens
    
    def add(self, key, content, gate=ContextGate.MEDIUM, ttl_hours=24.0):
        self.items.append(ContextItem(key=key, content=content, gate=gate,
                                      timestamp=time.time(), ttl_hours=ttl_hours))
    
    def prioritize(self):
        ranked = [(i.key, i.injection_weight) for i in self.items]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
    
    def build_context(self) -> str:
        sorted_items = sorted(self.items, key=lambda x: x.injection_weight, reverse=True)
        parts, total = [], 0
        limit = self.max_tokens * 4
        for item in sorted_items:
            if item.injection_weight < 0.05: continue
            if total + len(item.content) > limit: break
            parts.append(f"## {item.key} [w={item.injection_weight:.2f}]\n{item.content}")
            total += len(item.content)
        return "\n\n".join(parts)

# ═══════════════════════════════════════════════════════════════
# 2. YGGDRASIL: DEEP PLANNING
# ═══════════════════════════════════════════════════════════════

class PlanningPhase(Enum):
    INIT = "init"; CLARIFY = "clarify"; EXPLORE = "explore"
    EVALUATE = "evaluate"; FINALIZE = "finalize"

@dataclass
class PlanStep:
    phase: PlanningPhase
    content: str
    confidence: float = 0.0
    alternatives: list = field(default_factory=list)

class DeepPlanner:
    def __init__(self):
        self.steps = []
        self.current_phase = PlanningPhase.INIT
    
    def init_plan(self, problem):
        self.steps.append(PlanStep(PlanningPhase.INIT, f"PROBLÉMA: {problem}"))
        self.current_phase = PlanningPhase.CLARIFY
        return self
    
    def clarify(self, constraints, assumptions):
        c = f"KORLÁTOK: {constraints}\nFELTÉTELEK: {assumptions}"
        self.steps.append(PlanStep(PlanningPhase.CLARIFY, c))
        self.current_phase = PlanningPhase.EXPLORE
        return self
    
    def explore(self, options):
        so = sorted(options, key=lambda x: x[1], reverse=True)
        c = "LEHETŐSÉGEK:\n" + "\n".join(f"  - {n}: {s:.2f}" for n,s in so)
        self.steps.append(PlanStep(PlanningPhase.EXPLORE, c, alternatives=[n for n,_ in so]))
        self.current_phase = PlanningPhase.EVALUATE
        return self
    
    def evaluate(self, chosen, confidence, reasoning):
        c = f"VÁLASZTÁS: {chosen}\nBIZALOM: {confidence:.2f}\nINDOKLÁS: {reasoning}"
        self.steps.append(PlanStep(PlanningPhase.EVALUATE, c, confidence=confidence))
        self.current_phase = PlanningPhase.FINALIZE
        return self
    
    def finalize(self, actions):
        plan = "# DEEP PLAN\n\n"
        for s in self.steps:
            plan += f"## {s.phase.value.upper()}\n{s.content}\n\n"
        plan += "## AKCIÓ TERV\n" + "\n".join(f"{i}. {a}" for i,a in enumerate(actions,1))
        self.steps.append(PlanStep(PlanningPhase.FINALIZE, f"Akciók: {actions}"))
        return plan
    
    @property
    def has_consensus(self):
        ev = [s for s in self.steps if s.phase == PlanningPhase.EVALUATE]
        return ev[-1].confidence >= 0.6 if ev else False

# ═══════════════════════════════════════════════════════════════
# 3. CRSM: MULTI-HEADED CONSENSUS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Perspective:
    name: str; score: float; reasoning: str

class ConsensusChecker:
    def __init__(self, threshold=0.6, variance_limit=0.3):
        self.threshold = threshold
        self.variance_limit = variance_limit
    
    def check(self, perspectives):
        scores = [p.score for p in perspectives]
        avg = sum(scores) / len(scores)
        var = sum((s - avg)**2 for s in scores) / len(scores)
        std = var ** 0.5
        cons = avg >= self.threshold and std <= self.variance_limit
        penalty = max(0, (std - self.variance_limit) * 2.0)
        return {
            'consensus': cons, 'avg_score': avg, 'std_dev': std,
            'uncertainty_penalty': penalty, 'adjusted_score': max(0, avg - penalty),
            'recommendation': 'PROCEED' if cons else 'CAUTION — nincs konszenzus!'
        }

# ═══════════════════════════════════════════════════════════════
# 4. TRACE-WAVE: DECISION TRACER
# ═══════════════════════════════════════════════════════════════

class DecisionTracer:
    def __init__(self, log_path=None):
        self.trace = []; self.log_path = log_path; self.total_tokens = 0
    
    def trace_decision(self, decision, reasoning, inputs, output, token_cost=0):
        entry = {'ts': time.time(), 'decision': decision, 'reasoning': reasoning,
                 'inputs': inputs, 'output': output, 'tokens': token_cost}
        self.trace.append(entry); self.total_tokens += token_cost
        if self.log_path:
            with open(self.log_path, 'a') as f: f.write(json.dumps(entry, ensure_ascii=False)+'\n')
    
    def summary(self):
        n = len(self.trace)
        return f"Döntések: {n}, Token: {self.total_tokens}" + (f", Átlag: {self.total_tokens/n:.0f}/döntés" if n else "")
    
    def find_expensive(self, top_k=5):
        return sorted(self.trace, key=lambda x: x['tokens'], reverse=True)[:top_k]

# ═══════════════════════════════════════════════════════════════
# 5. LIGHTRAG: ENTITY-RELATION GRAPH
# ═══════════════════════════════════════════════════════════════

@dataclass
class KnowledgeEntity:
    name: str; entity_type: str; properties: dict = field(default_factory=dict)
    relations: list = field(default_factory=list)

class KnowledgeGraph:
    def __init__(self): self.entities = {}
    def add_entity(self, name, etype, **props): self.entities[name] = KnowledgeEntity(name, etype, props)
    def add_relation(self, src, rel, tgt):
        if src in self.entities: self.entities[src].relations.append((rel, tgt))
    def query(self, name, rel=None):
        if name not in self.entities: return []
        if rel: return [t for r,t in self.entities[name].relations if r==rel]
        return [t for _,t in self.entities[name].relations]
    def trace_path(self, start, end, max_depth=5):
        visited, queue = set(), [(start, [start])]
        while queue and max_depth > 0:
            cur, path = queue.pop(0)
            if cur == end: return path
            if cur in visited: continue
            visited.add(cur)
            if cur in self.entities:
                for _,tgt in self.entities[cur].relations:
                    if tgt not in visited: queue.append((tgt, path+[tgt]))
            max_depth -= 1
        return []

def build_scalper_knowledge_graph():
    g = KnowledgeGraph()
    g.add_entity('dollar_bar','method'); g.add_entity('triple_barrier','method')
    g.add_entity('meta_labeling','method'); g.add_entity('sample_weights','method')
    g.add_entity('feature_eng','method'); g.add_entity('walk_forward_cv','method')
    g.add_entity('atr','feature'); g.add_entity('rsi','feature'); g.add_entity('macd','feature')
    g.add_entity('obi_zscore','feature'); g.add_entity('hmm_state','feature')
    g.add_entity('BTCUSD','instrument'); g.add_entity('XAUUSD','instrument')
    g.add_entity('AFML','reference'); g.add_entity('MCTS','concept')
    g.add_relation('dollar_bar','REQUIRES','atr')
    g.add_relation('dollar_bar','USED_BY','BTCUSD')
    g.add_relation('triple_barrier','REQUIRES','atr')
    g.add_relation('triple_barrier','REQUIRES','dollar_bar')
    g.add_relation('triple_barrier','REFERENCES','AFML')
    g.add_relation('meta_labeling','REQUIRES','triple_barrier')
    g.add_relation('meta_labeling','REFERENCES','AFML')
    g.add_relation('sample_weights','REFERENCES','AFML')
    g.add_relation('sample_weights','CONFLICTS_WITH','meta_labeling')
    g.add_relation('feature_eng','PRODUCES','atr')
    g.add_relation('feature_eng','PRODUCES','rsi')
    g.add_relation('feature_eng','PRODUCES','obi_zscore')
    g.add_relation('walk_forward_cv','REQUIRES','triple_barrier')
    return g

if __name__ == '__main__':
    print("=" * 60)
    print("SELF-UPGRADE — Brain-alapú hatékonyság növelés")
    print("=" * 60)
    
    # 1. Context Prioritizer
    print("\n1. CRSM: Sparse-Gated Context Injection")
    cp = ContextPrioritizer(2000)
    cp.add('data_governance','Vizsga adaton tilos tanitani!',ContextGate.CRITICAL,72)
    cp.add('pipeline_config','v4.01, --no-weights',ContextGate.HIGH,48)
    cp.add('chart_template','HTML chart sablon',ContextGate.MEDIUM,24)
    cp.add('debug_log','Regi debug',ContextGate.LOW,6)
    for k,w in cp.prioritize(): print(f"  {k}: {w:.3f}")
    
    # 2. Deep Planner
    print("\n2. Yggdrasil: Deep Planning")
    p = DeepPlanner()
    plan = p.init_plan("Retrain 2.5 month data").clarify(['Only data/raw/'],['GPU OK']).explore([('v4.01 no-weights',0.85),('baseline',0.60),('with weights',0.40)]).evaluate('v4.01 no-weights',0.85,'AUC best').finalize(['python3 scalper_copilot_v4_01.py --no-weights','Eval on exam','Charts'])
    print(f"  Konszenzus: {p.has_consensus}")
    
    # 3. Consensus
    print("\n3. CRSM: Multi-Headed Consensus")
    cc = ConsensusChecker()
    r = cc.check([Perspective('data',0.85,'AUC jo'),Perspective('risk',0.70,'OK'),Perspective('domain',0.90,'Helyes')])
    print(f"  Konszenzus: {r['consensus']}, Avg: {r['avg_score']:.2f}, Rec: {r['recommendation']}")
    
    # 4. Tracer
    print("\n4. trace-wave: Decision Tracer")
    t = DecisionTracer()
    t.trace_decision('gov_fix','Vizsga=OOS',['exam CSV'],'Pipeline atirva',150)
    print(f"  {t.summary()}")
    
    # 5. Knowledge Graph
    print("\n5. LightRAG: Knowledge Graph")
    kg = build_scalper_knowledge_graph()
    print(f"  triple_barrier REQUIRES: {kg.query('triple_barrier','REQUIRES')}")
    print(f"  sample_weights CONFLICTS: {kg.query('sample_weights','CONFLICTS_WITH')}")
    print(f"  meta_labeling -> AFML: {kg.trace_path('meta_labeling','AFML')}")
    
    print("\n✅ Self-upgrade keszen!")
