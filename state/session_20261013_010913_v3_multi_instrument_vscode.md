# Session: v3_multi_instrument_vscode
*Időbélyeg: 2026-10-13T01:09:13.667487*

## v3.0 — Multi-instrument + VSCode/MCP integration

### Multi-instrument
- concept_map.json: `market_specifics` → `instruments` dict
- BTCUSD: 500K USD bar, TP=2σ, SL=2σ, VB=50 bars
- XAUUSD: 5M USD bar, TP=2.5σ, SL=1.5σ, VB=100 bars (gold wider TP, tighter SL)
- AGENTS.md: "SOHA ne hardcode-olj instrument paramétereket!"
- New instrument: csak új key a concept_map `instruments` dict-be

### VSCode tooling
- Installed 5 new extensions: black-formatter, isort, GitLens, YAML, TOML
- Total extensions: 17 (Python pack, C/C++ pack, Cline, Docker, GitLens, formatters)
- VSCode settings updated: Python venv, C/C++ IntelliSense, auto-save, CUDA env, format-on-save
- Cline MCP: rag_query added to autoApprove list

### MCP rag_query tool
- mode='concept': concept_map.json navigation
- mode='keyword', db='ml': ml_rag_v2.db (333K chunks)
- mode='keyword', db='brain': brain_rag.db (247K chunks)
- All tested and working

### Full environment documented
- vscode_mcp_environment.md: complete inventory of extensions, MCP config, tools, cron plugins