#!/usr/bin/env python3
"""
Context Priority System
=======================

Prioritizes memory entries by relevance, recency, and confidence.
Keeps the active memory lean so the Master agent gets the most
important context first.
"""

import json
import math
import re
from datetime import datetime, timezone


class ContextPrioritizer:
    """Ranks memory entries for context injection."""

    CONFIDENCE_MAP = {'TRUST': 1.0, 'REVIEW': 0.6, 'REJECT': 0.2}
    W_RELEVANCE = 0.45
    W_RECENCY = 0.25
    W_CONFIDENCE = 0.20
    W_USAGE = 0.10
    RECENCY_HALFLIFE_DAYS = 7.0

    def __init__(self, memory_file='/data/mcp_server/context/active_memory.json'):
        self.memory_file = memory_file
        self._load_memory()
        self.usage_counts = {}

    def _load_memory(self):
        with open(self.memory_file, 'r') as f:
            self.memory = json.load(f)

    def _extract_text(self, entry):
        parts = []
        for key in ('description', 'repo_name', 'repo_path', 'analysis_file',
                    'thought', 'name', 'type', 'language'):
            val = entry.get(key)
            if val:
                parts.append(str(val))
        for key in ('key_findings', 'hallucination_detected', 'actual_files',
                    'token_efficient_patterns', 'key_classes'):
            vals = entry.get(key)
            if isinstance(vals, list):
                parts.extend(str(v) for v in vals)
        return ' '.join(parts).lower()

    def _relevance_score(self, query, entry_text):
        if not query:
            return 0.0
        query_words = set(re.findall(r'\w+', query.lower()))
        if not query_words:
            return 0.0
        entry_words = set(re.findall(r'\w+', entry_text))
        overlap = query_words & entry_words
        return len(overlap) / len(query_words)

    def _recency_score(self, timestamp_str):
        if not timestamp_str:
            return 0.0
        try:
            ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return 0.0
        now = datetime.now(timezone.utc)
        # Handle naive datetimes (no timezone)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age_days = (now - ts).total_seconds() / 86400.0
        return math.exp(-0.693 * age_days / self.RECENCY_HALFLIFE_DAYS)

    def _confidence_score(self, entry):
        rec = entry.get('recommendation')
        if rec in self.CONFIDENCE_MAP:
            return self.CONFIDENCE_MAP[rec]
        conf = entry.get('confidence')
        if isinstance(conf, (int, float)):
            return float(conf)
        risk = entry.get('risk_level', '')
        if risk == 'LOW':
            return 0.9
        if risk == 'MEDIUM':
            return 0.6
        if risk == 'HIGH':
            return 0.2
        return 0.5

    def _usage_score(self, key):
        count = self.usage_counts.get(key, 0)
        return min(1.0, count / 10.0)

    def rank(self, query, max_entries=20):
        candidates = []
        sources = [
            ('qwen_analyses', self.memory.get('qwen_analyses', {})),
            ('deep_analyses', {i: e for i, e in enumerate(self.memory.get('deep_analyses', []))}),
            ('repositories', self.memory.get('repositories', {})),
            ('reasoning_repos', {i: e for i, e in enumerate(self.memory.get('reasoning_repos', []))}),
        ]
        for source_name, section in sources:
            if not isinstance(section, dict):
                continue
            for key, entry in section.items():
                if not isinstance(entry, dict):
                    continue
                entry_text = self._extract_text(entry)
                rel = self._relevance_score(query, entry_text)
                rec = self._recency_score(entry.get('timestamp', ''))
                conf = self._confidence_score(entry)
                usage = self._usage_score(f'{source_name}:{key}')
                score = (self.W_RELEVANCE * rel + self.W_RECENCY * rec +
                         self.W_CONFIDENCE * conf + self.W_USAGE * usage)
                candidates.append({
                    'key': key, 'source': source_name, 'entry': entry,
                    'score': round(score, 4),
                    'breakdown': {'relevance': round(rel, 3), 'recency': round(rec, 3),
                                  'confidence': round(conf, 3), 'usage': round(usage, 3)},
                })
        candidates.sort(key=lambda c: c['score'], reverse=True)
        return candidates[:max_entries]

    def build_context(self, query, max_entries=10, max_chars=4000):
        ranked = self.rank(query, max_entries=max_entries)
        lines = [f'# Kontextus (query: "{query}")', '']
        total = 0
        for c in ranked:
            e = c['entry']
            src = c['source']
            desc = e.get('description') or e.get('name') or e.get('repo_name') or str(c['key'])
            conf = e.get('confidence', c['breakdown']['confidence'])
            line = f"- [{src}] {desc} (score={c['score']}, conf={conf})"
            if len(line) + total > max_chars:
                break
            lines.append(line)
            total += len(line)
        return '\n'.join(lines)


if __name__ == '__main__':
    cp = ContextPrioritizer()
    query = 'Tree of Thoughts reasoning orchestration Monte Carlo'
    print(f"Query: {query}\n")
    ranked = cp.rank(query, max_entries=10)
    print(f"Top {len(ranked)} entries:\n")
    for c in ranked:
        e = c['entry']
        desc = e.get('description') or e.get('name') or e.get('repo_name') or c['key']
        print(f"  [{c['source']}] {desc}")
        print(f"    score={c['score']} | rel={c['breakdown']['relevance']} "
              f"rec={c['breakdown']['recency']} conf={c['breakdown']['confidence']}")
    print("\n--- Kontextus blokk ---\n")
    print(cp.build_context(query))
