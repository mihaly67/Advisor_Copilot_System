#!/usr/bin/env python3
"""
Token Dashboard v2.1 — Z.ai költség/token monitor (PyQt5)
3 kártya: Összköltség | Mai használat | Task/Session költség
+ GPU kártya. Breeze Dark téma, tray icon.
Induláskor VS Code logokat olvas, számol, saját logot ír.
"""
import sys
import os
import re
import json
import glob
import subprocess
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QGridLayout, QSystemTrayIcon, QMenu
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QStyleFactory

MCP_DIR = "/data/mcp_server"
COST_STATE = MCP_DIR + "/state/cost_persistent.json"
OWN_LOG = MCP_DIR + "/logs/token_dashboard.log"
CLINE_LOG_GLOB = "/home/Jules/.config/Code/logs/*/window*/exthost/output_logging_*/*-Cline.log"

# Breeze Dark színkészlet
COLOR_BG = "#232629"
COLOR_CARD = "#2d3033"
COLOR_BORDER = "#5c6063"
COLOR_TEXT = "#eff0f1"
COLOR_TEXT_DIM = "#bdc3c7"
COLOR_GREEN = "#1cdc9a"
COLOR_BLUE = "#1d99f3"
COLOR_YELLOW = "#fdbc4b"
COLOR_RED = "#da4453"
COLOR_PURPLE = "#9b59b6"

UTC_OFFSET_HOURS = 2  # CEST = UTC+2

