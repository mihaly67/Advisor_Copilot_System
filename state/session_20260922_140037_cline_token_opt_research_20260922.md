# Session: cline_token_opt_research_20260922
*Időbélyeg: 2026-09-22T14:00:37.213300*

# CLINE TOKEN OPTIMALIZÁCIÓ — KUTATÁSI EREDMÉNYEK

## KUTATÁS FORRÁSA: github.com/cline/cline + github.com/cline/clinerules

## 6 TOKEN-OPTIMALIZÁLÓ FUNKCIÓ TALÁLVA:

### 1. AUTO-COMPACT (docs/features/auto-compact.mdx)
- Automatikus kontextus összefoglalás amikor a context window közelít a határhoz
- Minden technikai részletet, kódot, döntést megőriz
- Prompt cache-t használ → költséghatékony (csak output tokeneket fizetsz)
- Checkpoint-okkal visszaállítható
- Más modelleknél rule-based truncation fallback

### 2. .CLINERULES (docs/customization/cline-rules.mdx)
- `.clinerules/` könyvtár workspace-ben
- Frontmatter: `paths:` glob minták → csak releváns fájloknál töltődik
- Token takarékosság: csak az releváns szabályok töltődnek be
- Támogatja: .cursorrules, .windsurfrules, AGENTS.md formátumokat is

### 3. .CLINEIGNORE (docs/customization/clineignore.mdx) — DEPRECATED de használható
- .gitignore szerű szintaxis
- Kizárja: node_modules, venv, __pycache__, nagy fájlok
- 200k+ token → 50k tokenre csökkentheti a kezdő kontextust
- PreToolUse hook-kal erősíthető (blokkolja az olvasást)

### 4. SKILLS (docs/customization/skills.mdx)
- Progresszív betöltés:
  - Metadata: mindig betöltve (~100 token/skill)
  - Instructions: csak ha triggerelődik (<5k token)
  - Resources: csak ha kell
- `.cline/skills/` könyvtárban SKILL.md fájlok

### 5. SUBAGENTS (docs/features/subagents.mdx) — EXPERIMENTAL
- Párhuzamos kutató ágensek, saját context window-val
- Csak olvasás (read_file, search, list, read-only commands)
- Token budget külön számlázva
- Alapból bekapcsolva

### 6. MEMORY BANK (clinerules/memory-bank.md + temporal-memory-bank.md)
- Strukturált projekt tudás: projectBrief.md, productContext.md, activeContext.md, systemPatterns.md, techContext.md, progress.md
- Sliding window: 10 legutóbbi esemény
- Changelog.md időrendi napló

## JELENLEGI ÁLLAPOT (lokális):
- `.clinerules` megvan (74 sor, egyetlen fájl, NEM path-based)
- `.clineignore` megvan (alapvető minták)
- Nincs `.cline/` könyvtár (skills)
- Nincs `memory-bank/` könyvtár
- MCP: `qwen-local` beállítva
- Nincs Cline VSCode settings
- Task history: 1 task ("szia")

## Cline org repos (30 db):
- cline (69k stars) — fő SDK/extension
- clinerules — közösségi szabályok (21 stars)
- prompts — prompt könyvtár (1.2k stars)
- mcp-marketplace — MCP szerver piactér (787 stars)
- plugins — hivatalos pluginok
- kanban — párhuzamos CLI ágensek
- harbor — értékelési framework
- benchmark-results, cline-bench — benchmarkok