"""
MCTS-Qwen Bridge
=================

Adapter between MCTS tree reasoning and Qwen GPU-accelerated analysis.
Token-efficient hybrid evaluation with caching.
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Any, Callable, Optional
import random


class HeuristicEvaluator:
    """Fast file-based scoring without GPU calls."""
    
    PYTHON_EXTENSIONS = {'.py', '.pyx', '.pyi'}
    CODE_EXTENSIONS = {'.js', '.ts', '.go', '.rust', '.java', '.cpp', '.c', '.h'}
    META_EXTENSIONS = {'.md', '.rst', '.txt', '.yaml', '.yml', '.toml', '.json', '.cfg', '.ini'}
    TEST_PATTERNS = {'test_', '_test.', 'tests/', 'test/', '__tests__/'}
    
    @classmethod
    def score_file(cls, file_path: str, file_size: int) -> float:
        """Score a single file using heuristic rules."""
        score = 0.5
        basename = os.path.basename(file_path)
        _, ext = os.path.splitext(basename)
        
        if ext.lower() in cls.PYTHON_EXTENSIONS:
            score += 0.2
        elif ext.lower() in cls.CODE_EXTENSIONS:
            score += 0.15
        elif ext.lower() in cls.META_EXTENSIONS:
            score += 0.1
        
        if any(p in basename.lower() for p in cls.TEST_PATTERNS):
            score += 0.15
        
        if file_size > 10 * 1024 * 1024:
            score -= 0.2
        elif file_size < 1024:
            score -= 0.1
        
        if not ext:
            score -= 0.05
        
        return max(0.0, min(1.0, score))


class QwenCache:
    """Cache layer for Qwen evaluations."""
    
    def __init__(self, cache_file: str = '/data/mcp_server/context/qwen_evaluations.json'):
        self.cache_file = cache_file
        self.cache: dict[str, dict] = self._load_cache()
    
    def _load_cache(self) -> dict[str, dict]:
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_cache(self) -> None:
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _hash_context(self, repo_path: str, files: list[str]) -> str:
        content = f"{repo_path}|{','.join(sorted(files))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def lookup(self, repo_path: str, files: list[str]) -> Optional[dict]:
        key = self._hash_context(repo_path, files)
        return self.cache.get(key)
    
    def store(self, repo_path: str, files: list[str],
              heuristic_score: float, qwen_score: float,
              qwen_tokens: int, timestamp: str) -> None:
        key = self._hash_context(repo_path, files)
        self.cache[key] = {
            'repo_path': repo_path,
            'heuristic_score': heuristic_score,
            'qwen_score': qwen_score,
            'qwen_tokens': qwen_tokens,
            'timestamp': timestamp
        }
        self._save_cache()


class MCTSQwenBridge:
    """Main bridge between MCTS and Qwen."""
    
    def __init__(self, heuristic_threshold: float = 0.6,
                 qwen_required_threshold: float = 0.4,
                 cache_file: str = '/data/mcp_server/context/qwen_evaluations.json'):
        self.heuristic_evaluator = HeuristicEvaluator()
        self.cache = QwenCache(cache_file)
        self.heuristic_threshold = heuristic_threshold
        self.qwen_required_threshold = qwen_required_threshold
    def _call_qwen_subprocess(self, repo_path, files, max_files=8, max_tokens=400):
        """Call real Qwen analyzer via subprocess (same pattern as orchestrator)."""
        import subprocess
        import glob as glob_mod
        from datetime import datetime as _dt

        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = '0'
        env['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
        env['QWEN_GPU_LAYERS'] = '-1'
        env['QWEN_N_THREADS'] = '4'
        env['PATH'] = '/home/Jules/jules_venv/bin:' + env.get('PATH', '')

        analysis_dir = f'{repo_path}/_qwen_analysis'
        existing = set(glob_mod.glob(f'{analysis_dir}/*.md')) if os.path.isdir(analysis_dir) else set()

        analyzer = '/data/mcp_server/tools/qwen_analyzer.py'
        cmd = ['python3', analyzer, repo_path,
               '--max-files', str(max_files),
               '--max-tokens', str(max_tokens)]

        t0 = _dt.now()
        try:
            proc = subprocess.run(cmd, env=env, capture_output=True,
                                  text=True, timeout=300)
            elapsed = (_dt.now() - t0).total_seconds()
        except subprocess.TimeoutExpired:
            return {'qwen_score': 0.5, 'qwen_tokens': max_tokens,
                    'elapsed_sec': 300, 'analysis_file': None, 'error': 'timeout'}

        current = set(glob_mod.glob(f'{analysis_dir}/*.md')) if os.path.isdir(analysis_dir) else set()
        new_files = current - existing
        analysis_file = sorted(new_files)[-1] if new_files else None

        # Run anti-hallucination to get a real confidence score
        qwen_score = 0.5
        if analysis_file:
            try:
                import sys as _sys
                _sys.path.insert(0, '/data/mcp_server/tools')
                from anti_hallucination import HallucinationDetector
                detector = HallucinationDetector(repo_path)
                with open(analysis_file) as f:
                    text = f.read()
                result = detector.analyze(text, os.path.basename(repo_path))
                qwen_score = result.get('confidence', 0.5)
            except Exception:
                pass

        return {
            'qwen_score': qwen_score,
            'qwen_tokens': max_tokens,
            'elapsed_sec': elapsed,
            'analysis_file': analysis_file,
        }


    
    def evaluate(self, repo_path: str, files: list[str],
                 file_sizes: dict[str, int]) -> dict:
        """Evaluate repository using hybrid strategy."""
        # Heuristic scoring
        heuristic_scores = []
        for f in files:
            size = file_sizes.get(f, 0)
            if os.path.isfile(f):
                score = self.heuristic_evaluator.score_file(f, size)
            else:
                score = 0.5
            heuristic_scores.append(score)
        
        avg_heuristic = sum(heuristic_scores) / len(heuristic_scores) if heuristic_scores else 0
        
        # Cache lookup
        cached = self.cache.lookup(repo_path, files)
        if cached:
            return {
                'final_score': cached['qwen_score'],
                'heuristic_score': avg_heuristic,
                'source': 'cache',
                'cache_hit': True
            }
        
        # Threshold-based decisions
        if avg_heuristic >= self.heuristic_threshold:
            return {
                'final_score': avg_heuristic,
                'heuristic_score': avg_heuristic,
                'source': 'heuristic_only',
                'cache_hit': False
            }
        
        if avg_heuristic <= self.qwen_required_threshold:
            return {
                'final_score': avg_heuristic,
                'heuristic_score': avg_heuristic,
                'source': 'pruned',
                'cache_hit': False
            }
        
        # Qwen evaluation (real subprocess call)
        qwen_result = self._call_qwen_subprocess(repo_path, files)
        qwen_score = qwen_result.get('qwen_score', avg_heuristic)
        qwen_tokens = qwen_result.get('qwen_tokens', 400)
        qwen_elapsed = qwen_result.get('elapsed_sec', 0)
        self.cache.store(repo_path, files, avg_heuristic, qwen_score, qwen_tokens, datetime.now().isoformat())
        
        return {
            'final_score': (avg_heuristic + qwen_score) / 2,
            'heuristic_score': avg_heuristic,
            'qwen_score': qwen_score,
            'qwen_tokens': qwen_tokens,
            'qwen_elapsed_sec': qwen_elapsed,
            'analysis_file': qwen_result.get('analysis_file'),
            'source': 'qwen_evaluated',
            'cache_hit': False
        }


if __name__ == "__main__":
    bridge = MCTSQwenBridge()
    result = bridge.evaluate("/data/Brain/mem0-aio", ["/data/Brain/mem0-aio/README.md"], {"/data/Brain/mem0-aio/README.md": 5000})
    print(f"Result: {result}")
    print(f"Cache stats: {len(bridge.cache.cache)}")
