#!/usr/bin/env python3
"""
Master-Subagent Orchestrator
=============================

Integrates all system components into a unified Master-Subagent workflow:
1. Anti-Hallucination Detector (validates Qwen output)
2. MCTS-Qwen Bridge (token-efficient hybrid evaluation)
3. Qwen Analyzer (GPU-accelerated repo analysis, P4000)
4. Memory System (active_memory.json, qwen_memory.json)

Workflow:
Master receives request → Strategy selection → Heuristic evaluation
→ (if needed) Qwen GPU analysis → Anti-hallucination validation
→ Memory storage → Response to user
"""

import os
import sys
import json
import glob
from datetime import datetime
from typing import Optional

sys.path.insert(0, '/data/mcp_server/tools')


class MasterOrchestrator:
    """Master agent that orchestrates subagent (Qwen) tasks."""
    
    def __init__(self):
        self.memory_file = '/data/mcp_server/context/active_memory.json'
        self.analyzer_path = '/data/mcp_server/tools/qwen_analyzer.py'
        self.bridge = None  # Lazy load MCTS-Qwen Bridge
        self.detector = None  # Lazy load Anti-Hallucination Detector
        
        # Strategy thresholds
        self.small_repo_threshold = 10  # <10 files = simple
        self.large_repo_threshold = 100  # >100 files = complex
    
    def _load_bridge(self):
        """Lazy load MCTS-Qwen Bridge."""
        if self.bridge is None:
            from mcts_qwen_bridge import MCTSQwenBridge
            self.bridge = MCTSQwenBridge()
        return self.bridge
    
    def _load_detector(self, repo_path: str):
        """Lazy load Anti-Hallucination Detector for a specific repo."""
        from anti_hallucination import HallucinationDetector
        self.detector = HallucinationDetector(repo_path)
        return self.detector
    
    def select_strategy(self, repo_path: str, file_count: int, repo_size_mb: float) -> str:
        """Select analysis strategy based on repo characteristics.
        
        Returns: 'full_qwen' | 'mcts_hybrid' | 'heuristic_only' | 'cached'
        """
        # Check if already analyzed (cache)
        analysis_dir = f'{repo_path}/_qwen_analysis'
        if os.path.isdir(analysis_dir) and glob.glob(f'{analysis_dir}/*.md'):
            return 'cached'
        
        # Adaptive strategy selection (benchmark-tanult)
        try:
            from adaptive_strategy_selector import AdaptiveStrategySelector
            selector = AdaptiveStrategySelector()
            decision = selector.select(repo_path)
            strategy_map = {
                'mcts_qwen': 'mcts_hybrid',
                'full_qwen': 'full_qwen',
            }
            adaptive = strategy_map.get(decision['strategy'], 'full_qwen')
            self._last_adaptive_decision = decision
            return adaptive
        except Exception:
            # Fallback: eredeti egyszeru logika
            if file_count < self.small_repo_threshold and repo_size_mb < 5:
                return 'full_qwen'
            elif file_count > self.large_repo_threshold or repo_size_mb > 500:
                return 'mcts_hybrid'
            else:
                return 'full_qwen'
    
    def analyze_repo(self, repo_path: str, force_reanalyze: bool = False) -> dict:
        """Analyze a repository using the selected strategy.
        
        Args:
            repo_path: Path to repository
            force_reanalyze: If True, ignore cache and re-analyze
            
        Returns:
            Analysis result dict with confidence and recommendation
        """
        repo_name = os.path.basename(repo_path)
        
        # Get repo stats
        file_count = 0
        total_size = 0
        if os.path.isdir(repo_path):
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '_qwen_analysis']
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total_size += os.path.getsize(fp)
                        file_count += 1
                    except OSError:
                        pass
        repo_size_mb = total_size / (1024 * 1024)
        
        # Select strategy
        strategy = 'full_qwen' if force_reanalyze else self.select_strategy(repo_path, file_count, repo_size_mb)
        
        result = {
            'repo_name': repo_name,
            'repo_path': repo_path,
            'file_count': file_count,
            'repo_size_mb': round(repo_size_mb, 2),
            'strategy': strategy,
            'timestamp': datetime.now().isoformat()
        }
        
        if strategy == 'cached':
            # Return cached analysis
            analysis_files = sorted(glob.glob(f'{repo_path}/_qwen_analysis/*.md'))
            result['analysis_file'] = analysis_files[-1]
            result['source'] = 'cache'
            result['tokens_used'] = 0
            
            # Still run anti-hallucination on cached result
            detector = self._load_detector(repo_path)
            with open(analysis_files[-1], 'r') as f:
                analysis_text = f.read()
            validation = detector.analyze(analysis_text, repo_name)
            result['validation'] = validation
            return result
        
        if strategy == 'heuristic_only':
            bridge = self._load_bridge()
            # Get top files for heuristic evaluation
            files = []
            for root, dirs, fnames in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '_qwen_analysis']
                for f in fnames[:5]:  # Top 5 files per dir
                    files.append(os.path.join(root, f))
                    if len(files) >= 20:
                        break
                if len(files) >= 20:
                    break
            
            file_sizes = {f: os.path.getsize(f) for f in files if os.path.isfile(f)}
            eval_result = bridge.evaluate(repo_path, files, file_sizes)
            result.update(eval_result)
            result['source'] = 'heuristic'
            return result
        
        # For full_qwen and mcts_hybrid: run real Qwen analysis via subprocess
        import subprocess
        import glob as glob_mod
        
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = '0'
        env['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
        env['QWEN_GPU_LAYERS'] = '-1'
        env['QWEN_N_THREADS'] = '4'
        # Ensure the venv python is used
        env['PATH'] = '/home/Jules/jules_venv/bin:' + env.get('PATH', '')
        
        # Adjust parameters based on strategy
        max_files = 8 if strategy == 'mcts_hybrid' else 12
        max_tokens = 400 if strategy == 'mcts_hybrid' else 600
        
        # Record existing analysis files so we can detect the new one
        analysis_dir = f'{repo_path}/_qwen_analysis'
        existing_files = set(glob_mod.glob(f'{analysis_dir}/*.md')) if os.path.isdir(analysis_dir) else set()
        
        # Kontextus prioritás: releváns memória injektálása a Qwen promptba
        # (korábbi elemzések, hasonló repók tapasztalatai a ContextPrioritizer-rel)
        context_query = f"{repo_name} repository analysis"
        cmd = [
            'python3', self.analyzer_path, repo_path,
            '--max-files', str(max_files),
            '--max-tokens', str(max_tokens),
            '--context-query', context_query,
        ]
        
        result['qwen_command'] = ' '.join(cmd)
        result['max_files'] = max_files
        result['max_tokens'] = max_tokens
        result['context_query'] = context_query
        
        try:
            t0 = datetime.now()
            proc = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=300
            )
            elapsed = (datetime.now() - t0).total_seconds()
            result['qwen_elapsed_sec'] = elapsed
            result['qwen_exit_code'] = proc.returncode
            
            # Detect newly created analysis file (more robust than parsing stdout)
            current_files = set(glob_mod.glob(f'{analysis_dir}/*.md')) if os.path.isdir(analysis_dir) else set()
            new_files = current_files - existing_files
            
            if new_files:
                analysis_file = sorted(new_files)[-1]  # Latest new file
                result['analysis_file'] = analysis_file
                result['source'] = 'qwen_gpu'
                result['tokens_used'] = max_tokens
                
                # Run anti-hallucination validation on the fresh Qwen output
                detector = self._load_detector(repo_path)
                with open(analysis_file, 'r') as f:
                    analysis_text = f.read()
                validation = detector.analyze(analysis_text, repo_name)
                result['validation'] = validation
                result['confidence'] = validation['confidence']
                result['risk_level'] = validation['risk_level']
                result['recommendation'] = validation['recommendation']
            else:
                result['source'] = 'qwen_failed'
                result['error'] = 'No new analysis file created'
                result['stdout_tail'] = proc.stdout[-500:] if proc.stdout else ''
                result['stderr_tail'] = proc.stderr[-500:] if proc.stderr else ''
        except subprocess.TimeoutExpired:
            result['source'] = 'qwen_timeout'
            result['error'] = 'Qwen timed out after 300s'
        except Exception as e:
            result['source'] = 'qwen_error'
            result['error'] = str(e)
        
        return result
    
    def get_system_status(self) -> dict:
        """Get overall system status."""
        with open(self.memory_file, 'r') as f:
            mem = json.load(f)
        
        return {
            'total_repos_analyzed': mem.get('analysis_stats', {}).get('total_repos_analyzed', 0),
            'gpu_status': mem.get('gpu_status', {}),
            'monte_carlo_repo': mem.get('monte_carlo_repo', {}).get('repo_name', 'N/A'),
            'anti_hallucination': mem.get('anti_hallucination', {}).get('batch_results', {}),
            'mcts_qwen_bridge': mem.get('mcts_qwen_bridge', {}),
            'timestamp': datetime.now().isoformat()
        }

    def plan_repo_analysis(self, repo_path: str, iterations: int = 4,
                           depth: int = 3) -> dict:
        """MCTS reasoning pipeline futtatása egy repó elemzési tervéhez.

        Összeköti a reasoning-et a repókkal: a repó jellemzőiből
        (név, fájlszám, méret) problémát épít, lefuttatja a heterogén
        MCTS pipeline-t, és a tervet a repóhoz rendeli. A Qwen deep
        reasoning a gyökérnél, tömeges rollout a mélyebb szinteken.

        Returns:
            Reasoning result dict best_path + final_plan + tree_file-dal.
        """
        import os as _os
        repo_name = _os.path.basename(repo_path)

        # Repó statisztikák a probléma építéséhez
        file_count = 0
        total_size = 0
        if _os.path.isdir(repo_path):
            for root, dirs, files in _os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')
                           and d != '_qwen_analysis']
                for f in files:
                    try:
                        total_size += _os.path.getsize(
                            _os.path.join(root, f))
                        file_count += 1
                    except OSError:
                        pass
        repo_size_mb = round(total_size / (1024 * 1024), 2)

        # Probléma építése repó jellemzőkből
        problem = (f"Hogyan elemezzuk a(z) {repo_name} repot? "
                   f"{file_count} fajl, {repo_size_mb} MB. "
                   f"Milyen strategia a leghatekonyabb (full Qwen vs "
                   f"MCTS hibrid)? Mely reszeketerdemes Qwen GPU-t "
                   f"futtatni, hol eleg a heurisztika?")

        try:
            from reasoning_pipeline import ReasoningPipeline
            pipeline = ReasoningPipeline(
                max_iterations=iterations,
                max_depth=depth,
                use_qwen=True,
                simulator_mode='auto',
                export_tree=True,
            )
            result = pipeline.plan(problem)
            result['repo_name'] = repo_name
            result['repo_path'] = repo_path
            result['repo_file_count'] = file_count
            result['repo_size_mb'] = repo_size_mb
            return result
        except Exception as e:
            return {
                'repo_name': repo_name,
                'repo_path': repo_path,
                'error': f'Reasoning pipeline hiba: {e}',
                'problem': problem,
            }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Master-Subagent Orchestrator — Qwen GPU pipeline + anti-hallucination'
    )
    parser.add_argument('repo', nargs='?', default=None,
                        help='Repó neve a /data/Brain alatt (pl. mem0-aio)')
    parser.add_argument('--force', action='store_true',
                        help='Force re-analize (ignore cache, run Qwen)')
    parser.add_argument('--status', action='store_true',
                        help='Rendszer státusz riport')
    parser.add_argument('--batch', type=int, default=0,
                        help='Batch: ennyi elemezetlen/force repón futtatja a Qwent')
    parser.add_argument('--plan-repo', action='store_true',
                        help='MCTS reasoning pipeline futtatasa repó elemzési tervéhez')
    parser.add_argument('--iterations', type=int, default=4,
                        help='MCTS iteraciok (plan-repo mode, default: 4)')
    parser.add_argument('--depth', type=int, default=3,
                        help='Max fa melyseg (plan-repo mode, default: 3)')
    args = parser.parse_args()
    
    orchestrator = MasterOrchestrator()
    
    if args.status or (not args.repo and args.batch == 0 and not args.plan_repo):
        print("📊 RENDSZER STÁTUSZ")
        print("=" * 50)
        status = orchestrator.get_system_status()
        print(f"Összes repo elemzve: {status['total_repos_analyzed']}")
        print(f"GPU: {status['gpu_status'].get('gpu_name', 'N/A')} ({status['gpu_status'].get('vram_usage_mb', 0)} MB)")
        print(f"Monte Carlo repo: {status['monte_carlo_repo']}")
        ah = status.get('anti_hallucination', {})
        print(f"Anti-hallucination: {ah.get('trust_count', 0)} TRUST, {ah.get('review_count', 0)} REVIEW")
        sys.exit(0)
    
    if args.plan_repo and args.repo:
        # MCTS reasoning pipeline: repó elemzési terv
        repo_path = f'/data/Brain/{args.repo}'
        if not os.path.isdir(repo_path):
            print(f"❌ Repó nem található: {repo_path}")
            sys.exit(1)
        print(f"🧠 MCTS REASONING PIPELINE: {args.repo} (iter={args.iterations}, depth={args.depth})")
        print("=" * 60)
        result = orchestrator.plan_repo_analysis(
            repo_path, iterations=args.iterations, depth=args.depth)
        print(f"\nProbléma: {result.get('problem', 'N/A')[:80]}")
        print(f"MCTS available: {result.get('mcts_available', False)}")
        print(f"Tree size: {result.get('tree_size', 0)} csomópont")
        print(f"Backend calls: {result.get('backend_calls', {})}")
        if result.get('hetero_stats'):
            print(f"Hetero stats: {result['hetero_stats']}")
        if result.get('tree_file'):
            print(f"🌲 Fa export: {result['tree_file']}")
        print(f"\n--- LEGJOBB ÚT ({len(result.get('best_path', []))} lépés) ---")
        for i, step in enumerate(result.get('best_path', []), 1):
            print(f"  {i}. {step[:100]}")
        if result.get('tree_visualization'):
            print(f"\n--- MCTS FA ---\n{result['tree_visualization']}")
        if result.get('error'):
            print(f"\n⚠️ Hiba: {result['error']}")
        sys.exit(0)


    if args.batch > 0:
        # Batch mode: run Qwen on N repos that need (re)analysis
        all_repos = sorted([d for d in os.listdir('/data/Brain')
                           if os.path.isdir(f'/data/Brain/{d}') and d != '_qwen_analysis'])
        print(f"🚀 BATCH MODE: {args.batch} repó Qwen GPU elemzése (force={args.force})")
        print("=" * 60)
        
        results = []
        for i, repo in enumerate(all_repos[:args.batch]):
            repo_path = f'/data/Brain/{repo}'
            print(f"\n[{i+1}/{args.batch}] 🤖 Qwen elemzi: {repo}")
            print("-" * 60)
            result = orchestrator.analyze_repo(repo_path, force_reanalyze=args.force)
            
            if result.get('source') == 'qwen_gpu':
                print(f"  ✅ KÉSZ: {result.get('qwen_elapsed_sec', 0):.1f}s, "
                      f"confidence={result.get('confidence', 0):.3f} "
                      f"({result.get('recommendation', 'N/A')})")
            elif result.get('source') == 'cache':
                print(f"  💾 CACHE: {result.get('analysis_file', 'N/A')}")
                print(f"     confidence={result.get('validation', {}).get('confidence', 0):.3f}")
            else:
                print(f"  ⚠️ {result.get('source', 'unknown')}: {result.get('error', '')}")
            
            results.append(result)
        
        # Batch summary
        print("\n" + "=" * 60)
        print("📊 BATCH ÖSSZEGZÉS")
        print("=" * 60)
        qwen_runs = [r for r in results if r.get('source') == 'qwen_gpu']
        cache_hits = [r for r in results if r.get('source') == 'cache']
        failures = [r for r in results if r.get('source') not in ('qwen_gpu', 'cache')]
        
        print(f"Qwen GPU futtatások: {len(qwen_runs)}")
        print(f"Cache találatok:    {len(cache_hits)}")
        print(f"Hibák:              {len(failures)}")
        
        if qwen_runs:
            total_time = sum(r.get('qwen_elapsed_sec', 0) for r in qwen_runs)
            avg_conf = sum(r.get('confidence', 0) for r in qwen_runs) / len(qwen_runs)
            print(f"Összes Qwen idő:   {total_time:.1f}s")
            print(f"Átlag confidence:  {avg_conf:.3f}")
        
        # Save batch results
        batch_file = f'/data/mcp_server/context/batch_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(batch_file, 'w') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\nEredmények: {batch_file}")
        
        sys.exit(0)
    
    # Single repo mode
    repo_path = f'/data/Brain/{args.repo}'
    if not os.path.isdir(repo_path):
        print(f"❌ Repó nem található: {repo_path}")
        sys.exit(1)
    
    print(f"🤖 Qwen GPU elemzés: {args.repo} (force={args.force})")
    print("=" * 60)
    result = orchestrator.analyze_repo(repo_path, force_reanalyze=args.force)
    
    print(f"Stratégia: {result['strategy']}")
    print(f"Fájlok: {result['file_count']}, Méret: {result['repo_size_mb']} MB")
    print(f"Forrás: {result.get('source', 'N/A')}")
    
    if result.get('source') == 'qwen_gpu':
        print(f"Qwen idő: {result.get('qwen_elapsed_sec', 0):.1f}s")
        print(f"Elemzés fájl: {result.get('analysis_file', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 0):.3f}")
        print(f"Kockázat: {result.get('risk_level', 'N/A')}")
        print(f"Ajánlás: {result.get('recommendation', 'N/A')}")
    elif result.get('source') == 'cache':
        print(f"Elemzés fájl: {result.get('analysis_file', 'N/A')}")
        v = result.get('validation', {})
        print(f"Confidence: {v.get('confidence', 0):.3f}")
        print(f"Kockázat: {v.get('risk_level', 'N/A')}")
        print(f"Ajánlás: {v.get('recommendation', 'N/A')}")
    else:
        print(f"Hiba: {result.get('error', 'N/A')}")
