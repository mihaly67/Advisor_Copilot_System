# Session: graphrag_integrated_20261016
*Időbélyeg: 2026-10-16T20:35:18.370261*

# GraphRAG integráció kész — 2026-10-16

## Microsoft GraphRAG 3.3.0
- pip install graphrag → telepítve (graphrag-core, -cache, -chunking, -common, -input, -llm, -storage, -vectors)
- graspologic-native is telepítve (hierarchikus Leiden clustering)

## Architektúra
GraphRAG pipeline:
1. **Text chunking** → 1200 char, 100 overlap
2. **Entity extraction** → LLM (Qwen2.5-Coder) kinyeri entitásokat
3. **Relationship extraction** → LLM kinyeri relációkat entity-k között
4. **Graph build** → Entity + Relationship gráf
5. **Hierarchical Leiden** → Community detekció (modularity alapú)
6. **Community reports** → LLM összefoglaló community-nként
7. **Embedding** → nomic-embed-text vektorizálás

## Query módok
- **Local search**: Entity-környezet + kapcsolódó relációk (részletes)
- **Global search**: Community-összefoglalók (átfogó)

## Input (36 fájl, 220K)
- knowledge/code_templates/*.py (13)
- knowledge/reference_digests/*.md (14)
- docs/architecture, analysis, master_plan (3)
- mcp/qwen_analysis (v4, labeling, cusum, model_chart) (5)
- README.md (1)

## Konfiguráció
- LLM: qwen2.5-coder-7b-instruct (Ollama)
- Embedding: nomic-embed-text (Ollama)
- Chunk: 1200 char, 100 overlap
- Community: max_cluster_size=10

## Következő lépés
- graphrag index --root . (entity+relation+community gráf építés)
- graphrag query --method local "meta labeling"
- graphrag query --method global "milyen feature-k kellenek a triple barrier-hez?"