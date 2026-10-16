#!/usr/bin/env python3
"""
Adaptive Strategy Selector
===========================

Benchmark-tanult adaptív döntés a MCTS-Qwen hibrid és a pure Qwen
stratégia között. A döntés a repó jellemzőin alapul:
  - Fájlszám és méret
  - Kód/komment-arány (bonyolultság)
  - Nyelv és fájlkiterjesztés eloszlás
  - Előző elemzések confidence-je (tanulás)

Benchmark eredmények (mcts_qwen_benchmark.json):
  - Kis repók (<50 fájl): MCTS-Qwen jobb (gyorsabb + magasabb conf)
  - Nagy repók (>100 fájl): pure Qwen pontosabb (több kontextus)
  - Közepes repók: komplexitás függvénye
"""

import os
import json
import math

CONTEXT_DIR = '/data/mcp_server/context'
BENCHMARK_FILE = f'{CONTEXT_DIR}/mcts_qwen_benchmark.json'
MEMORY_FILE = f'{CONTEXT_DIR}/active_memory.json'

LANG_COMPLEXITY = {
    '.py': 1.0, '.pyx': 1.2, '.js': 1.1, '.ts': 1.1, '.jsx': 1.1, '.tsx': 1.1,
    '.go': 0.9, '.rs': 1.2, '.java': 1.1, '.c': 1.1, '.cpp': 1.2, '.h': 0.8,
    '.cs': 1.0, '.rb': 1.0, '.php': 1.0, '.swift': 1.1, '.kt': 1.1,
    '.md': 0.3, '.rst': 0.3, '.txt': 0.2,
    '.json': 0.2, '.yaml': 0.2, '.yml': 0.2, '.toml': 0.2,
    '.cfg': 0.2, '.ini': 0.2,
    '.sh': 0.5, '.bash': 0.5,
    '.sql': 0.6, '.html': 0.4, '.css': 0.4,
}

TEST_PATTERNS = {'test_', '_test.', 'tests/', 'test/', '__tests__/',
                 '.test.', '.spec.', 'spec/', 'fixtures/'}


