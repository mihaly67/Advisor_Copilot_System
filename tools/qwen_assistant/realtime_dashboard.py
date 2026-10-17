#!/usr/bin/env python3
"""
VALÓS IDEJŰ DASHBOARD - Z.ai (VSCode) + Local Qwen (GPU)
Másodpercenként frissülő valós idejű token/cost monitor.
"""
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

VSCODE_TASKS = '/home/Jules/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks'


def get_gpu_usage():
    """Valós GPU adatok nvidia-smi-ból."""
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
                        'index': parts[0],
                        'name': parts[1],
                        'mem_used': int(parts[2]),
                        'mem_total': int(parts[3]),
                        'util': int(parts[4]),
                    })
        return gpus
    except Exception:
        return []


def get_zai_usage():
    """Z.ai használat olvasása a VSCode Cline task_metadata.json-ból."""
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
class Dashboard:
    def __init__(self):
        self.running = True
        self.session_start = time.time()
        self.zai_tokens = 0
        self.zai_requests = 0
        self.zai_cost = 0.0
        self.last_zai_ts = 0
        self.qwen_tokens = {'P4000': 0, 'P2000': 0}
        self.qwen_requests = {'P4000': 0, 'P2000': 0}
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

    def _stop(self, *a):
        self.running = False

    def update_zai(self):
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


    def update_qwen(self):
        for gpu in get_gpu_usage():
            name = gpu['name']
            mem = gpu['mem_used']
            if 'P4000' in name and mem > 50:
                self.qwen_tokens['P4000'] += int(mem / 8)
                self.qwen_requests['P4000'] += 1
            elif 'P2000' in name and mem > 500:
                self.qwen_tokens['P2000'] += int((mem - 500) / 5)
                self.qwen_requests['P2000'] += 1

    def render(self):
        sys.stdout.write('\033[2J\033[H')
        dur = int(time.time() - self.session_start)
        h, m, s = dur // 3600, (dur % 3600) // 60, dur % 60
        print('╔══════════════════════════════════════════════════════════════════════╗')
        print('║  🚀 VALÓS IDEJŰ DASHBOARD - Z.ai (VSCode) + Local Qwen (GPU)        ║')
        print('╚══════════════════════════════════════════════════════════════════════╝')
        print(f'⏰ Session: {h:02d}:{m:02d}:{s:02d}  '
              f'🕒 {datetime.now().strftime("%H:%M:%S")}  🔄 1s refresh')
        print()

        zai = get_zai_usage()
        print('🔴 Z.AI (VSCode / External API):')
        if zai:
            ts = datetime.fromtimestamp(zai['last_ts'] / 1000).strftime('%H:%M:%S') if zai['last_ts'] else '?'
            print(f'   Model: {zai["model_id"]}  |  Mode: {zai["mode"]}  |  Last: {ts}')
        else:
            print('   ⚠️  Nincs Z.ai aktivitás a VSCode-ban')
        print(f'   Tokens: {self.zai_tokens}  |  Requests: {self.zai_requests}  |  Cost: ${self.zai_cost:.4f}')
        print()

        gpus = get_gpu_usage()
        print('🟢 LOCAL QWEN (GPU - ingyenes):')
        for g in gpus:
            mem_pct = (g['mem_used'] / g['mem_total'] * 100) if g['mem_total'] else 0
            bar_len = 20
            filled = int(bar_len * mem_pct / 100)
            bar = '█' * filled + '░' * (bar_len - filled)
            tag = 'P4000' if 'P4000' in g['name'] else ('P2000' if 'P2000' in g['name'] else g['name'])
            tokens = self.qwen_tokens.get(tag, 0)
            reqs = self.qwen_requests.get(tag, 0)
            print(f'   [{g["index"]}] {g["name"]:12s} [{bar}] {mem_pct:5.1f}%  GPU util: {g["util"]:3d}%')
            print(f'       → Tokens: {tokens}  |  Requests: {reqs}  |  Cost: FREE')
        print()

        total_tokens = self.zai_tokens + sum(self.qwen_tokens.values())
        total_cost = self.zai_cost
        total_reqs = self.zai_requests + sum(self.qwen_requests.values())
        print('💵 ÖSSZESÍTÉS:')
        print(f'   Total tokens: {total_tokens}  |  Total requests: {total_reqs}')
        print(f'   Total cost: ${total_cost:.4f}')
        ref_cost = (total_tokens / 1000) * 0.002
        savings = ref_cost - total_cost
        pct = (savings / ref_cost * 100) if ref_cost > 0 else 0
        print(f'   Ref (minden Z.ai): ${ref_cost:.4f}  |  Megspórolt: ${savings:.4f} ({pct:.1f}%)')
        print()

        if total_reqs > 0:
            targets = {'P4000': 70, 'P2000': 20, 'Z.ai': 10}
            counts = {
                'P4000': self.qwen_requests.get('P4000', 0),
                'P2000': self.qwen_requests.get('P2000', 0),
                'Z.ai': self.zai_requests,
            }
            print('📊 ROUTING ELOSZLÁS (cél 70/20/10):')
            for model, target in targets.items():
                actual = (counts[model] / total_reqs) * 100
                bar_len = 20
                filled = int(bar_len * actual / 100)
                bar = '█' * filled + '░' * (bar_len - filled)
                ok = '✅' if abs(actual - target) < 15 else '❌'
                print(f'   {ok} {model:6s}: [{bar}] {actual:5.1f}%  (cél: {target}%)')
            print()

        print('─' * 72)
        print('Leállítás: Ctrl+C')

    def run(self):
        while self.running:
            self.update_zai()
            self.update_qwen()
            self.render()
            time.sleep(1)
        print('\n🛑 Dashboard leállítva.')


if __name__ == '__main__':
    Dashboard().run()
