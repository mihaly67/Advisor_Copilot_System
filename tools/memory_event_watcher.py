#!/usr/bin/env python3
"""
Memory Event Watcher
====================

Automatikus eseményfigyelő daemon ami a jelentős rendszer-eseményeket
érzékeli, memóriába írja őket, és figyelmeztetést generál.

Figyelt események:
  1. Új Qwen elemzés fájl (_qwen_analysis/*.md) → memória frissítés + alert
  2. Új batch_run_*.json → konszolidáció + alert
  3. Anti-hallucination REJECT/REVIEW → azonnali alert
  4. Benchmark eredmény → memória + alert
  5. GPU státusz változás (VRAM, utilization) → alert
  6. Memória corruptió → alert

Kimenetek:
  - /data/mcp_server/context/events.log         (napló, append)
  - /data/mcp_server/context/pending_alerts.json (értesítési sor)
  - /data/mcp_server/context/active_memory.json  (frissített memória)

Használat:
  # Egyszeri ellenőrzés
  python3 memory_event_watcher.py --once
  # Folyamatos figyelés (daemon mód, 30s ciklus)
  python3 memory_event_watcher.py --watch --interval 30
"""

import os
import sys
import json
import time
import glob
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, '/data/mcp_server/tools')

MEMORY_FILE = '/data/mcp_server/context/active_memory.json'
EVENTS_LOG = '/data/mcp_server/context/events.log'
ALERTS_FILE = '/data/mcp_server/context/pending_alerts.json'
STATE_FILE = '/data/mcp_server/context/watcher_state.json'
BRAIN_DIR = '/data/Brain'
CONTEXT_DIR = '/data/mcp_server/context'

SEVERITY_INFO = 'INFO'
SEVERITY_WARN = 'WARN'
SEVERITY_CRITICAL = 'CRITICAL'


