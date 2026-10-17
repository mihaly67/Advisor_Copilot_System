# Session: cline_plugins_cron_installed_20260922
*Időbélyeg: 2026-09-22T15:06:23.490680*

# SESSION: Cline Plugins + Cron Telepítés — 2026.09.22.

## TASK CÉL
Cline CLI + 4 plugin + 7 cron job telepítése token-optimalizáláshoz.

## KÉSZ ✅

### 1. Node.js v22 Telepítés
- Korábban v18 (Debian default) → NodeSource repo-ból v22.23.2
- `curl -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/nodesource_setup.sh && sudo bash /tmp/nodesource_setup.sh`
- `sudo apt-get install -y nodejs` → v22.23.2, npm 10.9.8
- `hash -r` (bash hash cache törlése fontos!)

### 2. Cline CLI v3.0.64
- `sudo npm install -g cline` (329 csomag)
- `cline --version` → 3.0.64

### 3. Plugins (4 db telepítve)
- **custom-compaction**: context compaction (preserve first msg + recent 24k, summarize middle) — MAX 120k tokens, compact at 90k
- **agents-squad**: background subagents with presets + handoff store (start_subagent, get_subagent, list_skills, save_handoff, read_handoff)
- **web-search**: Exa-backed web search tool
- **background-terminal**: long-running shell jobs with polling + cleanup

Útvonal: `~/.cline/plugins/_installed/official/`

### 4. Cron Jobs (7 db telepítve)
- changelog-generator (péntek 18:00) → memory-bank/changelog.md
- dependency-check (hétfő 10:00) → npm audit + outdated
- test-coverage-report → daily coverage metrics
- type-check-strict → TypeScript safety
- code-style-audit → linting + formatting
- dead-code-finder → unused code
- documentation-check → API doc coverage

Útvonal: `~/.cline/cron/*.cron.md`
Konfigurálva: workspaceRoot=/home/Jules/zhipu_projekt, enabled=true

## FÁJLOK:
- /home/Jules/.cline/plugins/_installed/official/custom-compaction-5b627110f9dd/
- /home/Jules/.cline/plugins/_installed/official/agents-squad-1ae2facb94f9/
- /home/Jules/.cline/plugins/_installed/official/web-search-c2569026205b/
- /home/Jules/.cline/plugins/_installed/official/background-terminal-6c6f0b95621b/
- /home/Jules/.cline/cron/changelog-generator.cron.md
- /home/Jules/.cline/cron/dependency-check.cron.md
- /home/Jules/.cline/cron/test-coverage-report.cron.md
- /home/Jules/.cline/cron/type-check-strict.cron.md
- /home/Jules/.cline/cron/code-style-audit.cron.md
- /home/Jules/.cline/cron/dead-code-finder.cron.md
- /home/Jules/.cline/cron/documentation-check.cron.md
- /data/Brain/_qwen_analysis/CLINE_PLUGINS_CRON_INSTALL.md

## RENDSZER:
- Node.js v22.23.2 (NodeSource)
- npm 10.9.8
- Cline CLI v3.0.64
- GPU: P4000 (Qwen MCP) + P2000 (szabad), persistence ON
- Sudo: passwordless (jelszó 1104)

## KÖVETKEZŐ:
- Scalper Copilot Lépcső 1 megkezdése
- Cron jobok tesztelése (cline cron list)
- Plugin működés validálása élő Cline session-ben