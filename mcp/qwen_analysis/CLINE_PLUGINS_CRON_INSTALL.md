# Cline CLI + Plugins + Cron Jobs — Telepítési Jegyzőkönyv

> **Dátum:** 2026.09.22. 15:05

## Rendszerkövetelmények
- **Node.js:** v22.23.2 (NodeSource repo, korábban v18 → frissítve)
- **npm:** 10.9.8
- **Cline CLI:** v3.0.64
- **OS:** Linux (Debian 12), sudo passwordless (jelszó 1104)

## Telepített Plugins (4 db)

| Plugin | Útvonal | Funkció |
|--------|---------|---------|
| **custom-compaction** | `~/.cline/plugins/_installed/official/custom-compaction-5b627110f9dd` | Context compaction: preserve first user msg + recent 24k tokens, summarize middle history |
| **agents-squad** | `~/.cline/plugins/_installed/official/agents-squad-1ae2facb94f9` | Background subagents: start/list/message/poll, presets, handoff store |
| **web-search** | `~/.cline/plugins/_installed/official/web-search-c2569026205b` | Exa-backed web search Cline tool |
| **background-terminal** | `~/.cline/plugins/_installed/official/background-terminal-6c6f0b95621b` | Long-running shell jobs with polling + cleanup |

## Telepített Cron Jobs (7 db)

| Cron Job | Ütemezés | Funkció |
|----------|----------|---------|
| **changelog-generator** | Péntek 18:00 | Auto-generate changelog from commits → memory-bank/changelog.md |
| **dependency-check** | Hétfő 10:00 | npm outdated + npm audit + security vulnerabilities |
| **test-coverage-report** | (cron) | Daily coverage metrics |
| **type-check-strict** | (cron) | TypeScript type safety audits |
| **code-style-audit** | (cron) | Linting and formatting checks |
| **dead-code-finder** | (cron) | Identify unused code |
| **documentation-check** | (cron) | API documentation coverage |

### Cron Konfiguráció
- workspaceRoot: `/home/Jules/zhipu_projekt`
- enabled: true (minden cron job)
- mode: act
- tools: run_commands, read_files, editor

## custom-compaction Plugin Működése
```
MAX_INPUT_TOKENS = 120,000
COMPACT_AT_RATIO = 0.75 (→ 90k token-nél indul)
PRESERVE_RECENT_TOKENS = 24,000

Ha total tokens > 90k:
1. Első user message megőrizve
2. Utolsó 24k token megőrizve
3. Középső history → egy summary message:
   - Compacted range (message count, token count, roles)
   - Tool activity (használt tool nevek)
   - Files mentioned (érintett fájlok)
   - Recent highlights (utolsó 6 message preview)
```

## agents-squad Plugin Működése
- Tools: start_subagent, get_subagent, list_agent_presets, list_skills, get_skill, save_handoff, read_handoff
- Agent presets: bundled agents (pl. "phantom" default)
- Handoff store: conversation-scoped file-based
- Skills: bundled, global, project-level

## Telepítési Lépések
1. `sudo apt-get install -y nodejs npm` (Debian nodejs v18)
2. `curl -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/nodesource_setup.sh && sudo bash /tmp/nodesource_setup.sh`
3. `sudo apt-get install -y nodejs` → v22.23.2
4. `hash -r` (bash hash cache törlése)
5. `sudo npm install -g cline` → v3.0.64
6. `cline plugin install custom-compaction`
7. `cline plugin install agents-squad`
8. `cline plugin install web-search`
9. `cline plugin install background-terminal`
10. Cron jobok letöltése: `curl -fsSL https://raw.githubusercontent.com/cline/cline/main/sdk/examples/cron/<name>.cron.md -o ~/.cline/cron/<name>.cron.md`
11. `sed` konfigurálás (workspaceRoot, enabled: true, changelog.md path)