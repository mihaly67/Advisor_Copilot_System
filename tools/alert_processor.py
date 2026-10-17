#!/usr/bin/env python3
"""
Alert Processor
===============

A Master ügynök értesítési központja. Olvassa a memory_event_watcher
által generált pending_alerts.json-t, és:

  1. Priorizálja az alerteket súlyosság szerint (CRITICAL > WARN > INFO)
  2. Csoportosítja az azonos típusú alerteket (pl. 10 új elemzés -> 1 összegzés)
  3. Formázott, olvasható kimenetet ad a Masternek
  4. Feldolgozás után automatikusan eltávolítja a pending alerteket

Használat:
    python3 alert_processor.py           # megmutatja a prioritizált alerteket
    python3 alert_processor.py --process # feldolgozza + törli a pending-et
    python3 alert_processor.py --watch    # on-demand (nincs daemon, egyszeri)
"""

import os
import sys
import json
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, '/data/mcp_server/tools')

ALERTS_FILE = '/data/mcp_server/context/pending_alerts.json'

SEVERITY_ORDER = {'CRITICAL': 0, 'WARN': 1, 'INFO': 2}
SEVERITY_ICONS = {'CRITICAL': '🔴', 'WARN': '🟡', 'INFO': '🔵'}


class AlertProcessor:
    """A Master ügynök alert-feldolgozó és értesítési központja."""

    def __init__(self):
        self.alerts = self._load_alerts()

    def _load_alerts(self):
        try:
            with open(ALERTS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('pending', []), data
        except (FileNotFoundError, json.JSONDecodeError):
            return [], {'pending': [], 'history': []}

    def _save_alerts(self, data):
        with open(ALERTS_FILE, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _group_alerts(self, alerts):
        """Csoportosítja az azonos típusú alerteket."""
        grouped = defaultdict(list)
        for a in alerts:
            grouped[a['event_type']].append(a)
        return grouped

    def get_prioritized(self):
        """Visszaadja az alerteket súlyosság szerint priorizálva."""
        pending, _ = self.alerts
        return sorted(pending,
                       key=lambda a: SEVERITY_ORDER.get(a['severity'], 3))

    def get_summary(self):
        """Rövid összegzés: hány alert, milyen súlyossági eloszlás."""
        pending, _ = self.alerts
        counts = defaultdict(int)
        for a in pending:
            counts[a['severity']] += 1
        return {
            'total': len(pending),
            'critical': counts.get('CRITICAL', 0),
            'warn': counts.get('WARN', 0),
            'info': counts.get('INFO', 0),
        }

    def format_alerts(self):
        """Formázott, olvasható kimenet a Masternek."""
        pending, _ = self.alerts
        if not pending:
            return '✅ Nincs feldolgozatlan alert. A rendszer tiszta.'

        grouped = self._group_alerts(pending)
        lines = []
        lines.append(f'📋 PENDING ALERTS: {len(pending)} db')
        lines.append('=' * 60)

        # CRITICAL alertek először
        for severity in ['CRITICAL', 'WARN', 'INFO']:
            sev_alerts = [a for a in pending if a['severity'] == severity]
            if not sev_alerts:
                continue
            icon = SEVERITY_ICONS[severity]
            lines.append(f'\n{icon} {severity} ({len(sev_alerts)} db):')
            for a in sev_alerts:
                ts = a['timestamp'][:19].replace('T', ' ')
                lines.append(f'  [{ts}] {a["event_type"]}: {a["message"]}')
                if a.get('data'):
                    # Rövidített adat
                    data_str = json.dumps(a['data'], ensure_ascii=False)
                    if len(data_str) > 120:
                        data_str = data_str[:120] + '...'
                    lines.append(f'    ↳ {data_str}')

        return '\n'.join(lines)

    def process(self):
        """Feldolgozza az alerteket: megmutatja + törli a pending-et."""
        pending, data = self.alerts
        if not pending:
            return '✅ Nincs feldolgozatlan alert.'

        output = self.format_alerts()

        # Pending törlése (history-ban marad)
        data['pending'] = []
        self._save_alerts(data)

        output += f'\n\n✅ {len(pending)} alert feldolgozva és törölve a pending sorból.'
        return output

    def get_critical_alerts(self):
        """Csak a CRITICAL alerteket adja vissza."""
        pending, _ = self.alerts
        return [a for a in pending if a['severity'] == 'CRITICAL']


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Alert Processor')
    parser.add_argument('--process', action='store_true',
                        help='Feldolgozas + pending torles')
    parser.add_argument('--summary', action='store_true',
                        help='Rovind osszegzes')
    parser.add_argument('--critical', action='store_true',
                        help='Csak CRITICAL alertek')
    args = parser.parse_args()

    processor = AlertProcessor()

    if args.summary:
        s = processor.get_summary()
        print(json.dumps(s, ensure_ascii=False, indent=2))
    elif args.critical:
        crits = processor.get_critical_alerts()
        if crits:
            print(json.dumps(crits, ensure_ascii=False, indent=2))
        else:
            print('Nincs CRITICAL alert.')
    elif args.process:
        print(processor.process())
    else:
        print(processor.format_alerts())
