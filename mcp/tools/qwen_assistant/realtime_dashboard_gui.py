#!/usr/bin/env python3
"""
VALÓS IDEJŰ PYQT6 DASHBOARD - Z.ai (VSCode) + Local Qwen (GPU)
Egyszerű ablak, másodpercenként frissülő adatokkal.
"""
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtWidgets import (QApplication, QGroupBox, QLabel, QMainWindow,
                              QProgressBar, QPushButton, QVBoxLayout, QWidget)

# Hibák megjelenítése (különben a QTimer elnyeli őket)
def _excepthook(exc_type, exc_value, tb):
    print(''.join(traceback.format_exception(exc_type, exc_value, tb)), flush=True)
sys.excepthook = _excepthook

VSCODE_TASKS = '/home/Jules/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks'


def get_gpu_usage():
    try:
        r = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5)
        gpus = []
        for line in r.stdout.strip().split('\n'):
            if line.strip():
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    gpus.append({
                        'index': parts[0], 'name': parts[1],
                        'mem_used': int(parts[2]), 'mem_total': int(parts[3]),
                        'util': int(parts[4]),
                    })
        return gpus
    except Exception:
        return []


def get_zai_usage():
    if not os.path.exists(VSCODE_TASKS):
        return None
    try:
        tasks = sorted([d for d in os.listdir(VSCODE_TASKS)
                        if os.path.isdir(os.path.join(VSCODE_TASKS, d))])
        if not tasks:
            return None
        meta_path = os.path.join(VSCODE_TASKS, tasks[-1], 'task_metadata.json')
        if not os.path.exists(meta_path):
            return None
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        zai_entries = [e for e in meta.get('model_usage', [])
                       if e.get('model_provider_id') == 'zai']
        if zai_entries:
            latest = zai_entries[-1]
            return {
                'model_id': latest.get('model_id', 'unknown'),
                'total_requests': len(zai_entries),
                'last_ts': latest.get('ts', 0),
                'mode': latest.get('mode', '?'),
            }
    except Exception:
        return None
    return None


