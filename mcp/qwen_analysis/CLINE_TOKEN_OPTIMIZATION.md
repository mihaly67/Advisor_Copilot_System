# CLINE TOKEN-OPTIMALIZÁCIÓ — ÖSSZEGZÉS

**Dátum:** 2026.09.22.
**Cél:** Cline token-égetés csökkentése + szoftverfejlesztői környezet kialakítása Brain RAG-gal

---

## 6 OPTIMALIZÁLÓ RÉTEG IMPLEMENTÁLVA

| Réteg | Fájlok | Token megtakarítás |
|---|---|---|
| `.clineignore` bővítés | 190 sor, 65+ új minta | ~150k token a kezdő kontextusból |
| `.clinerules/` path-based | 4 fájl (universal, ml-python, mql5, typescript) | ~3-5k token (csak releváns) |
| `.cline/skills/` on-demand | 5 skill (rag-search, ml-training, mt5-ea, hud-dev, mcp-session) | ~500 token metadata, <5k ha triggerelődik |
| `memory-bank/` strukturált | 5 fájl (brief, active, patterns, tech, progress) | Külső memória, 0 kontextus token |
| VSCode settings | auto-approve read, diff enabled, max 20 reads | Kevesebb prompt, kevesebb retry |
| Auto-compact (beépített) | Cline natív | Végtelen context (összefoglalás) |

---

## FÁJL STRUKTÚRA

```
/home/Jules/zhipu_projekt/
├── .clinerules/          # PATH-BASED (csak releváns töltődik)
│   ├── universal.md      # mindig aktív (~30 sor)
│   ├── ml-python.md      # **/*.py esetén
│   ├── mql5.md           # **/*.mq5 esetén
│   └── typescript.md     # **/*.ts esetén
├── .clineignore          # 190 sor szűrés
├── .cline/skills/        # ON-DEMAND (~100 token metadata)
│   ├── rag-search/       # RAG v4 keresés
│   ├── ml-training/      # LGBM/CNN pipeline
│   ├── mt5-ea/           # MQL5 EA + ZMQ
│   ├── hud-dev/          # PyQt5 HUD
│   └── mcp-session/      # MCP memória
├── memory-bank/          # STRUKTURÁLT TUDÁS
│   ├── projectBrief.md
│   ├── activeContext.md   # sliding window 10
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
└── agents.md             # cross-tool kompatibilitás
```

---

## KUTATÁSI FORRÁSOK (github.com/cline)
- `cline/cline` (69k stars) — fő SDK/extension
- `cline/clinerules` — közösségi szabályok
- `docs/features/auto-compact.mdx` — context összefoglalás
- `docs/customization/cline-rules.mdx` — path-based rules
- `docs/customization/clineignore.mdx` — fájl szűrés
- `docs/customization/skills.mdx` — on-demand skills
- `docs/features/subagents.mdx` — párhuzamos kutatás

---

*Mentve: /data/Brain/_qwen_analysis/CLINE_TOKEN_OPTIMIZATION.md*