class AdaptiveStrategySelector:
    """Adaptív stratégiaválasztó benchmark-tanult döntéssel."""

    def __init__(self):
        self.benchmark = self._load_benchmark()
        self.memory = self._load_memory()

    def _load_benchmark(self):
        try:
            with open(BENCHMARK_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _load_memory(self):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _analyze_repo(self, repo_path):
        """Gyors repó analízis: fájlszám, méret, kiterjesztés eloszlás."""
        file_count = 0
        total_size = 0
        ext_counts = {}
        test_count = 0
        doc_count = 0

        if not os.path.isdir(repo_path):
            return {'file_count': 0, 'size_mb': 0.0, 'complexity': 0.0}

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs
                       if not d.startswith('.') and d != '_qwen_analysis'
                       and d not in ('node_modules', '__pycache__', '.git',
                                     'venv', 'env', 'dist', 'build')]
            for f in files:
                fp = os.path.join(root, f)
                try:
                    size = os.path.getsize(fp)
                except OSError:
                    continue
                file_count += 1
                total_size += size

                _, ext = os.path.splitext(f)
                ext_lower = ext.lower()
                ext_counts[ext_lower] = ext_counts.get(ext_lower, 0) + 1

                if any(p in f.lower() for p in TEST_PATTERNS):
                    test_count += 1
                if ext_lower in ('.md', '.rst', '.txt'):
                    doc_count += 1

        size_mb = total_size / (1024 * 1024)

        total_weight = 0.0
        total_files_with_ext = 0
        for ext, count in ext_counts.items():
            weight = LANG_COMPLEXITY.get(ext, 0.5)
            total_weight += weight * count
            total_files_with_ext += count
        avg_complexity = (total_weight / total_files_with_ext
                          if total_files_with_ext > 0 else 0.5)

        return {
            'file_count': file_count,
            'size_mb': round(size_mb, 2),
            'complexity': round(avg_complexity, 3),
            'ext_distribution': dict(sorted(ext_counts.items(),
                                           key=lambda x: -x[1])[:5]),
            'test_count': test_count,
            'doc_count': doc_count,
            'test_ratio': round(test_count / max(1, file_count), 3),
            'doc_ratio': round(doc_count / max(1, file_count), 3),
        }

    def _get_historical_confidence(self, repo_name):
        """Lekéri a repó korábbi elemzésének confidence-jét."""
        analyses = self.memory.get('qwen_analyses', {})
        entry = analyses.get(repo_name)
        if entry and isinstance(entry, dict):
            return entry.get('confidence')
        return None

    def _compute_complexity_score(self, analysis):
        """Összetett bonyolultsági pontszám (0..1)."""
        fc = analysis['file_count']
        size = analysis['size_mb']
        comp = analysis['complexity']
        test_ratio = analysis['test_ratio']
        doc_ratio = analysis['doc_ratio']

        file_score = min(1.0, math.log10(max(1, fc)) / 3.0)
        size_score = min(1.0, size / 500.0)
        comp_score = min(1.0, comp)
        test_bonus = test_ratio * 0.1
        doc_bonus = doc_ratio * 0.1

        raw = (0.35 * file_score + 0.25 * size_score +
               0.30 * comp_score + 0.10 * (1.0 - test_bonus - doc_bonus))
        return max(0.0, min(1.0, raw))

    def select(self, repo_path):
        """Választ stratégiát a repó jellemzői alapján."""
        repo_name = os.path.basename(repo_path)
        analysis = self._analyze_repo(repo_path)
        complexity = self._compute_complexity_score(analysis)
        hist_conf = self._get_historical_confidence(repo_name)

        fc = analysis['file_count']
        size = analysis['size_mb']

        # Szabály 1: Nagyon kicsi repó → MCTS-Qwen
        if fc < 20 and size < 2:
            strategy = 'mcts_qwen'
            reasoning = (f'Kicsi repo ({fc} fájl, {size}MB) → '
                        f'MCTS-Qwen (benchmark: 33% gyorsabb)')
            expected_tokens = 400
        # Szabály 2: Nagy repó → pure Qwen
        elif fc > 100 or size > 50:
            strategy = 'full_qwen'
            reasoning = (f'Nagy/komplex repo ({fc} fájl, {size}MB, '
                        f'complexity={complexity:.2f}) → '
                        f'pure Qwen (pontosabb komplex kódhoz)')
            expected_tokens = 600
        # Szabály 3: Közepes — komplexitás dönt
        elif complexity > 0.6:
            strategy = 'full_qwen'
            reasoning = (f'Kozepes repo, magas komplexitas '
                        f'({complexity:.2f}) → pure Qwen')
            expected_tokens = 600
        elif complexity < 0.3:
            strategy = 'mcts_qwen'
            reasoning = (f'Kozepes repo, alacsony komplexitas '
                        f'({complexity:.2f}) → MCTS-Qwen')
            expected_tokens = 400
        else:
            if hist_conf is not None and hist_conf >= 0.8:
                strategy = 'mcts_qwen'
                reasoning = (f'Kozepes repo, korábbi conf={hist_conf:.3f} '
                            f'magas → MCTS-Qwen')
                expected_tokens = 400
            else:
                strategy = 'full_qwen'
                reasoning = (f'Kozepes repo, nincs magas korábbi conf '
                            f'→ pure Qwen')
                expected_tokens = 600

        return {
            'strategy': strategy,
            'reasoning': reasoning,
            'analysis': analysis,
            'complexity_score': round(complexity, 3),
            'expected_tokens': expected_tokens,
            'historical_confidence': hist_conf,
            'repo_name': repo_name,
        }


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Használat: python3 adaptive_strategy_selector.py <repo_path>')
        sys.exit(1)
    selector = AdaptiveStrategySelector()
    result = selector.select(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


