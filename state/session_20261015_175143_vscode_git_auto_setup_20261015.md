# Session: vscode_git_auto_setup_20261015
*Időbélyeg: 2026-10-15T17:51:43.093359*

# VS Code + Git + SSH Auto-Setup (2026-10-15)

## Problémák amiket megoldottunk
1. KDE Wallet folyamatos prompt → teljes letiltás
2. Git credential helper hiányzott → store beállítva
3. SSH kulcs hibás (libcrypto error) → új ED25519 generálva, passphrase nélkül
4. VS Code 3x indítás → git.autoFetch=false, performance optimalizálás
5. GH CLI hiányzott → telepítve (v2.23.0)

## Mit csináltunk

### Git Credential Store
- `git config --global credential.helper store`
- ~/.git-credentials létrejön első push/pull után

### SSH Kulcs
- Új ED25519: ~/.ssh/id_ed25519 (passphrase nélkül)
- Publikus kulcs: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFLZ373YmsT+a2hVsPT1gxzjFFWy6WI0rK7YQDqsCzQw jules@dev.local
- SSH config: ~/.ssh/config (GitHub + GitKraken)
- Auto-add: .profile, .bashrc, autostart

### KDE Wallet Némítás (4 réteg)
1. ~/.config/kwalletrc: Enabled=false + org.freedesktop.secrets Enabled=false
2. ~/.xsessionrc: KWALLET_DISABLED=1 + GIT_ASKPASS=/usr/bin/true
3. ~/.config/environment.d/ssh-kwallet.conf: KWALLET_DISABLED=1
4. .profile + .bashrc: export KWALLET_DISABLED=1

### VS Code Settings Optimalizálás
- git.autoFetch=false (nincs auto-credential prompt)
- git.autoRefresh=false
- git.useIntegratedAskPass=true
- git.openRepositoryInParentFolders=never
- git.repositoryScanMaxDepth=1
- extensions.autoUpdate=onlyEnabledExtensions
- extensions.autoCheckUpdates=false
- workbench.startupEditor=none
- files.watcherExclude (node_modules, __pycache__, .git, venv, hf_cache, .cline)
- terminal KWALLET_DISABLED=1

### Autostart Scripts
- ~/.config/autostart/dev-env-setup.desktop → dev-env-setup.sh
- ~/.config/autostart/ssh-agent-startup.desktop → ssh-agent-startup.sh
- ~/.local/bin/vscode-watchdog.sh (VS Code indítás stabilizáló)

### GitHub CLI
- gh v2.23.0 telepítve
- MÉG NINCS AUTENTIKÁLVA → gh auth login szükséges

### NYITOTT: GitHub auth
- SSH publikus kulcsot hozzá kell adni a GitHub account-hoz
- gh auth login --with-token szükséges
- VAGY: első git push/pull elmenti a credential-t a store-ba