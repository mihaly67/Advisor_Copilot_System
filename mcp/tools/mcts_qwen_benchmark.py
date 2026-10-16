#!/usr/bin/env python3
"""
MCTS-Qwen vs Pure Qwen Benchmark
=================================

Compares token usage, time, and accuracy between:
  1. Pure Qwen: full repo analysis (orchestrator's full_qwen strategy)
  2. MCTS-Qwen hybrid: heuristic → cache → Qwen (only when needed)

Metrics:
  - Tokens used (prompt + completion budget)
  - Wall-clock time
  - Confidence score (from anti-hallucination)

Expected outcome: MCTS-Qwen uses fewer tokens for high-confidence repos
(heuristic-only path), comparable accuracy for ambiguous repos.
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, '/data/mcp_server/tools')

from mcts_qwen_bridge import MCTSQwenBridge, HeuristicEvaluator
from master_orchestrator import MasterOrchestrator


def collect_files(repo_path, max_files=20):
    """Collect a representative file sample for the bridge."""
    files = []
    file_sizes = {}
    for root, dirs, fnames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '_qwen_analysis']
        for f in fnames:
            fp = os.path.join(root, f)
            try:
                file_sizes[fp] = os.path.getsize(fp)
                files.append(fp)
                if len(files) >= max_files:
                    return files[:max_files], {f: file_sizes[f] for f in files[:max_files]}
            except OSError:
                pass
    return files[:max_files], {f: file_sizes.get(f, 0) for f in files[:max_files]}


def run_pure_qwen(repo_path):
    """Run pure Qwen analysis via orchestrator (full_qwen strategy)."""
    orch = MasterOrchestrator()
    t0 = time.time()
    result = orch.analyze_repo(repo_path, force_reanalyze=True)
    elapsed = time.time() - t0
    return {
        'method': 'pure_qwen',
        'elapsed_sec': result.get('qwen_elapsed_sec', elapsed),
        'tokens_used': result.get('max_tokens', 600),
        'confidence': result.get('confidence', 0.5),
        'source': result.get('source'),
        'analysis_file': result.get('analysis_file'),
    }


def run_mcts_qwen(repo_path):
    """Run MCTS-Qwen hybrid evaluation."""
    bridge = MCTSQwenBridge()
    files, file_sizes = collect_files(repo_path, max_files=20)
    t0 = time.time()
    result = bridge.evaluate(repo_path, files, file_sizes)
    elapsed = time.time() - t0
    return {
        'method': 'mcts_qwen',
        'elapsed_sec': elapsed,
        'tokens_used': result.get('qwen_tokens', 0) if result.get('source') == 'qwen_evaluated' else 0,
        'confidence': result.get('final_score', 0.5),
        'source': result.get('source'),
        'heuristic_score': result.get('heuristic_score'),
        'cache_hit': result.get('cache_hit'),
        'files_evaluated': len(files),
    }


def benchmark(repo_names):
    """Run benchmark on a list of repos."""
    results = []
    print('=' * 70)
    print('🔬 MCTS-QWEN vs PURE QWEN BENCHMARK')
    print('=' * 70)

    for name in repo_names:
        repo_path = f'/data/Brain/{name}'
        if not os.path.isdir(repo_path):
            print(f'\n⚠️  Repo nem található: {name}, kihagyva')
            continue

        print(f'\n📁 {name}')
        print('-' * 70)

        # Clear cache for fair comparison
        cache_file = '/data/mcp_server/context/qwen_evaluations.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)

        # Remove existing analysis files to force fresh Qwen runs
        analysis_dir = f'{repo_path}/_qwen_analysis'
        if os.path.isdir(analysis_dir):
            import shutil
            shutil.rmtree(analysis_dir)

        # Run MCTS-Qwen hybrid
        print('  🤖 MCTS-Qwen hibrid futtatás...')
        mcts_result = run_mcts_qwen(repo_path)
        print(f"     Forrás: {mcts_result['source']}, "
              f"{mcts_result['elapsed_sec']:.1f}s, "
              f"{mcts_result['tokens_used']} token, "
              f"conf={mcts_result['confidence']:.3f}")

        # Clear analysis for pure Qwen run
        if os.path.isdir(analysis_dir):
            import shutil
            shutil.rmtree(analysis_dir)

        # Run pure Qwen
        print('  🤖 Pure Qwen futtatás...')
        pure_result = run_pure_qwen(repo_path)
        print(f"     Forrás: {pure_result['source']}, "
              f"{pure_result['elapsed_sec']:.1f}s, "
              f"{pure_result['tokens_used']} token, "
              f"conf={pure_result['confidence']:.3f}")

        # Compute savings
        token_savings = pure_result['tokens_used'] - mcts_result['tokens_used']
        token_savings_pct = (token_savings / pure_result['tokens_used'] * 100) if pure_result['tokens_used'] > 0 else 0
        time_diff = mcts_result['elapsed_sec'] - pure_result['elapsed_sec']

        results.append({
            'repo': name,
            'mcts_qwen': mcts_result,
            'pure_qwen': pure_result,
            'token_savings': token_savings,
            'token_savings_pct': round(token_savings_pct, 1),
            'time_diff_sec': round(time_diff, 1),
        })

    # Summary
    print('\n' + '=' * 70)
    print('📊 BENCHMARK ÖSSZEGZÉS')
    print('=' * 70)
    print(f"{'Repo':<25} {'MCTS token':<12} {'Pure token':<12} {'Megtakarítás':<15} {'MCTS idő':<10} {'Pure idő':<10}")
    print('-' * 84)
    for r in results:
        print(f"{r['repo'][:25]:<25} "
              f"{r['mcts_qwen']['tokens_used']:<12} "
              f"{r['pure_qwen']['tokens_used']:<12} "
              f"{r['token_savings']} ({r['token_savings_pct']}%){'':<3} "
              f"{r['mcts_qwen']['elapsed_sec']:<10.1f} "
              f"{r['pure_qwen']['elapsed_sec']:<10.1f}")

    # Aggregate
    total_mcts_tokens = sum(r['mcts_qwen']['tokens_used'] for r in results)
    total_pure_tokens = sum(r['pure_qwen']['tokens_used'] for r in results)
    total_mcts_time = sum(r['mcts_qwen']['elapsed_sec'] for r in results)
    total_pure_time = sum(r['pure_qwen']['elapsed_sec'] for r in results)
    print('-' * 84)
    print(f"{'ÖSSZESEN':<25} "
          f"{total_mcts_tokens:<12} "
          f"{total_pure_tokens:<12} "
          f"{total_pure_tokens - total_mcts_tokens} ({(total_pure_tokens - total_mcts_tokens) / max(1, total_pure_tokens) * 100:.1f}%){'':<3} "
          f"{total_mcts_time:<10.1f} "
          f"{total_pure_time:<10.1f}")

    # Save results
    out_file = '/data/mcp_server/context/mcts_qwen_benchmark.json'
    with open(out_file, 'w') as f:
        json.dump({'timestamp': datetime.now().isoformat(), 'results': results},
                  f, ensure_ascii=False, indent=2)
    print(f'\n💾 Eredmények: {out_file}')

    return results


if __name__ == '__main__':
    # Benchmark on a sample of repos (small for time efficiency)
    sample_repos = ['yggdrasil-mcp', 'mem0-aio']
    benchmark(sample_repos)