def run_cmd(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.stdout else ""
    except:
        return ""

def utc_to_local(utc_str):
    try:
        if utc_str.endswith('Z'):
            dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%f")
        return dt + timedelta(hours=UTC_OFFSET_HOURS)
    except:
        return None

def write_own_log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(OWN_LOG, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass

def load_cost_state():
    try:
        with open(COST_STATE) as f:
            return json.load(f)
    except:
        return {}

def save_cost_state(state):
    try:
        with open(COST_STATE, "w") as f:
            json.dump(state, f, indent=2)
    except:
        pass

def parse_task_usage_lines(filepath):
    results = []
    try:
        with open(filepath, "r", errors="replace") as f:
            for line in f:
                if "Task usage:" not in line:
                    continue
                m = re.search(
                    r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z).*tokensIn=(\d+).*tokensOut=(\d+).*cost=([\d.]+)',
                    line
                )
                if m:
                    local_dt = utc_to_local(m.group(1))
                    if local_dt:
                        results.append((local_dt, int(m.group(2)), int(m.group(3)), float(m.group(4))))
    except:
        pass
    return results

def get_all_cline_logs():
    return sorted(glob.glob(CLINE_LOG_GLOB))

def get_latest_cline_log():
    files = get_all_cline_logs()
    return files[-1] if files else None


def compute_all_stats():
    today_str = date.today().isoformat()
    all_logs = get_all_cline_logs()
    all_entries = []
    session_entries = []
    latest_log = get_latest_cline_log()

    for fpath in all_logs:
        entries = parse_task_usage_lines(fpath)
        all_entries.extend(entries)
        if fpath == latest_log:
            session_entries = entries

    per_day = {}
    for local_dt, tin, tout, cost in all_entries:
        day_key = local_dt.strftime("%Y-%m-%d")
        if day_key not in per_day:
            per_day[day_key] = {"cost": 0, "in": 0, "out": 0, "calls": 0}
        per_day[day_key]["cost"] += cost
        per_day[day_key]["in"] += tin
        per_day[day_key]["out"] += tout
        per_day[day_key]["calls"] += 1

    saved_state = load_cost_state()
    saved_per_day = saved_state.get("per_day", {})
    merged_per_day = {}
    all_days = set(list(per_day.keys()) + list(saved_per_day.keys()))
    for day in all_days:
        log_data = per_day.get(day, {"cost": 0, "in": 0, "out": 0, "calls": 0})
        saved_data = saved_per_day.get(day, {"cost": 0, "in": 0, "out": 0, "calls": 0})
        merged_per_day[day] = {
            "cost": max(saved_data["cost"], log_data["cost"]),
            "in": max(saved_data["in"], log_data["in"]),
            "out": max(saved_data["out"], log_data["out"]),
            "calls": max(saved_data["calls"], log_data["calls"]),
        }

    total_cost = sum(v["cost"] for v in merged_per_day.values())
    total_in = sum(v["in"] for v in merged_per_day.values())
    total_out = sum(v["out"] for v in merged_per_day.values())
    total_calls = sum(v["calls"] for v in merged_per_day.values())
    active_days = sorted(merged_per_day.keys())

    new_state = {
        "total_cost": round(total_cost, 8),
        "total_in": total_in,
        "total_out": total_out,
        "total_calls": total_calls,
        "active_days_set": active_days,
        "per_day": {k: {"cost": round(v["cost"], 8), "in": v["in"], "out": v["out"], "calls": v["calls"]} for k, v in merged_per_day.items()}
    }
    save_cost_state(new_state)

    today_data = merged_per_day.get(today_str, {"cost": 0, "in": 0, "out": 0, "calls": 0})

    session_cost = sum(e[3] for e in session_entries)
    session_in = sum(e[1] for e in session_entries)
    session_out = sum(e[2] for e in session_entries)
    session_calls = len(session_entries)

    result = {
        "total_cost": total_cost,
        "total_in": total_in,
        "total_out": total_out,
        "total_calls": total_calls,
        "total_days": len(active_days),
        "today_cost": today_data["cost"],
        "today_in": today_data["in"],
        "today_out": today_data["out"],
        "today_calls": today_data["calls"],
        "session_cost": session_cost,
        "session_in": session_in,
        "session_out": session_out,
        "session_calls": session_calls,
        "log_files": len(all_logs),
    }

    write_own_log(
        f"UPDATE | total=${total_cost:.4f} in={total_in} out={total_out} calls={total_calls} | "
        f"today=${today_data['cost']:.4f} in={today_data['in']} out={today_data['out']} calls={today_data['calls']} | "
        f"session=${session_cost:.4f} in={session_in} out={session_out} calls={session_calls} | "
        f"logs={len(all_logs)}"
    )
    return result

def get_gpu_status():
    out = run_cmd("nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits 2>/dev/null")
    if not out:
        return {"vram": "-", "vram_total": "-", "util": "-", "temp": "-", "pct": 0}
    try:
        parts = [p.strip() for p in out.split(',')]
        vram = int(parts[0])
        vram_total = int(parts[1])
        util = int(parts[2])
        temp_str = parts[3].strip().split('\n')[0].strip()
        temp = int(temp_str)
        pct = int(vram / vram_total * 100) if vram_total > 0 else 0
        return {"vram": vram, "vram_total": vram_total, "util": util, "temp": temp, "pct": pct}
    except (ValueError, IndexError):
        return {"vram": "-", "vram_total": "-", "util": "-", "temp": "-", "pct": 0}


class TokenDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Z.ai Token Dashboard v2.1")
        self.resize(620, 460)
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLOR_BG}; }}")

        icon_path = MCP_DIR + "/state/icons/zai-token-256.png"
        self.app_icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon.fromTheme("zai-token-dashboard")
        if self.app_icon.isNull():
            self.app_icon = QIcon.fromTheme("zai-token-dashboard")
        self.setWindowIcon(self.app_icon)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(5)

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)

        self.card_total = self._make_card("ÖSSZES KÖLTSÉG", COLOR_GREEN)
        self.card_today = self._make_card("MAI HASZNÁLAT", COLOR_BLUE)
        self.card_session = self._make_card("TASK / SESSION", COLOR_PURPLE)
        self.card_gpu = self._make_card("P4000 GPU", COLOR_YELLOW)

        grid.addWidget(self.card_total["frame"], 0, 0)
        grid.addWidget(self.card_today["frame"], 0, 1)
        grid.addWidget(self.card_session["frame"], 1, 0)
        grid.addWidget(self.card_gpu["frame"], 1, 1)
        main_layout.addLayout(grid)

        self.tray = QSystemTrayIcon(self.app_icon, self)
        tray_menu = QMenu()
        act_show = tray_menu.addAction("Megjelenítés")
        act_show.triggered.connect(self.showNormal)
        act_quit = tray_menu.addAction("Kilépés")
        act_quit.triggered.connect(QApplication.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(5000)

        self.update_dashboard()

    def _make_card(self, title, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(1)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {COLOR_TEXT_DIM}; border: none; background: transparent;")
        layout.addWidget(lbl_title)

        lbl_main = QLabel("—")
        lbl_main.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl_main.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        layout.addWidget(lbl_main)

        lbl_sub = QLabel("")
        lbl_sub.setFont(QFont("Segoe UI", 11))
        lbl_sub.setStyleSheet(f"color: {COLOR_TEXT}; border: none; background: transparent;")
        layout.addWidget(lbl_sub)

        return {"frame": frame, "title": lbl_title, "main": lbl_main, "sub": lbl_sub}

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def update_dashboard(self):
        try:
            stats = compute_all_stats()
        except Exception as e:
            write_own_log(f"ERROR update_dashboard: {e}")
            return

        # Card 1: Total
        self.card_total["main"].setText(f"${stats['total_cost']:.4f}")
        self.card_total["sub"].setText(
            f"{stats['total_in']:,} IN | {stats['total_out']:,} OUT\n"
            f"{stats['total_calls']} calls | {stats['total_days']} nap"
        )

        # Card 2: Today
        self.card_today["main"].setText(f"${stats['today_cost']:.4f}")
        self.card_today["sub"].setText(
            f"{stats['today_in']:,} IN | {stats['today_out']:,} OUT\n"
            f"{stats['today_calls']} calls"
        )

        # Card 3: Session (current task/session)
        self.card_session["main"].setText(f"${stats['session_cost']:.4f}")
        self.card_session["sub"].setText(
            f"{stats['session_in']:,} IN | {stats['session_out']:,} OUT\n"
            f"{stats['session_calls']} calls | {stats['log_files']} log"
        )

        # Card 4: GPU
        gpu = get_gpu_status()
        if isinstance(gpu["vram"], int):
            self.card_gpu["main"].setText(f"{gpu['vram']} / {gpu['vram_total']} MiB")
            util = gpu["util"]
            color = COLOR_GREEN if util < 50 else (COLOR_YELLOW if util < 80 else COLOR_RED)
            self.card_gpu["main"].setStyleSheet(f"color: {color}; border: none; background: transparent;")
            self.card_gpu["sub"].setText(f"GPU: {util}% | Temp: {gpu['temp']}°C")
        else:
            self.card_gpu["main"].setText("N/A")
            self.card_gpu["sub"].setText("nvidia-smi nem elérhető")

        # Tray tooltip
        self.tray.setToolTip(
            f"Z.ai | Összes: ${stats['total_cost']:.4f} | "
            f"Ma: ${stats['today_cost']:.4f} | "
            f"Session: ${stats['session_cost']:.4f}"
        )

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage("Dashboard", "A tálcára minimalizálva.", QSystemTrayIcon.Information, 2000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setQuitOnLastWindowClosed(False)

    dash = TokenDashboard()
    if "--hidden" not in sys.argv:
        dash.show()
    sys.exit(app.exec_())