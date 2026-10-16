# VSCode + Cline + MCP Környezet

## Telepített VSCode kiegészítők

| Kiegészítő | Verzió | Funkció |
|-----------|--------|---------|
| **saoudrizwan.claude-dev** | 4.1.23 | **Cline** — AI coding agent (ez maga a Cline!) |
| ms-python.python | 2026.8.0 | Python nyelv támogatás |
| ms-python.vscode-pylance | 2026.4.1 | Python type checker + IntelliSense |
| ms-python.debugpy | 2026.6.0 | Python debugger |
| ms-python.vscode-python-envs | 1.38.0 | Python environment management |
| ms-python.black-formatter | 2026.6.0 | **ÚJ** — Black formázó |
| ms-python.isort | 2026.6.0 | **ÚJ** — Import rendezés |
| ms-vscode.cpptools | 1.34.4 | C/C++ IntelliSense + debug |
| ms-vscode.cpptools-extension-pack | 1.5.1 | C/C++ csomag |
| ms-vscode.cpptools-themes | 2.0.0 | C/C++ témák |
| ms-vscode.cpp-devtools | 0.6.18 | C/C++ dev tools |
| ms-vscode.cmake-tools | 1.24.42 | CMake build |
| ms-vscode.makefile-tools | 0.12.17 | Makefile support |
| eamodio.gitlens | 19.3.0 | **ÚJ** — Git supercharge |
| redhat.vscode-yaml | 1.25.0 | **ÚJ** — YAML support |
| tamasfe.even-better-toml | 0.21.2 | **ÚJ** — TOML support |
| ms-azuretools.vscode-containers | 2.5.2 | Docker containers |

## Cline MCP Konfig

**Fájl**: `/home/Jules/.cline/mcp.json` és `/home/Jules/.cline/data/settings/cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "qwen-mcp-server": {
      "command": "/data/mcp_server/venv/bin/python3",
      "args": ["/data/mcp_server/server.py"],
      "env": {
        "CUDA_VISIBLE_DEVICES": "0",
        "HF_HOME": "/data/ml/hf_cache",
        "MCP_SERVER_DIR": "/data/mcp_server"
      },
      "autoApprove": [
        "list_gpu",
        "read_repo",
        "read_session",
        "repository_memory_indexer",
        "rag_query"
      ]
    }
  }
}
```

## MCP Tool-ok (qwen-mcp-server)

| Tool | Auto-approve | Funkció |
|------|-------------|---------|
| list_gpu | ✅ | GPU állapot lekérdezés |
| read_repo | ✅ | Biztonságos fájl/könyvtár olvasás |
| write_log | ❌ | Napló/kivonat írás |
| analyze_with_qwen | ❌ | Qwen GPU elemzés indítás |
| store_session | ❌ | Session tudás mentés |
| read_session | ✅ | Session tudás visszolvasás |
| repository_memory_indexer | ✅ | Repository kód indexelés |
| **rag_query** | ✅ **ÚJ** | RAG keresés (concept + keyword) |

## rag_query MCP Tool

```python
# Koncept navigáció (Level 1)
rag_query(query="triple_barrier", mode="concept")
rag_query(query="meta_labeling", mode="concept")

# ML DB keresés (Level 4 — 333K chunk)
rag_query(query="CUSUM filter", mode="keyword", db="ml", top_k=5)

# Brain DB keresés (Level 4 — 247K chunk)
rag_query(query="LightRAG mcp", mode="keyword", db="brain", top_k=5)
```

## VSCode Settings (fontosabbak)

- `cline.autoApprove.read: true` — auto-approve olvasás
- `cline.diffEnabled: true` — diff-based editing (token takarékosság)
- `cline.autoCompact: true` — auto context kompaktálás
- `python.defaultInterpreterPath` — Python venv
- `C_Cpp.intelliSenseEngine: default` — C++ IntelliSense
- `terminal.integrated.env.linux.CUDA_VISIBLE_DEVICES: "0"` — GPU a terminálban
- `files.autoSave: afterDelay` — auto-save 1s után

## Cline Auto-approve (MINDEN true)

```json
"cline.autoApprove": {
    "read": true,
    "readFile": true,
    "listDirectory": true,
    "searchCodebase": true,
    "runCommands": true,
    "editFile": true,
    "createFile": true
}
"cline.autoApprove.subagents": true,
"cline.autoApprove.executeReadOnlyCommands": true,
"cline.alwaysAllowReadOnly": true,
"cline.maxFileReadsPerTask": 50
```

→ **Nincs emberi jóváhagyás** — Cline mindent auto-approveol.

## Git Config

```
[user] name = Jules, email = jules@dev.local
[core] editor = code --wait, autocrlf = input
[init] defaultBranch = main
[pull] rebase = true
[push] autoSetupRemote = true
```

## File Permissions

- `/data/Brain/_qwen_analysis/` — writable
- `/data/mcp_server/state/` — writable
- `/data/mcp_server/logs/` — writable
- `/data/mcp_server/context/` — writable

- Plan mode: **zhipuai** (GLM-4.5)
- Act mode: **zhipuai** (GLM-4.5)
- API: ZhipuAI endpoint

## Cron plugin-ek

- changelog-generator, code-style-audit, dead-code-finder
- dependency-check, documentation-check, test-coverage-report
- type-check-strict
