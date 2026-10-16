#!/usr/bin/env python3
"""UCB1 és pruning stratégiák tesztelése az MCTS engine-en."""
import sys, time, json, argparse
from datetime import datetime, timezone
sys.path.insert(0, '/data/Brain/agentic-os-core/src')
sys.path.insert(0, '/data/mcp_server/tools')


class MockBackend:
    """Gyors szimulált backend (nem hív Qwen-t).

    A kandidátumok MÉLYSÉGFÜGGŐEK — a state-ben lévő last_thought
    alapján különböző tartalmat generál, így a fa csomópontjai egyediek.
    A score a kandidátum betűjétől függ (A=magas, E=alacsony).
    """
    CANDIDATE_QUALITY = {
        'A': 0.85,
        'B': 0.60,
        'C': 0.45,
        'D': 0.30,
        'E': 0.15,
    }

    def __init__(self):
        self.call_count = 0

    def evaluate(self, state, thought):
        self.call_count += 1
        for letter, quality in self.CANDIDATE_QUALITY.items():
            tag = f'_{letter}:'
            if tag in thought:
                noise = (self.call_count % 7) / 100.0
                return max(0.0, min(1.0, quality + noise - 0.03))
        score = 0.3 + (len(thought) % 50) / 100
        return max(0.0, min(1.0, score))

    def generate_candidates(self, state):
        problem = state.get('problem', 'ismeretlen')
        last = state.get('last_thought', '')
        # Mélység kiszámítása a last_thought prefixből (d0_, d1_, ...)
        import re
        m = re.search(r'd(\d+)_', last)
        depth = int(m.group(1)) + 1 if m else 0
        return [
            f"d{depth}_{letter}: {problem[:10]}"
            for letter in self.CANDIDATE_QUALITY
        ]


def test_exploration_weights(problem, iterations, depth):
    """Teszteli különböző exploration_weight (c) értékeket."""
    from agentic_os.core.tree.mcts import MCTS
    weights = [0.1, 0.5, 1.0, 1.414, 2.0]
    results = {}
    print(f"\n{'='*70}")
    print(f"  TESZT 1: Exploration Weight (c) hatasa")
    print(f"{'='*70}")
    print(f"{'c':<8} {'Ido(s)':<10} {'Fa meret':<10} {'Best path':<12} {'Avg score':<10}")
    print(f"{'-'*60}")
    for c in weights:
        backend = MockBackend()
        mcts = MCTS(exploration_weight=c, max_iterations=iterations,
                    max_depth=depth)
        evaluator = lambda state, thought: backend.evaluate(state, thought)
        generator = lambda state: backend.generate_candidates(state)
        t0 = time.time()
        tree = mcts.search(root_thought=problem,
                           root_state={'problem': problem},
                           generator=generator, evaluator=evaluator)
        elapsed = time.time() - t0
        best_path = tree.get_best_path() if hasattr(tree, 'get_best_path') else []
        path_texts = [n.thought for n in best_path] if best_path else []
        if best_path:
            avg_scores = [n.avg_score for n in best_path]
            avg_best = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        else:
            avg_best = 0
        results[c] = {
            'elapsed_sec': round(elapsed, 3),
            'tree_size': getattr(tree, '_size', 0),
            'best_path_steps': len(path_texts),
            'avg_score': round(avg_best, 4),
        }
        print(f"{c:<8} {elapsed:<10.3f} {results[c]['tree_size']:<10} "
              f"{len(path_texts):<12} {avg_best:<10.4f}")
    return results

def test_pruning(problem, iterations, depth):
    """Pruning tesztje manuálisan felépített, elágazó fával.

    Az agentic-os-core MCTS implementáció láncot épít (egy gyerek
    iterációnként, mindig a legmélyebb levélig megy le), ezért itt
    egy elágazó fát építünk kézzel ismert score-okkal, hogy a
    pruning valóban eltávolítson alacsony scoreú ágakat.
    """
    from agentic_os.core.tree.thought_tree import ThoughtTree
    print(f"\n{'='*70}")
    print(f"  TESZT 2: Pruning hatasa (manualis elagazo fa)")
    print(f"{'='*70}")

    # Fa építése: root → 5 gyermek, mindegyiknek 2 unokája
    # A-E gyermekek ismert score-okkal (A=0.85, E=0.15)
    qualities = {'A': 0.85, 'B': 0.60, 'C': 0.45, 'D': 0.30, 'E': 0.15}

    def build_tree():
        tree = ThoughtTree(max_depth=3, max_children=20)
        root = tree.set_root(problem, {'problem': problem})
        root.visits = 10  # szimulált látogatottság
        for letter, q in qualities.items():
            child = tree.add_thought(
                root, f'd1_{letter}: {problem[:10]}',
                {'problem': problem, 'last_thought': f'd1_{letter}'},
                score=q * 5)  # cumulative score (visits=5)
            child.visits = 5
            # Minden gyermeknek 2 unokája: jó és rossz
            for sub, sq in [('jo', 0.8), ('rossz', 0.1)]:
                gc = tree.add_thought(
                    child, f'd2_{letter}_{sub}: {problem[:5]}',
                    {'problem': problem, 'last_thought': f'd2_{letter}_{sub}'},
                    score=sq * 3)
                gc.visits = 3
        return tree

    thresholds = [0.0, 0.3, 0.5, 0.7, 0.9, 1.5, 3.0, 5.0]
    results = {}
    print(f"{'min_score':<12} {'Eltavolitva':<14} {'Maradt':<10} {'Best path':<12}")
    print(f"{'-'*50}")
    for min_score in thresholds:
        tree = build_tree()
        size_before = getattr(tree, '_size', 0)
        removed = tree.prune(min_score) if hasattr(tree, 'prune') else 0
        size_after = getattr(tree, '_size', 0)
        best_after = tree.get_best_path() if hasattr(tree, 'get_best_path') else []
        results[str(min_score)] = {
            'size_before': size_before, 'removed': removed,
            'size_after': size_after, 'best_path_steps': len(best_after),
        }
        print(f"{min_score:<12} {removed:<14} {size_after:<10} {len(best_after):<12}")
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='UCB1 es pruning strategiak tesztelese')
    parser.add_argument('--problem', type=str,
                        default='Hogyan javitsuk a rendszer memoriakezeleset?')
    parser.add_argument('--iterations', type=int, default=20)
    parser.add_argument('--depth', type=int, default=4)
    args = parser.parse_args()
    print(f"UCB1 ES PRUNING TESZT")
    print(f"Problema: {args.problem}")
    print(f"Iteraciok: {args.iterations}, Melyseg: {args.depth}")
    weight_results = test_exploration_weights(
        args.problem, args.iterations, args.depth)
    prune_results = test_pruning(
        args.problem, args.iterations, args.depth)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    out_file = f'/data/mcp_server/context/ucb1_pruning_test_{ts}.json'
    with open(out_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'problem': args.problem,
            'iterations': args.iterations,
            'depth': args.depth,
            'exploration_weight_results': weight_results,
            'pruning_results': prune_results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nEredmenyek: {out_file}")

