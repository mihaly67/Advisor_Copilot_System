# Session: MCP szerver MCPServer API migráció + élő teszt SIKER

*Időbélyeg: 2026-09-18 13:39*

## Probléma: elavult MCP API
A `/data/mcp_server/server.py` eredetileg a régi `mcp.server.Server` API-t használta
(`@server.list_tools()` és `@server.call_tool()` dekorátorok). A telepített `mcp 2.2.0`
SDK-ban azonban a FastMCP-et átnevezték `MCPServer`-re (`from mcp.server.mcpserver import MCPServer`),
és a `Server.list_tools` / `Server.call_tool` dekorátorok eltűntek.

**Hibaüzenet**: `AttributeError: 'Server' object has no attribute 'list_tools'`

## Megoldás: MCPServer dekorátoros API
A `serve()` függvényt átírtuk az MCPServer API-ra. Mind a 6 tool-t külön wrapper
függvényként regisztráljuk a `@server.tool(name=..., description=...)` dekorátorral.
A wrapper-ek meghívják a meglévő `dispatch_tool()` routing-ot (ami érintetlen maradt).
Az inputSchema-t az MCPServer a függvény típusjegyzeteiből generálja.

## Változtatások a server.py-ban
1. **Import**: `from mcp.server.mcpserver import MCPServer` a `from mcp.server import Server`
   helyett. Az `stdio_server` és `mcp_stdio` import eltávolítva (nem kell az MCPServer-hez).
2. **serve()**: `MCPServer("qwen-mcp-server", instructions=...)` létrehozása, 6 `@server.tool()`
   dekorátor wrapper függvénnyel, `await server.run_stdio_async()` a futtatáshoz.
3. A `get_tool_definitions()` és `dispatch_tool()` érintetlen (a wrapper-ek csak hívnak rá).

## Élő tesztek (2026-09-18 13:38-13:40) - MIND SIKERES

### 1. Handshake (initialize + tools/list)
- `initialize` válasz: `{'name': 'qwen-mcp-server', 'version': ''}` ✅
- `tools/list`: 6 tool listázva ✅
  - list_gpu, read_repo, write_log, analyze_with_qwen, store_session, read_session

### 2. Tool hívások (tools/call) stdio transporton
- `read_session(stage="")` → 721 karakter válasz (session index) ✅
- `list_gpu()` → 256 karakter válasz (P4000 + P2000 állapot) ✅

### 3. Direkt dispatch_tool tesztek (MCP nélkül)
- `read_session("")` → index ✅
- `list_gpu()` → GPU állapot ✅
- `read_session("gpu_setup")` → session markdown ✅
- `read_repo("/data/Brain")` → 83 bejegyzés listázása ✅

## Qwen repó-elemzések (P4000 GPU, élő futtatás)
Három elemzés készült, mindegyik Markdown fájlba írva a célkönyvtár `_qwen_analysis/` almappájába:

| Könyvtár | Időbélyeg | Generálási idő | Karakterek | Modell betöltés |
|---|---|---|---|---|
| `/data/Brain/Qwen-Agent` | 13:29:41 | 24.0s | 995 | 2.2s |
| `/home/Jules/RAG_epito_ismeretek` | 13:30:24 | 23.5s | 1013 | 1.5s |
| `/data/Brain` | 13:31:10 | 26.2s | 1180 | 1.5s |

**VRAM**: 0 MB maradandó (a modell `gpu_cache_tisztítva` után felszabadul)
**Intelligens lock**: a `/data/Brain` első próbálkozását elutasította, mert a
`/home/Jules/RAG_epito_ismeretek` elemzés még futott (PID-alapú lock + stale detection)

## GPU állapot az élő tesztek után
```
GPU 0: Quadro P4000 | VRAM: 8 MiB/8192 MiB (szabad: 8100 MiB) | kihasználás: 0 %
GPU 1: Quadro P2000 | VRAM: 765 MiB/5120 MiB (szabad: 4280 MiB) | kihasználás: 29 %
```
A P4000 teljesen szabad (a Qwen cache-t felszabadítja minden futás után).
A P2000 más folyamatok által használt (nem a Qwen).

## Készen álló komponensek
- ✅ `/data/mcp_qwen_setup.sh` - végleges környezeti beállító (GPU izoláció, HF cache,
  LD_LIBRARY_PATH, venv, verifikáció)
- ✅ `/data/mcp_server/server.py` - MCP szerver (MCPServer API, 6 tool, stdio transport)
- ✅ `/data/mcp_server/tools/qwen_analyzer.py` - Qwen2.5-Coder wrapper (intelligens lock,
  timeout guard, file discovery, Markdown report)
- ✅ `/data/mcp_server/state/` - 3 session-tudás fájl + index (memória az MCP fölött)
- ✅ `/data/mcp_server/logs/` - qwen_analyzer.log + mcp_server.log

## Indítás (felhasználó részéről)
```bash
source /data/mcp_qwen_setup.sh          # környezet aktiválása (verifikációval)
python3 /data/mcp_server/server.py       # MCP szerver (stdio transport, klienshez)
```
vagy egy lépésben:
```bash
source /data/mcp_qwen_setup.sh && python3 /data/mcp_server/server.py
```

Qwen repó-elemzés önállóan (MCP nélkül):
```bash
source /data/mcp_qwen_setup.sh
python3 /data/mcp_server/tools/qwen_analyzer.py /data/Brain/Qwen-Agent
```
