#!/usr/bin/env python3
"""
Benchmark: MCTS-Qwen (heterogén) vs pure Qwen token használat és sebesség.

Ugyanazt a problémát lefuttatja:
  1. simulator_mode='qwen'  — pure Qwen (minden hívás tömeges rollout)
  2. simulator_mode='auto'   — heterogén (deep + rollout, adaptív switch_after)

Mérjük:
  - elapsed time (másodperc)
  - backend_calls (qwen, api)
  - becsült token fogyasztás (backend_calls * max_tokens_per_call)
  - best_path lépésszám + tartalom hossz (karakter)

Token becslés a backend konfiguráció alapján:
  - Qwen generate: 200 token, Qwen evaluate: 20 token  -> 220/hívás
  - API  generate: 400 token, API  evaluate: 300 token -> 700/hívás
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime, timezone

sys.path.insert(0, '/data/mcp_server/tools')

TOKEN_PER_CALL = {
    'qwen': {'generate': 200, 'evaluate': 20},
    'api':  {'generate': 400, 'evaluate': 300},
}

def estimate_tokens(backend_calls, hetero_stats=None):
    """Becsült token fogyasztás a backend_calls és call_trace alapján."""
    if hetero_stats and hetero_stats.get('call_trace'):
        trace = hetero_stats['call_trace']
        qwen_calls = sum(1 for t in trace if t['backend'] == 'qwen')
        api_calls = sum(1 for t in trace if t['backend'] == 'api')
        qwen_tokens = qwen_calls * (TOKEN_PER_CALL['qwen']['generate'] +
                                   TOKEN_PER_CALL['qwen']['evaluate']) / 2
        api_tokens = api_calls * (TOKEN_PER_CALL['api']['generate'] +
                                  TOKEN_PER_CALL['api']['evaluate']) / 2
        return int(qwen_tokens + api_tokens)
    qwen = backend_calls.get('qwen', 0)
    api = backend_calls.get('api', 0)
    qwen_tokens = qwen * (TOKEN_PER_CALL['qwen']['generate'] +
                          TOKEN_PER_CALL['qwen']['evaluate']) / 2
    api_tokens = api * (TOKEN_PER_CALL['api']['generate'] +
                        TOKEN_PER_CALL['api']['evaluate']) / 2
    return int(qwen_tokens + api_tokens)


def run_benchmark(problem, iterations, depth):
    """Futtatja a benchmarkot mindkét módban."""
    from reasoning_pipeline import ReasoningPipeline
    results = {}
    for mode in ['qwen', 'auto']:
        print(f"\n{'='*60}")
        print(f"  MOD: {mode.upper()}")
        print(f"{'='*60}")
        pipeline = ReasoningPipeline(
            max_iterations=iterations, max_depth=depth,
            use_qwen=True, simulator_mode=mode, export_tree=False)
        t0 = time.time()
        result = pipeline.plan(problem)
        elapsed = time.time() - t0
        backend_calls = result.get('backend_calls', {})
        hetero_stats = result.get('hetero_stats')
        tokens = estimate_tokens(backend_calls, hetero_stats)
        best_path = result.get('best_path', [])
        path_chars = sum(len(s) for s in best_path)
        results[mode] = {
            'elapsed_sec': round(elapsed, 1),
            'backend_calls': backend_calls,
            'estimated_tokens': tokens,
            'best_path_steps': len(best_path),
            'best_path_chars': path_chars,
            'switch_after': hetero_stats.get('switch_after') if hetero_stats else None,
            'tree_size': result.get('tree_size', 0),
            'mcts_available': result.get('mcts_available', False),
        }
        print(f"  Ido: {elapsed:.1f}s")
        print(f"  Backend calls: {backend_calls}")
        print(f"  Becsult tokenek: {tokens}")
        print(f"  Best path: {len(best_path)} lepes, {path_chars} karakter")
        if hetero_stats:
            print(f"  switch_after={hetero_stats.get('switch_after')}")
    return results


def compare(results):
    """Összehasonlítja a két módot."""
    q = results['qwen']
    a = results['auto']
    print(f"\n{'='*60}")
    print(f"  OSSZEHASONLITAS")
    print(f"{'='*60}")
    token_reduction = 0
    if q['estimated_tokens'] > 0:
        token_reduction = (1 - a['estimated_tokens'] /
                           q['estimated_tokens']) * 100
    speed_diff = a['elapsed_sec'] - q['elapsed_sec']
    print(f"{'Metrika':<25} {'Pure Qwen':<15} {'MCTS-Qwen':<15} {'Kulonbseg':<15}")
    print(f"{'-'*70}")
    print(f"{'Ido (s)':<25} {q['elapsed_sec']:<15} {a['elapsed_sec']:<15} "
          f"{speed_diff:+.1f}s")
    print(f"{'Becsult tokenek':<25} {q['estimated_tokens']:<15} "
          f"{a['estimated_tokens']:<15} {token_reduction:+.1f}%")
    print(f"{'Best path lepesek':<25} {q['best_path_steps']:<15} "
          f"{a['best_path_steps']:<15}")
    print(f"{'Best path karakter':<25} {q['best_path_chars']:<15} "
          f"{a['best_path_chars']:<15}")
    print(f"{'Backend (qwen)':<25} {q['backend_calls'].get('qwen',0):<15} "
          f"{a['backend_calls'].get('qwen',0):<15}")
    print(f"{'Backend (api)':<25} {q['backend_calls'].get('api',0):<15} "
          f"{a['backend_calls'].get('api',0):<15}")
    return {
        'token_reduction_pct': round(token_reduction, 1),
        'speed_diff_sec': round(speed_diff, 1),
        'pure_qwen_tokens': q['estimated_tokens'],
        'mcts_qwen_tokens': a['estimated_tokens'],
        'pure_qwen_time': q['elapsed_sec'],
        'mcts_qwen_time': a['elapsed_sec'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Benchmark: MCTS-Qwen vs pure Qwen')
    parser.add_argument('--problem', type=str, default=None,
                        help='A problema (ha nincs, --repo-bol epit)')
    parser.add_argument('--repo', type=str, default=None,
                        help='Repo neve a /data/Brain alatt')
    parser.add_argument('--iterations', type=int, default=4)
    parser.add_argument('--depth', type=int, default=3)
    args = parser.parse_args()

    if args.problem:
        problem = args.problem
    elif args.repo:
        repo_path = f'/data/Brain/{args.repo}'
        if not os.path.isdir(repo_path):
            print(f"Hiba: repo nem talalhato: {repo_path}")
            sys.exit(1)
        fc, sz = 0, 0
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')
                       and d != '_qwen_analysis']
            for f in files:
                try:
                    sz += os.path.getsize(os.path.join(root, f))
                    fc += 1
                except OSError:
                    pass
        repo_name = os.path.basename(repo_path)
        problem = (f"Hogyan elemezzuk a(z) {repo_name} repot? {fc} fajl, "
                   f"{round(sz/(1024*1024),2)} MB. Milyen strategia a "
                   f"leghatekonyabb (full Qwen vs MCTS hibrid)?")
    else:
        parser.error('--problem vagy --repo szukseges')

    print(f"BENCHMARK: MCTS-Qwen (heterogen) vs pure Qwen")
    print(f"Problema: {problem[:80]}...")
    print(f"Iteraciok: {args.iterations}, Melyseg: {args.depth}")

    results = run_benchmark(problem, args.iterations, args.depth)
    comparison = compare(results)

    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    out_file = f'/data/mcp_server/context/benchmark_mcts_vs_qwen_{ts}.json'
    with open(out_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'problem': problem,
            'iterations': args.iterations,
            'depth': args.depth,
            'pure_qwen': results['qwen'],
            'mcts_qwen': results['auto'],
            'comparison': comparison,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nEredmenyek: {out_file}")

