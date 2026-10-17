#!/usr/bin/env python3
"""
MCP Infrastruktura Dashboard - PyQt5 + pyqtgraph trend grafikonok.
Az egesz MCP infrastruktura monitorozasa: szerver, Qwen, Z.ai, folyamatok, toolok, riasztasok.
Breeze Dark theme, tray icon, animalt statuszjelzok.
"""
import sys
import os
import re
import json
import time
import subprocess
from datetime import datetime, date
from collections import deque
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QFrame, QGridLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon
try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

# ===========================================================================
# KONFIG
# ===========================================================================
MCP_SERVER_DIR = "/data/mcp_server"
MCP_LOG = MCP_SERVER_DIR + "/logs/mcp_server.log"
MCP_LOCK = MCP_SERVER_DIR + "/lock/mcp.lock"
QWEN_ANALYZER_LOG = MCP_SERVER_DIR + "/logs/qwen_analyzer.log"
MQL5_QWEN_LOG = MCP_SERVER_DIR + "/logs/mql5_book_qwen.log"
COST_STATE_FILE = MCP_SERVER_DIR + "/state/cost_persistent.json"
BRAIN_DIR = "/data/Brain"
CLINE_LOG_GLOB = "/home/Jules/.config/Code/logs/*/window*/exthost/output_logging_*/1-Cline.log"

# Ismert folyamatok (nev, cmdline substring, kritikus?)
KNOWN_PROCS = [
    ("MCP Server",      "server.py",                True),
    ("Qwen Analyzer",   "qwen_analyzer.py",         False),
    ("MQL5 Qwen 14B",   "mql5_book_qwen_analyzer",  False),
    ("Hardware Monitor", "hardware_monitor_v2",      True),
    ("Token Dashboard",  "token_dashboard.py",       False),
    ("Security Dash",    "security_dashboard.py",    False),
    ("SSH Monitor",      "ssh_tailscale_monitor",    False),
    ("Memory Watcher",   "memory_event_watcher",    True),
]

# Z.ai arazas (GLM-4.5 becsles)
ZAI_COST_PER_1K_IN = 0.001
ZAI_COST_PER_1K_OUT = 0.004

# Breeze Dark szinkeszlet
COLOR_BG = "#232629"
COLOR_CARD = "#2d3033"
COLOR_CARD_ALT = "#313639"
COLOR_BORDER = "#5c6063"
COLOR_TEXT = "#eff0f1"
COLOR_TEXT_DIM = "#bdc3c7"
COLOR_GREEN = "#1cdc9a"
COLOR_BLUE = "#1d99f3"
COLOR_YELLOW = "#fdbc4b"
COLOR_RED = "#da4453"
COLOR_PURPLE = "#9b59b6"
COLOR_ORANGE = "#f67400"
COLOR_TEAL = "#3daee9"

COLOR_OK = COLOR_GREEN
COLOR_WARN = COLOR_YELLOW
COLOR_CRIT = COLOR_RED
COLOR_INACTIVE = "#6b7280"

TOOL_CALL_RE = re.compile(r'call_tool: (\w+)')
QWEN_TOK_RE = re.compile(r'(\d+) tok')
MQL5_TPS_RE = re.compile(r'([\d.]+) tok/s \[(\d+)B\]')
MQL5_PROGRESS_RE = re.compile(r'\[(\d+)/(\d+)\]')
QWEN_VRAM_RE = re.compile(r'VRAM hasznalat: (\d+) MB')

# ===========================================================================
# ADATGYUJTES
# ===========================================================================

def get_mcp_server_status():
    """MCP szerver statusz (PID, uptime, utolso log)."""
    try:
        r = subprocess.run(['pgrep', '-f', 'server.py'], capture_output=True, text=True, timeout=3)
        pids = r.stdout.strip().split('\n') if r.stdout.strip() else []
        pid = int(pids[0]) if pids and pids[0] else None
    except Exception:
        pid = None
    uptime = ""
    if pid:
        try:
            r2 = subprocess.run(['ps', '-o', 'etime=', '-p', str(pid)],
                                capture_output=True, text=True, timeout=3)
            uptime = r2.stdout.strip()
        except Exception:
            pass
    last_log = ""
    log_errors = 0
    try:
        with open(MCP_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-200:]
        for line in lines[-3:]:
            last_log = line.strip()[:80]
        log_errors = sum(1 for l in lines if "[ERROR]" in l or "[CRITICAL]" in l)
    except Exception:
        pass
    return {"pid": pid, "uptime": uptime, "last_log": last_log, "errors": log_errors}


