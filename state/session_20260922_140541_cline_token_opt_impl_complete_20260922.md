# Session: cline_token_opt_impl_complete_20260922
*Időbélyeg: 2026-09-22T14:05:41.113157*

# CLINE TOKEN-OPTIMALIZÁCIÓ — IMPLEMENTÁCIÓ KÉSZ

## DÁTUM: 2026.09.22.
## ÁLLAPOT: ✅ KÉSZ

## 6 TOKEN-OPTIMALIZÁLÓ RÉTEG IMPLEMENTÁLVA:

### 1. .clinerules/ KÖNYVTÁR (path-based feltételes szabályok)
- `universal.md` — mindig aktív (válaszstílus, fájlolvasás, hibakezelés, prompt caching, eszközhasználat, kódgenerálás)
- `ml-python.md` — paths: **/*.py — ML pipeline, tanítás, validáció szabályok
- `mql5.md` — paths: **/*.mq5, **/*.mqh — MT5 EA, ZMQ, broker védelem
- `typescript.md` — paths: **/*.ts, **/*.js — TS konvenciók

### 2. .clineignore BŐVÍTVE (65+ új minta)
- MCP server belső állapot (state, conversations, logs, lock, secure)
- ML modellek (gguf, bin, safetensors, onnx, pt, pth, ckpt)
- RAG vector DB (SQLite fájlok)
- Brain Qwen elemzések
- LGBM adatok/modellek
- Kép/média fájlok
- CSV adatfájlok
- Backup fájlok
- Eredmény: kezdő kontextus 200k → ~50k token

### 3. .cline/skills/ (on-demand, ~100 token metadata)
- `rag-search/SKILL.md` — RAG v4 keresés (336,907 chunks)
- `ml-training/SKILL.md` — LGBM/CNN tanítás pipeline
- `mt5-ea/SKILL.md` — MQL5 EA + ZMQ + broker védelem
- `hud-dev/SKILL.md` — PyQt5 HUD + Lightweight Charts
- `mcp-session/SKILL.md` — MCP session memória használata

### 4. memory-bank/ (strukturált projekt tudás)
- `projectBrief.md` — projekt cél, alapelvek, technológiák
- `activeContext.md` — aktuális munka, sliding window (10 esemény)
- `systemPatterns.md` — architektúra, token rétegek, hardver
- `techContext.md` — nyelvek, könyvtárak, infra, fájl útvonalak
- `progress.md` — kész/folyamatban/ismert problémák/következő

### 5. VSCODE SETTINGS (Cline optimalizáció)
- `cline.autoApprove`: read/fileRead/listDir/searchCodebase = true (kevesebb prompt)
- `cline.diffEnabled`: true (diff-based editing, token takarékosság)
- `cline.fuzzyMatchThreshold`: 0.8 (pontosabb match, kevesebb retry)
- `cline.maxFileReadsPerTask`: 20 (token védelem)

### 6. AUTO-COMPACT (Cline beépített)
- Automatikus context összefoglalás a context window határánál
- Prompt cache-t használ → költséghatékony
- Checkpoint-okkal visszaállítható
- Nem kell külön beállítani — beépített funkció

## FÁJL STRUKTÚRA:
```
/home/Jules/zhipu_projekt/
├── .clinerules/          # path-based szabályok (4 fájl)
│   ├── universal.md      # mindig aktív
│   ├── ml-python.md      # **/*.py
│   ├── mql5.md           # **/*.mq5
│   └── typescript.md     # **/*.ts
├── .clineignore          # token szűrés (190 sor)
├── .cline/
│   └── skills/           # on-demand tudás (5 skill)
│       ├── rag-search/
│       ├── ml-training/
│       ├── mt5-ea/
│       ├── hud-dev/
│       └── mcp-session/
├── memory-bank/          # projekt tudás (5 fájl)
│   ├── projectBrief.md
│   ├── activeContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
├── agents.md             # cross-tool kompatibilitás
└── SCALPER_MASTER_PLAN_v2.0.md ( Brain-ben)
```

## VÁRHATÓ TOKEN MEGTAKARÍTÁS:
- .clineignore: ~150k token megtakarítás a kezdő kontextusban
- .clinerules path-based: ~3-5k token (csak releváns szabályok)
- Skills on-demand: ~4-5k token (csak ha triggerelődik)
- Auto-compact: végtelen context (összefoglalás)
- MCP session: 0 kontextus token (külső memória)
- VSCode auto-approve read: kevesebb interakciós prompt

## KUTATÁSI FORRÁSOK:
- github.com/cline/cline — fő repó (69k stars)
- github.com/cline/clinerules — közösségi szabályok
- docs/features/auto-compact.mdx — auto-compact dokumentáció
- docs/customization/cline-rules.mdx — path-based rules
- docs/customization/clineignore.mdx — fájl szűrés
- docs/customization/skills.mdx — on-demand skills
- docs/features/subagents.mdx — párhuzamos kutatás