class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('🚀 Valós Idejű Dashboard - Z.ai + Qwen')
        self.setMinimumSize(700, 640)

        # Sötét téma (Catppuccin Mocha)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor('#1e1e2e'))
        pal.setColor(QPalette.ColorRole.WindowText, QColor('#cdd6f4'))
        pal.setColor(QPalette.ColorRole.Base, QColor('#181825'))
        pal.setColor(QPalette.ColorRole.Text, QColor('#cdd6f4'))
        pal.setColor(QPalette.ColorRole.Button, QColor('#313244'))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor('#cdd6f4'))
        self.setPalette(pal)

        # Állapot
        self.session_start = time.time()
        self.zai_tokens = 0
        self.zai_requests = 0
        self.zai_cost = 0.0
        self.last_zai_ts = 0
        self.qwen_tokens = {'P4000': 0, 'P2000': 0}
        self.qwen_requests = {'P4000': 0, 'P2000': 0}

        self._build_ui()


    @staticmethod
    def _box_style(color):
        return (f'QGroupBox {{ color: {color}; font-weight: bold; border: 1px solid {color};'
                f' border-radius: 6px; margin-top: 12px; padding-top: 10px; }} '
                f'QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}')

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        # Fejléc
        self.lbl_header = QLabel('⏰ Session: 00:00:00   🕒 --:--:--')
        self.lbl_header.setFont(QFont('Sans', 12, QFont.Weight.Bold))
        self.lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_header)

        # --- Z.ai szekció ---
        zai_box = QGroupBox('🔴 Z.AI (VSCode / External API)')
        zai_box.setStyleSheet(self._box_style('#f38ba8'))
        zai_lay = QVBoxLayout(zai_box)
        self.lbl_zai_model = QLabel('Model: -  |  Mode: -  |  Last: -')
        self.lbl_zai_stats = QLabel('Tokens: 0  |  Requests: 0  |  Cost: $0.0000')
        for lbl in (self.lbl_zai_model, self.lbl_zai_stats):
            lbl.setFont(QFont('Sans', 10))
            zai_lay.addWidget(lbl)
        layout.addWidget(zai_box)

        # --- GPU szekció (fix 2 sor: P4000, P2000) ---
        gpu_box = QGroupBox('🟢 LOCAL QWEN (GPU - ingyenes)')
        gpu_box.setStyleSheet(self._box_style('#a6e3a1'))
        gpu_lay = QVBoxLayout(gpu_box)
        # P4000 sor
        self.gpu_bar = {}
        self.gpu_info = {}
        for tag in ('P4000', 'P2000'):
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(True)
            info = QLabel(f'  → Tokens: 0  |  Requests: 0  |  Cost: FREE')
            info.setFont(QFont('Sans', 9))
            gpu_lay.addWidget(bar)
            gpu_lay.addWidget(info)
            self.gpu_bar[tag] = bar
            self.gpu_info[tag] = info
        layout.addWidget(gpu_box)

        # --- Összesítés ---
        sum_box = QGroupBox('💵 ÖSSZESÍTÉS')
        sum_box.setStyleSheet(self._box_style('#f9e2af'))
        sum_lay = QVBoxLayout(sum_box)
        self.lbl_totals = QLabel('Total tokens: 0  |  Total requests: 0')
        self.lbl_cost = QLabel('Total cost: $0.0000  |  Megspórolt: $0.0000 (0.0%)')
        for lbl in (self.lbl_totals, self.lbl_cost):
            lbl.setFont(QFont('Sans', 10))
            sum_lay.addWidget(lbl)
        layout.addWidget(sum_box)

        # --- Routing eloszlás ---
        route_box = QGroupBox('📊 ROUTING ELOSZLÁS (cél 70/20/10)')
        route_box.setStyleSheet(self._box_style('#89b4fa'))
        from PyQt6.QtWidgets import QGridLayout
        route_lay = QGridLayout(route_box)
        self.route_bars = {}
        self.route_labels = {}
        targets = [('P4000', 70), ('P2000', 20), ('Z.ai', 10)]
        for row, (model, target) in enumerate(targets):
            lbl_name = QLabel(f'{model} (cél: {target}%)')
            lbl_name.setFont(QFont('Sans', 10))
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(True)
            pct_lbl = QLabel('0.0%')
            pct_lbl.setFont(QFont('Sans', 10))

    def _tick(self):
        try:
            self._update_zai()
            self._update_qwen()

            # Fejléc
            dur = int(time.time() - self.session_start)
            h, m, s = dur // 3600, (dur % 3600) // 60, dur % 60
            self.lbl_header.setText(
                f'⏰ Session: {h:02d}:{m:02d}:{s:02d}   '
                f'🕒 {datetime.now().strftime("%H:%M:%S")}   🔄 1s')

            # Z.ai
            zai = get_zai_usage()
            if zai:
                ts = datetime.fromtimestamp(zai['last_ts'] / 1000).strftime('%H:%M:%S') if zai['last_ts'] else '?'
                self.lbl_zai_model.setText(
                    f'Model: {zai["model_id"]}  |  Mode: {zai["mode"]}  |  Last: {ts}')
            else:
                self.lbl_zai_model.setText('⚠️ Nincs Z.ai aktivitás a VSCode-ban')
            self.lbl_zai_stats.setText(
                f'Tokens: {self.zai_tokens}  |  Requests: {self.zai_requests}  |  Cost: ${self.zai_cost:.4f}')

            # GPU
            gpus = get_gpu_usage()
            for g in gpus:
                tag = 'P4000' if 'P4000' in g['name'] else ('P2000' if 'P2000' in g['name'] else None)
                if tag is None:
                    continue
                mem_pct = (g['mem_used'] / g['mem_total'] * 100) if g['mem_total'] else 0
                tokens = self.qwen_tokens.get(tag, 0)
                reqs = self.qwen_requests.get(tag, 0)
                self.gpu_bar[tag].setValue(int(mem_pct))
                self.gpu_bar[tag].setFormat(f'{g["name"]} - {mem_pct:.1f}% mem  |  util: {g["util"]}%')
                self.gpu_info[tag].setText(f'  → Tokens: {tokens}  |  Requests: {reqs}  |  Cost: FREE')

            # Összesítés
            total_tokens = self.zai_tokens + sum(self.qwen_tokens.values())
            total_cost = self.zai_cost
            total_reqs = self.zai_requests + sum(self.qwen_requests.values())
            self.lbl_totals.setText(f'Total tokens: {total_tokens}  |  Total requests: {total_reqs}')
            ref_cost = (total_tokens / 1000) * 0.002
            savings = ref_cost - total_cost
            pct = (savings / ref_cost * 100) if ref_cost > 0 else 0
            self.lbl_cost.setText(
                f'Total cost: ${total_cost:.4f}  |  Ref: ${ref_cost:.4f}  |  Megspórolt: ${savings:.4f} ({pct:.1f}%)')

            # Routing
            if total_reqs > 0:
                counts = {
                    'P4000': self.qwen_requests.get('P4000', 0),
                    'P2000': self.qwen_requests.get('P2000', 0),
                    'Z.ai': self.zai_requests,
                }
                for model in ('P4000', 'P2000', 'Z.ai'):
                    actual = (counts[model] / total_reqs) * 100
                    self.route_bars[model].setValue(int(actual))
                    self.route_labels[model].setText(f'{actual:.1f}%')
        except Exception:
            traceback.print_exc()

    def _update_zai(self):
        data = get_zai_usage()
        if not data:
            return
        if data['last_ts'] > self.last_zai_ts:
            new_reqs = data['total_requests'] - self.zai_requests
            if new_reqs > 0:
                est_tokens = new_reqs * 150
                self.zai_tokens += est_tokens
                self.zai_requests = data['total_requests']
                self.zai_cost += (est_tokens / 1000) * 0.002
            self.last_zai_ts = data['last_ts']

    def _update_qwen(self):
        for gpu in get_gpu_usage():
            name = gpu['name']
            mem = gpu['mem_used']
            if 'P4000' in name and mem > 50:
                self.qwen_tokens['P4000'] += int(mem / 8)
                self.qwen_requests['P4000'] += 1
            elif 'P2000' in name and mem > 500:
                self.qwen_tokens['P2000'] += int((mem - 500) / 5)
                self.qwen_requests['P2000'] += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = DashboardWindow()
    win.show()
    sys.exit(app.exec())
