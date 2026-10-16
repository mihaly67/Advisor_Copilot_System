# Cline Token-Optimalizálás — Phase 2

> **Dátum:** 2026.09.22. | **Session:** cline_token_opt_phase2_20260922

## Új felfedezések a GitHub docs-ból

### 1. `.clineignore` DEPRECATED lesz!
- Hivatalos helyettesítő: **PreToolUse hook** (`.clinerules/hooks/PreToolUse`)
- A hook **AKTÍVAN BLOKKOLJA** a tool call-t (nem csak szűr, mint az eredeti)
- Forrás: `sdk/examples/hooks/PreToolUse_ClineignoreGuard.sh`
- Működés: `git check-ignore` alapú, jq+git szükséges
- Védi a `.clineignore` fájlt magát is (agent nem módosíthatja)

### 2. SDK Plugin lifecycle hooks
```
beforeRun, afterRun, beforeModel, afterModel, beforeTool, afterTool, onEvent
Hook stages: tool_call_before, tool_call_after, run_start, run_end, error
Hook policies: mode (blocking/async), timeoutMs, retries, failureMode (fail_open/fail_closed)
```

### 3. Community rules (clinerules repó)
- 30+ rule fájl: memory-bank, codebase-onboarding, writing-effective-clinerules, sequential-thinking, temporal-memory-bank, self-iming-cline, stb.
- `writing-effective-clinerules.md` — MUST/SHOULD/MAY/NEVER direktívák
- `memory-bank.md` — hivatalos Memory Bank custom instructions (mermaid diagramokkal)

### 4. Skills progressive loading
- Level 1: Metadata (~100 token) — mindig betölt
- Level 2: Instructions (<5k token) — csak ha triggerelődik
- Level 3: Resources (docs/, templates/, scripts/) — csak ha szükséges

### 5. Auto-Compact
- Prompt cache-t használ → költséghatékony
- Checkpointokkal visszaállítható
- Más modelleknél rule-based truncation (fallback)

## Telepített komponensek

| Komponens | Útvonal | Állapot |
|-----------|---------|---------|
| PreToolUse hook | `.clinerules/hooks/PreToolUse` | ✅ executable |
| memory-bank.md rule | `.clinerules/memory-bank.md` | ✅ |
| codebase-onboarding.md rule | `.clinerules/codebase-onboarding.md` | ✅ |
| productContext.md | `memory-bank/productContext.md` | ✅ |
| .clineignore fejléc | deprecated figyelmeztetés | ✅ |
| VSCode settings | hooks, autoCompact, subagents | ✅ |

## Token megtakarítás becslés
| Funkció | Token megtakarítás |
|---------|-------------------|
| .clineignore (190 sor) | ~150k token |
| PreToolUse hook | +biztonság (aktív blokkolás) |
| Path-based rules (6 fájl) | ~10k token (csak releváns töltődik) |
| Skills (5 db on-demand) | ~20k token (nem mindig aktív) |
| Auto-compact | context határ közelében ~50k |
| **Összesen** | **~230k token fel nem töltött kontextus** |