class MemoryEventWatcher:
    """Figyeli a rendszer-eseményeket és automatikusan frissíti a memóriát."""

    def __init__(self):
        self.state = self._load_state()
        self.alerts = self._load_alerts()

    # ---- Állapot és alert kezelés ----

    def _load_state(self):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'seen_analysis_files': [],
                'seen_batch_files': [],
                'seen_benchmark_files': [],
                'last_gpu_check': None,
                'last_memory_hash': None,
            }

    def _save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def _load_alerts(self):
        try:
            with open(ALERTS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'pending': [], 'history': []}

    def _save_alerts(self):
        with open(ALERTS_FILE, 'w') as f:
            json.dump(self.alerts, f, ensure_ascii=False, indent=2)

    def _log_event(self, event_type, severity, message, data=None):
        ts = datetime.now(timezone.utc).isoformat()
        log_line = f"[{ts}] [{severity}] [{event_type}] {message}"
        if data:
            log_line += f" | data={json.dumps(data, ensure_ascii=False)}"
        with open(EVENTS_LOG, 'a') as f:
            f.write(log_line + '\n')

    def _add_alert(self, event_type, severity, message, data=None):
        ts = datetime.now(timezone.utc).isoformat()
        alert = {
            'timestamp': ts,
            'event_type': event_type,
            'severity': severity,
            'message': message,
            'data': data or {},
        }
        self.alerts['pending'].append(alert)
        self.alerts['history'].append(alert)
        if len(self.alerts['history']) > 200:
            self.alerts['history'] = self.alerts['history'][-200:]
        self._save_alerts()
        self._log_event(event_type, severity, message, data)
        return alert

    def dismiss_alert(self, idx):
        if 0 <= idx < len(self.alerts['pending']):
            removed = self.alerts['pending'].pop(idx)
            self._save_alerts()
            return removed
        return None

    # ---- Memória frissítés ----

    def _load_memory(self):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self._add_alert('memory_corruption', SEVERITY_CRITICAL,
                            f'Memória corrupt: {e}')
            return {}

    def _save_memory(self, mem):
        with open(MEMORY_FILE, 'w') as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)

    def _memory_hash(self, mem):
        return hashlib.md5(json.dumps(mem, sort_keys=True).encode()).hexdigest()

    def _update_memory_repo(self, mem, repo_name, analysis_file, confidence,
                            recommendation, risk_level, source='qwen_gpu'):
        if 'qwen_analyses' not in mem:
            mem['qwen_analyses'] = {}
        mem['qwen_analyses'][repo_name] = {
            'repo_path': f'{BRAIN_DIR}/{repo_name}',
            'analysis_file': analysis_file,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'confidence': confidence,
            'recommendation': recommendation,
            'risk_level': risk_level,
            'source': source,
        }
        return mem

    # ---- Esemény detektorok ----

    def _detect_new_analyses(self, mem):
        """Új _qwen_analysis/*.md fájlokat keres a /data/Brain-ben."""
        seen = set(self.state.get('seen_analysis_files', []))
        new_events = []

        for repo_dir in glob.glob(f'{BRAIN_DIR}/*/'):
            repo_name = os.path.basename(os.path.normpath(repo_dir))
            if repo_name.startswith('_'):
                continue
            for af in glob.glob(f'{repo_dir}_qwen_analysis/*.md'):
                if af not in seen:
                    new_events.append((repo_name, af))

        if new_events:
            try:
                from anti_hallucination import HallucinationDetector
            except ImportError:
                HallucinationDetector = None

            for repo_name, af in new_events:
                confidence = 0.5
                recommendation = 'UNKNOWN'
                risk_level = 'UNKNOWN'
                if HallucinationDetector:
                    try:
                        repo_path = f'{BRAIN_DIR}/{repo_name}'
                        detector = HallucinationDetector(repo_path)
                        with open(af, 'r') as f:
                            text = f.read()
                        result = detector.analyze(text, repo_name)
                        confidence = result.get('confidence', 0.5)
                        recommendation = result.get('recommendation', 'UNKNOWN')
                        risk_level = result.get('risk_level', 'UNKNOWN')
                    except Exception as e:
                        self._log_event('analysis_validation_error',
                                       SEVERITY_WARN,
                                       f'Validacios hiba: {repo_name}: {e}')

                mem = self._update_memory_repo(
                    mem, repo_name, af, confidence,
                    recommendation, risk_level)

                if recommendation == 'REJECT':
                    sev = SEVERITY_CRITICAL
                    msg = (f'UJ ELEMZES REJECT: {repo_name} '
                           f'(conf={confidence:.3f}, risk={risk_level})')
                elif recommendation == 'REVIEW':
                    sev = SEVERITY_WARN
                    msg = (f'UJ ELEMZES REVIEW: {repo_name} '
                           f'(conf={confidence:.3f})')
                else:
                    sev = SEVERITY_INFO
                    msg = (f'Uj Qwen elemzes: {repo_name} '
                           f'(conf={confidence:.3f}, {recommendation})')

                self._add_alert('new_analysis', sev, msg, {
                    'repo': repo_name,
                    'analysis_file': af,
                    'confidence': confidence,
                    'recommendation': recommendation,
                })
                seen.add(af)

        self.state['seen_analysis_files'] = sorted(seen)
        return mem

    def _detect_new_batches(self, mem):
        """Új batch_run_*.json fájlokat keres."""
        seen = set(self.state.get('seen_batch_files', []))
        batch_files = sorted(glob.glob(f'{CONTEXT_DIR}/batch_run_*.json'))

        new_batches = [bf for bf in batch_files if bf not in seen]
        if new_batches:
            total_repos = 0
            total_time = 0
            confidences = []
            for bf in new_batches:
                try:
                    with open(bf, 'r') as f:
                        results = json.load(f)
                    for r in results:
                        if r.get('source') == 'qwen_gpu':
                            total_repos += 1
                            total_time += r.get('qwen_elapsed_sec', 0)
                            confidences.append(r.get('confidence', 0))
                except (json.JSONDecodeError, TypeError):
                    pass

            avg_conf = (sum(confidences) / len(confidences)
                        if confidences else 0)

            self._add_alert('new_batch', SEVERITY_INFO,
                            f'Uj batch eredmeny: {len(new_batches)} fajl, '
                            f'{total_repos} repo, '
                            f'{total_time:.1f}s, '
                            f'atlag conf={avg_conf:.3f}', {
                                'batch_files': new_batches,
                                'total_repos': total_repos,
                                'total_time_sec': round(total_time, 1),
                                'avg_confidence': round(avg_conf, 3),
                            })

            if 'production_run' not in mem:
                mem['production_run'] = {}
            mem['production_run']['last_batch_update'] = (
                datetime.now(timezone.utc).isoformat())
            mem['production_run']['batch_files_count'] = len(batch_files)

            seen.update(new_batches)
            self.state['seen_batch_files'] = sorted(seen)

        return mem

    def _detect_new_benchmarks(self, mem):
        """Új benchmark eredményeket keres."""
        seen = set(self.state.get('seen_benchmark_files', []))
        bench_file = f'{CONTEXT_DIR}/mcts_qwen_benchmark.json'

        if os.path.exists(bench_file) and bench_file not in seen:
            try:
                with open(bench_file, 'r') as f:
                    bench = json.load(f)
                agg = bench.get('aggregate', {})
                self._add_alert('new_benchmark', SEVERITY_INFO,
                                f'Uj benchmark: token sporolas '
                                f'{agg.get("token_savings_pct", 0)}%, '
                                f'ido sporolas '
                                f'{agg.get("time_savings_pct", 0)}%', agg)
                mem['mcts_qwen_benchmark_last'] = bench.get('timestamp')
            except (json.JSONDecodeError, TypeError):
                pass
            seen.add(bench_file)
            self.state['seen_benchmark_files'] = sorted(seen)

        return mem

    def _detect_gpu_status(self, mem):
        """GPU státuszt ellenőriz nvidia-smi-vel."""
        try:
            import subprocess
            proc = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,utilization.gpu',
                 '--format=csv,noheader,nounits', '-i', '0'],
                capture_output=True, text=True, timeout=10)
            if proc.returncode == 0:
                parts = proc.stdout.strip().split(',')
                vram_mb = int(parts[0].strip())
                util_pct = int(parts[1].strip())

                last = self.state.get('last_gpu_check')
                if last:
                    prev_util = last.get('util_pct', 0)
                    if util_pct > 95 and prev_util < 50:
                        self._add_alert('gpu_spike', SEVERITY_WARN,
                                        f'GPU spike: util {prev_util}%->'
                                        f'{util_pct}%, VRAM={vram_mb}MB')
                    if vram_mb > 7000:
                        self._add_alert('gpu_vram_high', SEVERITY_WARN,
                                        f'GPU VRAM magas: {vram_mb}MB')

                self.state['last_gpu_check'] = {
                    'vram_mb': vram_mb,
                    'util_pct': util_pct,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }

                if 'gpu_status' not in mem:
                    mem['gpu_status'] = {}
                mem['gpu_status']['vram_mb'] = vram_mb
                mem['gpu_status']['util_pct'] = util_pct
                mem['gpu_status']['last_check'] = (
                    datetime.now(timezone.utc).isoformat())
        except Exception as e:
            self._log_event('gpu_check_error', SEVERITY_WARN,
                            f'nvidia-smi hiba: {e}')

        return mem

    def _detect_memory_corruption(self, mem):
        """Memória hash változást detektál."""
        try:
            current_hash = self._memory_hash(mem)
        except Exception:
            current_hash = None

        last_hash = self.state.get('last_memory_hash')
        if last_hash and current_hash and last_hash != current_hash:
            self._log_event('memory_changed', SEVERITY_INFO,
                            'Memoria modosult (hash valtozas)')
        self.state['last_memory_hash'] = current_hash
        return mem

    # ---- Fő ellenőrzés ----

    def check_once(self):
        """Egyszeri teljes ellenőrzés.

        Fontos: minden ciklus elején újratöltjük az alerteket a lemezről,
        hogy a külső módosítások (pl. cleanup script, dismiss) azonnal
        érvényre jussanak. Korábban az __init__-ben betöltött in-memory
        cache elavult maradt, és a logok helytelen countot mutattak.
        """
        self.alerts = self._load_alerts()
        self._log_event('check_start', SEVERITY_INFO,
                        f'Ellenorzes inditasa, '
                        f'{len(self.alerts.get("pending", []))} pending alert')

        mem = self._load_memory()
        if not mem:
            self._add_alert('memory_empty', SEVERITY_CRITICAL,
                            'A memoria ures vagy corrupt!')
            return False

        mem = self._detect_new_analyses(mem)
        mem = self._detect_new_batches(mem)
        mem = self._detect_new_benchmarks(mem)
        mem = self._detect_gpu_status(mem)
        mem = self._detect_memory_corruption(mem)

        self._save_memory(mem)
        self._save_state()

        pending_count = len(self.alerts.get('pending', []))
        self._log_event('check_done', SEVERITY_INFO,
                        f'Ellenorzes kesz, {pending_count} pending alert')
        return pending_count

    def watch(self, interval=30):
        """Folyamatos figyelési ciklus (daemon mód).

        SIGTERM/SIGINT jelekre kecsesen leáll (értékeli a start-stop-daemon
        és a service stop parancsot).
        """
        import signal

        # Flag a signal handler számára (a while ciklus figyeli)
        self._stop_requested = False

        def _handle_signal(signum, frame):
            self._stop_requested = True

        # SIGTERM (start-stop-daemon alapértelmezett) és SIGINT (Ctrl-C)
        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        self._add_alert('watcher_start', SEVERITY_INFO,
                        f'Memoria esemenyfigyelo elindult (interval={interval}s)')

        while not self._stop_requested:
            self.check_once()
            # Rövid alvás ciklusokban, hogy hamar reagáljon a signal-ra
            slept = 0
            while slept < interval and not self._stop_requested:
                time.sleep(1)
                slept += 1

        self._add_alert('watcher_stop', SEVERITY_INFO,
                        'Memoria esemenyfigyelo leallitva (signal)')

    def summary(self):
        """Rövid összegzés a jelenlegi állapotról."""
        mem = self._load_memory()
        pending = self.alerts.get('pending', [])
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'pending_alerts': len(pending),
            'alerts': pending[-10:],
            'memory_keys': len(mem) if mem else 0,
            'seen_analyses': len(self.state.get('seen_analysis_files', [])),
            'seen_batches': len(self.state.get('seen_batch_files', [])),
            'gpu_last': self.state.get('last_gpu_check'),
        }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Memoria esemenyfigyelo')
    parser.add_argument('--once', action='store_true',
                        help='Egyszeri ellenorzes')
    parser.add_argument('--watch', action='store_true',
                        help='Folyamatos figyeles (daemon)')
    parser.add_argument('--interval', type=int, default=30,
                        help='Ellenorzesi interval (sec, alapertelmezett 30)')
    parser.add_argument('--summary', action='store_true',
                        help='Osszegzes a jelenlegi allapotrol')
    parser.add_argument('--dismiss', type=int, default=None,
                        help='Pending alert eltavolitasa (index)')
    args = parser.parse_args()

    watcher = MemoryEventWatcher()

    if args.summary:
        s = watcher.summary()
        print(json.dumps(s, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.dismiss is not None:
        removed = watcher.dismiss_alert(args.dismiss)
        if removed:
            print(f'Eltavolitva: {removed["message"]}')
        else:
            print('Nem talalhato alert ezzel az index-szel')
        sys.exit(0)

    if args.watch:
        watcher.watch(interval=args.interval)
    else:
        pending = watcher.check_once()
        print(f'Ellenorzes kesz. {pending} pending alert.')
        s = watcher.summary()
        print(json.dumps(s, ensure_ascii=False, indent=2))





