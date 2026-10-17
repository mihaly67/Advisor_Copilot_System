# Session: kg_tools_integration
*Időbélyeg: 2026-10-16T22:22:39.238815*

## Knowledge Graph Tools Integration — 2026-10-16

### Létrehozott fájlok
1. `/data/mcp_server/tools/knowledge_graph_tools.py` (20KB) — fő modul
2. `/data/mcp_server/data/knowledge_graph.db` (53KB) — SQLite adatbázis

### Szerkezet (MegaMemory + yantrikdb + HybridRAG inspiráció)
- **KnowledgeGraphDB** — SQLite WAL mode, concepts/edges/contradictions/thinking_sessions táblák
  - NodeKind: feature|module|pattern|config|decision|parameter|method|instrument|reference|concept|data
  - RelationType: depends_on|conflicts_with|influences|requires|references|configured_by|validated_by|implements|produces|used_by|risk_of|never_with
  - CRUD: create_concept, get_concept, update_concept, remove_concept, list_roots, search_concepts
  - link, detect_contradictions, resolve_contradiction, apply_decay, trace_path, get_stats
- **SequentialThinker** — többlépéses gondolkodás (start→analyze→consider_options→evaluate→conclude)
- **ContextCompressor** — token-optimalizált kontextus összeállítás (importance × relevance)
- **build_scalper_knowledge_graph()** — 25+ entity, 35+ reláció

### Kontradikciók (yantrikdb minta)
1. meta-labeling ↔ sample-weights (explicit CONFLICTS_WITH — double-counting risk)
2. profit-mult ↔ stop-mult (explicit CONFLICTS_WITH — asymmetric barriers → label bias)
3. training-tick ↔ exam-tick (NEVER_WITH — data leakage!)
4. Implicit: profit-mult és stop-mult both influence label-distribution in "financial"

### MCP server kiegészítés
- Új tool: `knowledge_graph(action, concept_id, query, name, kind, summary, domain, from_id, to_id, relation, description, top_k)`
- 10 action: stats|get|search|create|link|contradictions|trace|context|decay|rebuild
- server.py frissítve: tool definíció, dispatch, @server.tool dekorátor

### self_upgrade.py frissítés
- 5. szakasz: MegaMemory + yantrikdb gráf (korábban: LightRAG in-memory)
- Docstring: 9 koncepció + 5 Brain repo inspiráció

### Következő lépések
1. MCP server restart hogy a knowledge_graph tool éljen
2. self_upgrade.py tesztelés (import path beállítása)
3. cortexdb Go modul integráció (shared-brain gRPC server)
4. yantrikdb Python binding telepítés (pip install yantrikdb)
5. HybridRAG vector+graph hybrid retrieval implementáció
