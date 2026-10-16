# Session: tailscale_emergency_access
*Időbélyeg: 2026-09-23T00:11:41.044125*

## Tailscale Vészhelyzeti Hozzáférés (Disaster Recovery)

### Mikor használható?
- Ha a Jules fizikai gépen fekete képernyő van (display driver hiba)
- Ha VSCode/Cline nem indul el lokálisan
- Ha másik gépről (laptop/phone) VSCode Cline-nal kell beavatkozni

### Csatlakozási mód:
1. Másik gépen VSCode + Cline extension
2. Tailscale VPN aktív a másik gépen
3. SSH csatlakozás:
```bash
export SSHPASS='1104'
sshpass -e ssh -o ConnectTimeout=10 Jules@100.77.191.66 'parancsok'
```

### IP címek (Tailscale, dinamikusak!):
- **Jules fizikai gép**: 100.77.191.66 (stabilabb, háromhavonta változhat)
- **Devbox** (efemer): 100.96.244.14 (offline amikor nem használják)

### Hitelesítés:
- Felhasználó: Jules
- Jelszó: 1104
- SSH kulcs alternatíva: ~/.ssh/jules_key (ed25519)

### Mit lehet csinálni SSH-n keresztül?
- GRUB módosítás: sudo nano /etc/default/grub + sudo update-grub
- Kernel választás: GRUB_DEFAULT módosítás
- NVIDIA driver: sudo nvidia-smi, DKMS modulok
- Service management: sudo service sshd restart, sudo service sddm restart
- Display manager újraindítás: sudo service sddm restart
- Rendszer újraindítás: sudo reboot

### Fontos szolgáltatások (bootkor indulnak):
- S03ssh (sshd) — SSH elérés azonnal
- S03tailscaled — Tailscale VPN felépül
- S04ssh-tailscale-sync — automatikus szinkron

### Monitor:
- ssh_tailscale_monitor.py v2.0.0 fut a tálcán
- Új funkció: CLINE KAPCSOLAT DETEKTÁLÁS
- Megkülnönbözteti: 🖥️ Lokális Cline vs 🌐 Távoli Cline (Tailscale SSH)
- Hely: /home/Jules/HardverMonitor_dev/ssh_tailscale_monitor.py
- Autostart: ~/.config/autostart/SSH_Tailscale_Monitor.desktop

### PreToolUse Hook javítás (2026-09-22):
- run_commands eset: csak útvonal-szerű tokeneket ellenőriz (/, .env, .key stb.)
- .clineignore védelem: csak editor/apply_patch-re, nem run_commands-ra
- Ez javította a végtelen abort problémát SSH parancsoknál

### VPS (Contabo) — csak olvasásra:
- IP: 5.189.163.88, user: misi
- Csak SSH kulccal, jelszó nélkül
- RAG/tudástér tárolás, nem fejlesztés