def get_tool_usage():
    """MCP tool hivas szamlalo a logbol."""
    counts = {}
    try:
        with open(MCP_LOG, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = TOOL_CALL_RE.search(line)
                if m:
                    name = m.group(1)
                    counts[name] = counts.get(name, 0) + 1
    except Exception:
        pass
    return counts


def get_qwen_instances():
    """Qwen instance-ok statusza (GPU, modell, tokenek)."""
    instances = []
    # MQL5 Qwen (14B)
    mql5_running = False
    mql5_pid = None
    try:
        r = subprocess.run(['pgrep', '-f', 'mql5_book_qwen_analyzer'],
                           capture_output=True, text=True, timeout=3)
        if r.stdout.strip():
            mql5_running = True
            mql5_pid = int(r.stdout.strip().split('\n')[0])
    except Exception:
        pass
    mql5_tokens = 0
    mql5_tps = 0.0
    mql5_progress = (0, 0)
    mql5_model = "14B"
    try:
        with open(MQL5_QWEN_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-500:]
        for line in lines:
            for m in QWEN_TOK_RE.finditer(line):
                mql5_tokens += int(m.group(1))
            m2 = MQL5_TPS_RE.search(line)
            if m2:
                mql5_tps = float(m2.group(1))
                mql5_model = m2.group(2) + "B"
            m3 = MQL5_PROGRESS_RE.search(line)
            if m3:
                mql5_progress = (int(m3.group(1)), int(m3.group(2)))
    except Exception:
        pass
    instances.append({
        "name": "MQL5 Qwen " + mql5_model,
        "gpu": "P4000",
        "running": mql5_running,
        "pid": mql5_pid,
        "tokens": mql5_tokens,
        "tps": mql5_tps,
        "progress": mql5_progress,
    })

    # Qwen Analyzer (7B/14B)
    analyzer_running = False
    analyzer_pid = None
    try:
        r = subprocess.run(['pgrep', '-f', 'qwen_analyzer\\.py'],
                           capture_output=True, text=True, timeout=3)
        if r.stdout.strip():
            analyzer_running = True
            analyzer_pid = int(r.stdout.strip().split('\n')[0])
    except Exception:
        pass
    analyzer_count = 0
    analyzer_vram = 0
    try:
        with open(QWEN_ANALYZER_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-300:]
        analyzer_count = sum(1 for l in lines if "elemzes elmentve" in l or "Valasz generalva" in l)
        for line in lines:
            m = QWEN_VRAM_RE.search(line)
            if m:
                analyzer_vram = int(m.group(1))
    except Exception:
        pass
    instances.append({
        "name": "Qwen Repo Analyzer",
        "gpu": "P4000",
        "running": analyzer_running,
        "pid": analyzer_pid,
        "tokens": 0,
        "tps": 0,
        "analyses": analyzer_count,
        "vram": analyzer_vram,
    })
    return instances


def get_gpu_full():
    """Mindket GPU statusza."""
    gpus = []
    try:
        r = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        for line in r.stdout.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "vram_used": int(parts[2]),
                    "vram_total": int(parts[3]),
                    "util": int(parts[4]),
                    "temp": int(parts[5]),
                })
    except Exception:
        pass
    return gpus


