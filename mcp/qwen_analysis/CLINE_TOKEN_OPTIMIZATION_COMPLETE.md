# Cline Token-Optimalizálás — Teljes GitHub Kutatás

> **Dátum:** 2026.09.22. | Phase 1+2+3

## Cline GitHub Ökoszisztéma (30 repó)

| Repo | Stars | Funkció |
|------|-------|---------|
| **cline/cline** | 69k | Fő SDK + VSCode extension + CLI |
| **cline/kanban** | 1.3k | CLI agents párhuzamos futtatás |
| **cline/prompts** | 1.2k | Community rules + workflows (30+ fájl) |
| **cline/mcp-marketplace** | 787 | MCP szerver katalógus |
| **cline/plugins** | 31 | 16 hivatalos plugin |
| **cline/marketplace** | 7 | Curated primitives (plugins, skills, MCP) |
| **cline/cline-bench** | 38 | Real-world coding benchmarks |
| **cline/linear-mcp** | 134 | Linear MCP szerver |

## Cline Plugins (16 db hivatalos)

| Plugin | Funkció | Token-opt? |
|--------|---------|-----------|
| **env-blocker** | Blokkolja .env olvasást (beforeTool hook) | ✅ |
| **gitignore-read-files-guard** | Blokkolja .gitignore-ban lévő fájlokat | ✅ |
| **custom-compaction** | Egyedi context compaction (preserve first msg + recent) | ✅ |
| **agents-squad** | Background subagents with presets + handoffs | ✅ |
| **branch-protector** | Blokkolja protected branch push-t | — |
| **background-terminal** | Hosszan futó shell jobok polling-gal | — |
| **bundled-skills-demo** | Bundled skill discovery demo | — |
| **clickhouse-data-analyst** | ClickHouse skill | — |
| **goal** | Completion nudges aktív goal-okhoz | — |
| **intercom-support-triage-slack** | Intercom triage tools | — |
| **jev-browser** | Browser automation Vercel AI Gateway | — |
| **linear** | Linear SDK scripting skill | — |
| **mac-notify** | macOS notifications run complete | — |
| **nanobanana** | Képgenerálás OpenRouter + Gemini | — |
| **speak** | ElevenLabs TTS | — |
| **typescript-lsp** | TypeScript goto_definition | — |
| **weather-metrics** | Demo weather tool + runtime metrics hooks | — |
| **web-search** | Exa web search tool | ✅ |

## SDK Examples (hooks + cron + plugins)

### Hook Lifecycle Stages
```
beforeRun, afterRun, beforeModel, afterModel, beforeTool, afterTool, onEvent
Stages: session_start, run_start, iteration_start, turn_start, before_agent_start,
        tool_call_before, tool_call_after, turn_end, stop_error, iteration_end,
        run_end, session_shutdown, error
```

### Hook Files
- `PreToolUse` (bash/Python/TS) — blokkol tool call-t
- `PostToolUse` — logol results, trigger side effects
- `TaskStart` / `TaskComplete` / `SessionShutdown`

### Cron Jobs (`.cline/cron/`)
- changelog-generator, dependency-check, test-coverage-report, performance-baseline
- type-check-strict, code-style-audit, dead-code-finder, documentation-check
- Event-driven: pr-changelog-check, pr-test-coverage

## Community Rules (clinerules/prompts repo)

| Rule | Funkció |
|------|---------|
| memory-bank.md | Hivatalos Memory Bank custom instructions |
| **temporal-memory-bank.md** | Time-aware: sliding window 10 + changelog.md |
| **self-improving-cline.md** | Reflection before attempt_completion |
| **continuous-improvement-protocol.md** | raw_reflection_log + consolidated_learnings |
| codebase-onboarding.md | Token-takarékos kódbázis felfedezés |
| writing-effective-clinerules.md | MUST/SHOULD/MAY/NEVER direktívák |
| sequential-thinking.md | sequentialthinking MCP tool guide |
| cline-architecture.md | Architektúra elemzés |
| cline-for-research.md | Kutatási workflow |
| mermaid-plans.md | Mermaid diagram tervezés |
| testing-strategy.md | Tesztelési stratégiák |
| security-audit.md | Biztonsági audit |
| new-task-automation.md | Task automatizálás |

## Discussion Insight-ok

| Téma | Érték |
|------|-------|
| "Is it just me or Cline became more expensive?" | 14 szavazat — költség probléma |
| "Add Cheaper Inference as built-in provider" | 11 szavazat — olcsóbb modellek |
| "DO NOT INSTALL AFTER 4.1.8 — money burners" | Figyelmeztetés verziókra |
| "Best practices for local Ollama + Cline" | Token limit + timeout tippek |
| "Unreliable token count for Qwen3.5 + llama.cpp" | Token számlálási probléma |
| "Complementary PreToolUse reliability gates" | Hook megbízhatóság |
| "Square Root Boundary for Context Compression" | Context compression optimalizálás |
| "Secret-masking proxy (AI Firewall)" | Secret masking proxy |

## Kulcs Issue-k

| # | Cím | Jelentőség |
|---|-----|-----------|
| #14393 | OpenAI Codex 400K context cap | Context limit probléma |
| #14378 | recover from max-tokens turns | Output budget scaling |
| #14371 | summarize with current credentials during compaction | Compaction fix |
| #14355 | enable core auto-compaction for desktop | Auto-compact desktop |
| #14377 | guard checkpoint restore from dirty gitignore rules | Checkpoint + gitignore |

## Implementált Eredmények

### .clinerules/ (8 fájl)
1. universal.md — mindig aktív token-opt szabályok
2. ml-python.md — Python ML path-based (`**/*.py`)
3. mql5.md — MQL5 path-based (`**/*.mq5`)
4. typescript.md — TypeScript path-based (`**/*.ts`)
5. memory-bank.md — Memory Bank custom instructions
6. codebase-onboarding.md — token-takarékos onboarding
7. self-improving.md — reflection process
8. continuous-improvement.md — tudásrögzítés protokoll

### .clinerules/hooks/
- PreToolUse — .clineignore guard (170 sor, executable)

### memory-bank/ (9 fájl)
1. projectBrief.md
2. productContext.md
3. activeContext.md
4. systemPatterns.md
5. techContext.md
6. progress.md
7. changelog.md — időrendi változásnapló
8. raw_reflection_log.md — részletes tanulságok
9. consolidated_learnings.md — finomított insightok

### .cline/skills/ (5 skill)
- rag-search, ml-training, mt5-ea, hud-dev, mcp-session

### VSCode settings
- enableHooks, autoCompact, autoApprove (read, subagents, readOnlyCommands)
- diffEnabled, fuzzyMatchThreshold=0.8, maxFileReadsPerTask=20

### Token megtakarítás becsülés
| Funkció | ~Token |
|---------|--------|
| .clineignore (195 sor) | ~150k |
| Path-based rules (8 fájl) | ~15k |
| Skills (5 db on-demand) | ~20k |
| Auto-compact | ~50k |
| PreToolUse hook (aktív blokkolás) | biztonság |
| **Összesen** | **~235k fel nem töltött kontextus** |