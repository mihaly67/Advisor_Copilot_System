#!/bin/bash
# ============================================================
# Scalper V6 — KDE Indító wrapper (kdialog alapú)
# Megjelenít egy ablakot: Indítás / Leállítás / Státusz / Mégse
# A választott opciót továbbítja a scalper_v6_start.sh-nak.
# ============================================================

# Futtatási környezet a KDE indítóhoz (különösen DISPLAY/fontok)
export DISPLAY="${DISPLAY:-:0}"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/Jules/jules_venv/bin"

# A start.sh a WorkingDirectory-t használja, de a .desktop fájl nem tudja
# azt szabványosan beállítani — itt cd-zünk a projektgyökérbe.
cd /data/LGBM_copilot || {
    kdialog --error "Nem található a projekt mappa: /data/LGBM_copilot"
    exit 1
}

START_SCRIPT="/data/LGBM_copilot/scalper_v6_start.sh"

if [ ! -x "$START_SCRIPT" ]; then
    kdialog --error "A start script nem található vagy nem futtatható:\n$START_SCRIPT"
    exit 1
fi

# Radiolist: minden sornak: <tag> <label> <on|off>
# Csak az "on" státuszú van alapértelmezetten kiválasztva.
CHOICE=$(kdialog --title "Scalper V6 HUD" \
    --radiolist "Mit szeretnél csinálni?" \
    start  "🚀 Indítás  (Bridge + HUD elindítása)"  on \
    stop   "⏹️  Leállítás (Bridge + HUD leállítása)" off \
    restart "🔄 Újraindítás"                          off \
    status "📊 Státusz lekérdezése"                  off)

# Ha a user bezárta az ablakot vagy Mégse-t nyomott
if [ $? -ne 0 ] || [ -z "$CHOICE" ]; then
    exit 0
fi

case "$CHOICE" in
    start|stop|restart|status)
        # A start.sh már tartalmazza a venv aktiválást és env változókat
        # Konsole ablak nyitása hogy lássa a kimenetet (főleg start/status)
        # --hold: bezárás után nem lép ki azonnal — Enter vagy ablakbezárás kell
        # Ha a script befejezi, a konsole is bezáródik ( --hold csak végén vár)
        konsole --hold -e bash -c "$START_SCRIPT $CHOICE; echo; echo 'Ablak bezárása: Ctrl+C vagy X gomb'; sleep 600"
        ;;
    *)
        kdialog --error "Ismeretlen opció: $CHOICE"
        exit 1
        ;;
esac