def get_process_status():
    """Ismert folyamatok statusza."""
    procs = []
    try:
        r = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        ps_lines = r.stdout
    except Exception:
        return procs
    for name, pattern, critical in KNOWN_PROCS:
        running = pattern in ps_lines
        pid = None
        cpu = 0.0
        if running:
            try:
                rp = subprocess.run(['pgrep', '-f', pattern],
                                    capture_output=True, text=True, timeout=3)
                if rp.stdout.strip():
                    pid = int(rp.stdout.strip().split('\n')[0])
                    rc = subprocess.run(['ps', '-o', '%cpu=', '-p', str(pid)],
                                        capture_output=True, text=True, timeout=3)
                    cpu = float(rc.stdout.strip()) if rc.stdout.strip() else 0.0
            except Exception:
                pass
        procs.append({
            "name": name, "running": running, "pid": pid,
            "cpu": cpu, "critical": critical,
        })
    return procs


def get_zai_vs_qwen():
    """Z.ai koltesseg vs Qwen megtakaritas."""
    zai_cost = 0.0
    zai_today = 0.0
    zai_tokens_in = 0
    zai_tokens_out = 0
    try:
        with open(COST_STATE_FILE, "r") as f:
            state = json.load(f)
        zai_cost = state.get("total_cost", 0)
        per_day = state.get("per_day", {})
        today_str = date.today().isoformat()
        if today_str in per_day:
            zai_today = per_day[today_str].get("cost", 0)
            zai_tokens_in = per_day[today_str].get("in", 0)
            zai_tokens_out = per_day[today_str].get("out", 0)
    except Exception:
        pass
    # Qwen tokenek (MQL5 log)
    qwen_tokens = 0
    try:
        with open(MQL5_QWEN_LOG, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                for m in QWEN_TOK_RE.finditer(line):
                    qwen_tokens += int(m.group(1))
    except Exception:
        pass
    # Qwen repo analyzer tokenek (becsles: ~800 tok/analizis)
    try:
        with open(QWEN_ANALYZER_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        n_analyses = sum(1 for l in lines if "Valasz generalva" in l)
        qwen_tokens += n_analyses * 800
    except Exception:
        pass
    # Megtakaritas: Qwen tokenek Z.ai aron
    qwen_saving = (qwen_tokens / 1000) * ZAI_COST_PER_1K_IN
    return {
        "zai_cost": zai_cost,
        "zai_today": zai_today,
        "zai_tokens_in": zai_tokens_in,
        "zai_tokens_out": zai_tokens_out,
        "qwen_tokens": qwen_tokens,
        "qwen_saving": qwen_saving,
    }


def get_alerts(gpus, procs, mcp):
    """Riasztasok generalasa."""
    alerts = []
    for g in gpus:
        if g["util"] > 90:
            alerts.append(("crit", "GPU " + g["name"] + " " + str(g["util"]) + "% kihasznaltsag!"))
        elif g["util"] > 75:
            alerts.append(("warn", "GPU " + g["name"] + " " + str(g["util"]) + "%"))
        if g["temp"] > 80:
            alerts.append(("crit", "GPU " + g["name"] + " " + str(g["temp"]) + "C!"))
        elif g["temp"] > 70:
            alerts.append(("warn", "GPU " + g["name"] + " " + str(g["temp"]) + "C"))
        vram_pct = g["vram_used"] / g["vram_total"] * 100 if g["vram_total"] else 0
        if vram_pct > 95:
            alerts.append(("crit", "VRAM " + g["name"] + " " + str(int(vram_pct)) + "%!"))
    for p in procs:
        if p["critical"] and not p["running"]:
            alerts.append(("crit", p["name"] + " LEALLT!"))
    if mcp.get("errors", 0) > 10:
        alerts.append(("warn", "MCP log " + str(mcp["errors"]) + " hiba"))
    # Inaktivitas: ha MCP log > 5 perc nem irodott
    try:
        mtime = os.path.getmtime(MCP_LOG)
        idle_sec = time.time() - mtime
        if idle_sec > 300:
            alerts.append(("warn", "MCP log " + str(int(idle_sec / 60)) + " perce nem irodik"))
    except Exception:
        pass
    if not alerts:
        alerts.append(("ok", "Minden rendben"))
    return alerts


# ===========================================================================
# WIDGETEK
# ===========================================================================

class CardWidget(QFrame):
    """Egy kartya a dashboard-on."""
    def __init__(self, title, parent=None, alt=False):
        super().__init__(parent)
        bg = COLOR_CARD_ALT if alt else COLOR_CARD
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame { background-color: " + bg + "; border-radius: 6px; border: 1px solid " + COLOR_BORDER + "; }")
        self.layout_v = QVBoxLayout(self)
        self.layout_v.setContentsMargins(10, 6, 10, 6)
        self.layout_v.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "color: " + COLOR_TEXT_DIM + "; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        self.title_label.setMinimumHeight(16)
        self.layout_v.addWidget(self.title_label)

    def add_label(self, text, color=None, size=13, bold=False):
        if color is None:
            color = COLOR_TEXT
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        w = "bold" if bold else "normal"
        lbl.setStyleSheet("color: " + color + "; font-size: " + str(size) + "px; font-weight: " + w + ";")
        self.layout_v.addWidget(lbl)
        return lbl

    def add_bar(self, value, maximum, color):
        bar = QProgressBar()
        bar.setMaximum(maximum if maximum > 0 else 1)
        bar.setValue(min(value, maximum if maximum > 0 else 1))
        bar.setTextVisible(True)
        bar.setFormat(str(value) + " / " + str(maximum))
        bar.setStyleSheet(
            "QProgressBar { background-color: #1a1c1e; border: 1px solid " + COLOR_BORDER +
            "; border-radius: 4px; text-align: center; color: " + COLOR_TEXT +
            "; font-size: 10px; min-height: 18px; max-height: 18px; }"
            "QProgressBar::chunk { background-color: " + color + "; border-radius: 3px; }")
        self.layout_v.addWidget(bar)
        return bar

    def add_plot(self, title=""):
        """pyqtgraph PlotWidget hozzaadasa (fallback: QLabel ha nincs pyqtgraph)."""
        if HAS_PYQTGRAPH:
            pw = pg.PlotWidget()
            pw.setBackground(COLOR_BG)
            pw.setTitle(title, color=COLOR_TEXT_DIM, size="8pt")
            pw.setMaximumHeight(80)
            pw.showGrid(x=False, y=True, alpha=0.15)
            for axis in [pw.getAxis('bottom'), pw.getAxis('left')]:
                axis.setPen(pg.mkPen(COLOR_BORDER))
                axis.setTextPen(pg.mkPen(COLOR_TEXT_DIM))
                axis.setStyle(tickLength=-3)
            self.layout_v.addWidget(pw)
            return pw
        else:
            lbl = QLabel("[pyqtgraph nem erheto el]")
            lbl.setStyleSheet("color: " + COLOR_TEXT_DIM + "; font-size: 9px;")
            self.layout_v.addWidget(lbl)
            return None


def status_icon(running, critical=False):
    """Statusz ikon szoveg."""
    if running:
        return "OK"
    return "CRIT" if critical else "OFF"


# ===========================================================================
# FO ABLAK
# ===========================================================================

class MCPDashboardWindow(QMainWindow):
    def __init__(self, start_minimized=False):
        super().__init__()
        self.setWindowTitle("MCP Infrastruktura Dashboard")
        self.setMinimumSize(900, 720)
        self.setStyleSheet("QMainWindow { background-color: " + COLOR_BG + "; }")
        icon_path = "/usr/share/icons/hicolor/256x256/apps/mcp-infra.png"
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.tray = None

        # Trend history (deque, max 60 pont = 3 perc @ 3s)
        self.gpu_util_hist = deque(maxlen=60)
        self.gpu_vram_hist = deque(maxlen=60)
        self.tps_hist = deque(maxlen=60)
        self.cost_hist = deque(maxlen=60)

        self._init_ui()
        self._init_tray()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(3000)
        self.refresh()

        if start_minimized:
            self.hide()
            if self.tray:
                self.tray.show()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(10, 8, 10, 8)

        # Fejlec
        hdr = QHBoxLayout()
        title = QLabel("  MCP INFRASTRUKTURA DASHBOARD")
        title.setStyleSheet("color: " + COLOR_BLUE + "; font-size: 17px; font-weight: bold;")
        hdr.addWidget(title)
        self.lbl_clock = QLabel("")
        self.lbl_clock.setStyleSheet("color: " + COLOR_PURPLE + "; font-size: 11px;")
        hdr.addStretch()
        hdr.addWidget(self.lbl_clock)
        main_layout.addLayout(hdr)

        # 3x2 racs
        grid = QGridLayout()
        grid.setSpacing(6)
        main_layout.addLayout(grid)

        # === 1. MCP SZERVER STATUS ===
        self.card_server = CardWidget("MCP SZERVER")
        grid.addWidget(self.card_server, 0, 0)
        self.srv_status = self.card_server.add_label("", COLOR_TEXT, 13, bold=True)
        self.srv_pid = self.card_server.add_label("", COLOR_TEXT_DIM, 10)
        self.srv_uptime = self.card_server.add_label("", COLOR_TEXT_DIM, 10)
        self.srv_tools = self.card_server.add_label("", COLOR_TEAL, 10)
        self.srv_last = self.card_server.add_label("", COLOR_TEXT_DIM, 9)
        self.srv_errors = self.card_server.add_label("", COLOR_TEXT_DIM, 10)

        # === 2. QWEN INSTANCIAK ===
        self.card_qwen = CardWidget("QWEN INSTANCIAK", alt=True)
        grid.addWidget(self.card_qwen, 0, 1)
        self.qwen_mql5 = self.card_qwen.add_label("", COLOR_TEXT, 12, bold=True)
        self.qwen_mql5_bar = self.card_qwen.add_bar(0, 1, COLOR_BLUE)
        self.qwen_mql5_bar.setVisible(False)
        self.qwen_mql5_detail = self.card_qwen.add_label("", COLOR_TEXT_DIM, 10)
        self.qwen_analyzer = self.card_qwen.add_label("", COLOR_TEXT, 12, bold=True)
        self.qwen_analyzer_detail = self.card_qwen.add_label("", COLOR_TEXT_DIM, 10)

        # === 3. Z.ai vs QWEN ===
        self.card_savings = CardWidget("Z.ai vs QWEN MEGTAKARITAS")
        grid.addWidget(self.card_savings, 0, 2)
        self.sav_zai = self.card_savings.add_label("", COLOR_BLUE, 13, bold=True)
        self.sav_qwen = self.card_savings.add_label("", COLOR_TEAL, 13, bold=True)
        self.sav_saving = self.card_savings.add_label("", COLOR_GREEN, 15, bold=True)
        self.sav_pct = self.card_savings.add_label("", COLOR_GREEN, 12)
        self.sav_detail = self.card_savings.add_label("", COLOR_TEXT_DIM, 10)

        # === 4. FOLYAMATOK ===
        self.card_procs = CardWidget("FOLYAMATOK", alt=True)
        grid.addWidget(self.card_procs, 1, 0)
        self.proc_labels = []
        for _ in KNOWN_PROCS:
            lbl = self.card_procs.add_label("", COLOR_TEXT, 11)
            self.proc_labels.append(lbl)

        # === 5. TOOL HASZNALAT ===
        self.card_tools = CardWidget("TOOL HASZNALAT")
        grid.addWidget(self.card_tools, 1, 1)
        self.tool_labels = {}
        tool_names = ["list_gpu", "read_repo", "write_log", "analyze_with_qwen",
                      "store_session", "read_session", "repository_memory_indexer"]
        for tn in tool_names:
            lbl = self.card_tools.add_label("  " + tn + ": --", COLOR_TEXT_DIM, 10)
            self.tool_labels[tn] = lbl
        self.tool_total = self.card_tools.add_label("", COLOR_TEAL, 11, bold=True)

        # === 6. RIASZTASOK + GRAFIKON ===
        self.card_alerts = CardWidget("RIASZTASOK & TREND", alt=True)
        grid.addWidget(self.card_alerts, 1, 2)
        self.alert_label = self.card_alerts.add_label("", COLOR_TEXT, 11)
        self.alert_label.setWordWrap(True)
        # Trend grafikon
        self.plot_widget = self.card_alerts.add_plot("GPU% (kek) / tok/s (zold)")

    def _init_tray(self):
        icon_path = "/usr/share/icons/hicolor/256x256/apps/mcp-infra.png"
        icon = QIcon(icon_path) if os.path.isfile(icon_path) else QIcon()
        self.tray = QSystemTrayIcon(icon, self)
        menu = QMenu()
        act_show = menu.addAction("Megjelenites")
        act_show.triggered.connect(self._tray_show)
        act_quit = menu.addAction("Kilepes")
        act_quit.triggered.connect(QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("MCP Infra Dashboard")
        self.tray.show()

    def _tray_show(self):
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event):
        """X gomb = tálca letétel, nem kilépés."""
        event.ignore()
        self.hide()
        if self.tray:
            self.tray.show()

    def refresh(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.lbl_clock.setText("  " + now + "  (3s)")

        # Adatgyujtes
        mcp = get_mcp_server_status()
        tools = get_tool_usage()
        qwen = get_qwen_instances()
        gpus = get_gpu_full()
        procs = get_process_status()
        savings = get_zai_vs_qwen()
        alerts = get_alerts(gpus, procs, mcp)

        # --- MCP Szerver ---
        if mcp["pid"]:
            self.srv_status.setText(status_icon(True) + "  MCP Server aktiv")
            self.srv_status.setStyleSheet("color: " + COLOR_OK + "; font-size: 13px; font-weight: bold;")
        else:
            self.srv_status.setText(status_icon(False, True) + "  MCP Server LEALLT!")
            self.srv_status.setStyleSheet("color: " + COLOR_CRIT + "; font-size: 13px; font-weight: bold;")
        self.srv_pid.setText("PID: " + str(mcp["pid"] or "N/A"))
        self.srv_uptime.setText("Uptime: " + str(mcp["uptime"] or "N/A"))
        top_tools = sorted(tools.items(), key=lambda x: -x[1])[:5]
        tools_str = "  ".join(n + ":" + str(c) for n, c in top_tools)
        self.srv_tools.setText("Top: " + tools_str)
        self.srv_last.setText("Log: " + mcp["last_log"][:60])
        err_color = COLOR_CRIT if mcp["errors"] > 5 else COLOR_TEXT_DIM
        self.srv_errors.setText("Hibak (200): " + str(mcp["errors"]))
        self.srv_errors.setStyleSheet("color: " + err_color + "; font-size: 10px;")

        # --- Qwen Instanciak ---
        for inst in qwen:
            if "MQL5" in inst["name"]:
                si = status_icon(inst["running"])
                self.qwen_mql5.setText(si + "  " + inst["name"] + " (" + inst["gpu"] + ")")
                c = COLOR_OK if inst["running"] else COLOR_INACTIVE
                self.qwen_mql5.setStyleSheet("color: " + c + "; font-size: 12px; font-weight: bold;")
                prog = inst["progress"]
                if prog[1] > 0:
                    self.qwen_mql5_bar.setMaximum(prog[1])
                    self.qwen_mql5_bar.setValue(prog[0])
                    self.qwen_mql5_bar.setFormat(str(prog[0]) + "/" + str(prog[1]))
                    self.qwen_mql5_bar.setVisible(True)
                else:
                    self.qwen_mql5_bar.setVisible(False)
                detail = "Tokenek: " + format(inst["tokens"], ",") + " | " + ("%.1f" % inst["tps"]) + " tok/s"
                self.qwen_mql5_detail.setText(detail)
                # Trend
                self.tps_hist.append(inst["tps"])
            elif "Analyzer" in inst["name"]:
                si = status_icon(inst["running"])
                self.qwen_analyzer.setText(si + "  " + inst["name"] + " (" + inst["gpu"] + ")")
                c = COLOR_OK if inst["running"] else COLOR_INACTIVE
                self.qwen_analyzer.setStyleSheet("color: " + c + "; font-size: 12px; font-weight: bold;")
                detail = "Elemzesek: " + str(inst.get("analyses", 0)) + " | VRAM: " + str(inst.get("vram", 0)) + " MB"
                self.qwen_analyzer_detail.setText(detail)

        # --- GPU trend ---
        for g in gpus:
            if "P4000" in g["name"]:
                self.gpu_util_hist.append(g["util"])
                self.gpu_vram_hist.append(g["vram_used"])

        # --- Z.ai vs Qwen ---
        self.sav_zai.setText("Z.ai koltesseg: $" + ("%.2f" % savings["zai_cost"]) + " (ma: $" + ("%.4f" % savings["zai_today"]) + ")")
        self.sav_qwen.setText("Qwen tokenek: " + format(savings["qwen_tokens"], ","))
        self.sav_saving.setText(">> Megtakaritas: $" + ("%.4f" % savings["qwen_saving"]))
        total_spent = savings["zai_cost"] + savings["qwen_saving"]
        pct = (savings["qwen_saving"] / total_spent * 100) if total_spent > 0 else 0
        self.sav_pct.setText("Qwen arany: " + ("%.1f" % pct) + "% a teljesbol")
        self.sav_detail.setText(
            "Z.ai ma: IN " + format(savings["zai_tokens_in"], ",") + " OUT " + format(savings["zai_tokens_out"], ","))

        # --- Folyamatok ---
        for i, p in enumerate(procs):
            if i < len(self.proc_labels):
                si = status_icon(p["running"], p["critical"])
                cpu_str = " (" + ("%.1f" % p["cpu"]) + "% CPU)" if p["running"] and p["cpu"] > 0 else ""
                pid_str = " PID:" + str(p["pid"]) if p["pid"] else ""
                c = COLOR_OK if p["running"] else (COLOR_CRIT if p["critical"] else COLOR_INACTIVE)
                self.proc_labels[i].setText(si + "  " + p["name"] + pid_str + cpu_str)
                self.proc_labels[i].setStyleSheet("color: " + c + "; font-size: 11px;")

        # --- Tool Hasznalat ---
        total_calls = 0
        for tn, lbl in self.tool_labels.items():
            cnt = tools.get(tn, 0)
            total_calls += cnt
            lbl.setText("  " + tn + ": " + str(cnt))
        self.tool_total.setText("Osszes hivas: " + format(total_calls, ","))

        # --- Riasztasok ---
        alert_lines = []
        for level, msg in alerts[:5]:
            if level == "crit":
                alert_lines.append("[!] " + msg)
            elif level == "warn":
                alert_lines.append("[~] " + msg)
            else:
                alert_lines.append("[OK] " + msg)
        self.alert_label.setText("\n".join(alert_lines))
        has_crit = any(l == "crit" for l, _ in alerts)
        ac = COLOR_CRIT if has_crit else (COLOR_YELLOW if any(l == "warn" for l, _ in alerts) else COLOR_OK)
        self.alert_label.setStyleSheet("color: " + ac + "; font-size: 11px;")

        # --- Trend grafikon ---
        if self.plot_widget is not None and HAS_PYQTGRAPH:
            self.plot_widget.clear()
            if self.gpu_util_hist:
                x = list(range(len(self.gpu_util_hist)))
                self.plot_widget.plot(x, list(self.gpu_util_hist),
                                      pen=pg.mkPen(COLOR_BLUE, width=2), name="GPU%")
            if self.tps_hist:
                x2 = list(range(len(self.tps_hist)))
                scaled_tps = [t * 0.5 for t in self.tps_hist]
                self.plot_widget.plot(x2, scaled_tps,
                                      pen=pg.mkPen(COLOR_GREEN, width=2), name="tok/s")

        # --- Koltesseg trend ---
        self.cost_hist.append(savings["zai_cost"])

        # Tray tooltip
        n_running = sum(1 for p in procs if p["running"])
        self.tray.setToolTip(
            "MCP Infra: " + str(n_running) + "/" + str(len(procs)) + " fut | "
            "Z.ai $" + ("%.2f" % savings["zai_cost"]) + " | Qwen $" + ("%.4f" % savings["qwen_saving"]))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    start_min = "--minimized" in sys.argv or "--hidden" in sys.argv
    win = MCPDashboardWindow(start_minimized=start_min)
    if not start_min:
        win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
