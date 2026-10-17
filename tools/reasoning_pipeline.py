#!/usr/bin/env python3
"""
Reasoning Pipeline
===================

Heterogén reasoning pipeline amely integrálja:

  1. **agentic-os-core MCTS motorját** (4-fázisú: Selection/Expansion/
     Simulation/Backpropagation, UCB1-gyel)
  2. **yggdrasil-mcp tervezési fázisait** (init → clarify → explore →
     evaluate → finalize)
  3. **Qwen szimulátor** (rollout végrehajtó, lokális GPU)
  4. **API agent opció** (magasabb szintű gondolkodás sekély rolloutokhoz)

Az MCTS fa gyökere egy "probléma/gondolat". A gyermek csomópontok a
lehetséges megközelítések. A Qwen (vagy API agent) értékeli a leveleket.

Használat:
    pipeline = ReasoningPipeline()
    result = pipeline.plan(
        problem="Hogyan javítsuk a memória frissítés megbízhatóságát?",
        max_iterations=50,
    )
"""

import os
import sys
import json
import math
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable, Optional

sys.path.insert(0, '/data/mcp_server/tools')

# agentic-os-core MCTS integráció (ha elérhető)
AGENTIC_OS_PATH = '/data/Brain/agentic-os-core/src'
try:
    sys.path.insert(0, AGENTIC_OS_PATH)
    from agentic_os.core.tree.mcts import MCTS, Evaluator, CandidateGenerator
    from agentic_os.core.tree.thought_node import ThoughtNode
    from agentic_os.core.tree.thought_tree import ThoughtTree
    AGENTIC_OS_AVAILABLE = True
except ImportError:
    AGENTIC_OS_AVAILABLE = False

MEMORY_FILE = '/data/mcp_server/context/active_memory.json'
EVENTS_LOG = '/data/mcp_server/context/events.log'
MCTS_TREES_DIR = '/data/mcp_server/context/mcts_trees'

# yggdrasil-mcp tervezési fázisok (planning.ts inspiráció)
PLANNING_PHASES = [
    'init',        # probléma inicializálása
    'clarify',     # kérdések tisztázása
    'explore',     # lehetséges megközelítések (ágak)
    'evaluate',    # ágak értékelése (MCTS)
    'finalize',    # legjobb útvonal kiválasztása
]


class QwenSimulatorBackend:
    """Qwen (lokális GPU) szimulátor backend az MCTS rolloutokhoz.

    Ez a tömeges rolloutokhoz való — lokális, ingyenes, determinisztikusabb.
    Külön scriptet hív subprocess-ként (qwen_reasoning_backend.py), ami
    robosztusabb mint a -c argumentum.
    """

    BACKEND_SCRIPT = '/data/mcp_server/tools/qwen_reasoning_backend.py'

    def __init__(self, max_tokens: int = 200, timeout: int = 120):
        self.max_tokens = max_tokens
        self.timeout = timeout

    def evaluate(self, state: dict[str, Any], thought: str) -> float:
        """Értékel egy gondolatot egy adott állapotban 0..1 tartományban."""
        problem = state.get('problem', 'ismeretlen')
        output = self._call_backend('evaluate', problem, thought)
        try:
            return float(output.strip())
        except (ValueError, TypeError):
            return 0.5

    def generate_candidates(self, state: dict[str, Any]) -> list[str]:
        """Generál lehetséges megközelítéseket egy állapothoz."""
        problem = state.get('problem', 'ismeretlen')
        output = self._call_backend('generate', problem)
        try:
            import json
            candidates = json.loads(output)
            if isinstance(candidates, list):
                return candidates[:5]
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def _call_backend(self, mode: str, problem: str, thought: str = None):
        """Külön script hívása subprocess-ként."""
        cmd = ['/home/Jules/jules_venv/bin/python3', self.BACKEND_SCRIPT,
               '--mode', mode, '--problem', problem]
        if thought:
            cmd.extend(['--thought', thought])
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = '0'
        env.setdefault('QWEN_MODEL_PATH',
                       '/data/ml/hf_cache/models--Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/snapshots/13fb94bfda8c8cf22497dc57b78f391a9acb426a/qwen2.5-coder-7b-instruct-q5_k_m.gguf')
        env.setdefault('QWEN_GPU_LAYERS', '35')
        # CUDA runtime lib path (kritikus a llama_cpp betöltéséhez)
        _cuda_libs = (
            '/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:'
            '/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cublas/lib'
        )
        _existing = env.get('LD_LIBRARY_PATH', '')
        if _cuda_libs not in _existing:
            env['LD_LIBRARY_PATH'] = (
                f'{_cuda_libs}:{_existing}' if _existing else _cuda_libs
            )
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=self.timeout, env=env)
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, Exception):
            return '0.500' if mode == 'evaluate' else '[]'


class APISimulatorBackend:
    """Sekély-deep reasoning backend az MCTS rolloutokhoz.

    A QwenSimulatorBackend-től eltérő profil: nem tömeges rollout,
    hanem sekély-deep gondolkodás — system prompt, alacsonyabb
    temperature, hosszabb válaszok, részletes indoklás.

    A Qwen-t (P4000) használja, de a qwen_reasoning_backend.py
    deep-generate/deep-evaluate módjaival — ez egy "második profil"
    a Qwen-nek, ami mélyebb következtetést produkál.

    A ReasoningPipeline._choose_backend() dönti el, hogy mikor használja
    (auto módban: sekély fánál, depth<2 és nodes<10).
    """

    BACKEND_SCRIPT = '/data/mcp_server/tools/qwen_reasoning_backend.py'

    def __init__(self, max_tokens: int = 400, timeout: int = 180):
        self.max_tokens = max_tokens
        self.timeout = timeout

    def evaluate(self, state: dict[str, Any], thought: str) -> float:
        """Részletes értékelés indoklással (deep-evaluate mód)."""
        problem = state.get('problem', 'ismeretlen')
        output = self._call_backend('deep-evaluate', problem, thought)
        try:
            return float(output.strip())
        except (ValueError, TypeError):
            return 0.5

    def generate_candidates(self, state: dict[str, Any]) -> list[str]:
        """Strukturált, részletezett megközelítések (deep-generate mód)."""
        problem = state.get('problem', 'ismeretlen')
        output = self._call_backend('deep-generate', problem)
        try:
            import json
            candidates = json.loads(output)
            if isinstance(candidates, list):
                return candidates[:3]
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def _call_backend(self, mode: str, problem: str, thought: str = None):
        """Qwen deep reasoning backend hívása subprocess-ként."""
        cmd = ['/home/Jules/jules_venv/bin/python3', self.BACKEND_SCRIPT,
               '--mode', mode, '--problem', problem]
        if thought:
            cmd.extend(['--thought', thought])
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = '0'
        env.setdefault('QWEN_MODEL_PATH',
                       '/data/ml/hf_cache/models--Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/snapshots/13fb94bfda8c8cf22497dc57b78f391a9acb426a/qwen2.5-coder-7b-instruct-q5_k_m.gguf')
        env.setdefault('QWEN_GPU_LAYERS', '35')
        # CUDA runtime lib path
        _cuda_libs = (
            '/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:'
            '/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cublas/lib'
        )
        _existing = env.get('LD_LIBRARY_PATH', '')
        if _cuda_libs not in _existing:
            env['LD_LIBRARY_PATH'] = (
                f'{_cuda_libs}:{_existing}' if _existing else _cuda_libs
            )
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=self.timeout, env=env)
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, Exception):
            return '0.500' if 'evaluate' in mode else '[]'


class HeterogeneousBackend:
    """Heterogén backend wrapper: depth-proxy alapján vált Qwen/deep közt.

    Az MCTS engine fixen egy generator+evaluator párt kap. Ez a wrapper
    úgy viselkedik, mint egyetlen backend, de belül a hívás sorszáma
    alapján dönt:

      - Az első ``switch_after`` hívás (gyökér közel): deep reasoning
        (APISimulatorBackend) — strukturált, indokolt megközelítések
      - Utána: Qwen tömeges rollout (QwenSimulatorBackend) — gyors,
        ismétlődő értékelések a fa mélyebb szintjein

    Ez a hívás-számláló egy jó proxy a depth-re, mert az MCTS
    szerkezetéből adódóan az első hívások a gyökér közelében vannak.
    """

    def __init__(self, qwen_backend, api_backend, switch_after: int = 1):
        self.qwen_backend = qwen_backend
        self.api_backend = api_backend
        self.switch_after = switch_after
        self._call_count = 0
        # Trace: melyik backendet használtuk melyik hívásnál
        self._call_trace = []

    def _choose(self):
        """Választ egy backendet a hívás sorszáma alapján."""
        self._call_count += 1
        if self._call_count <= self.switch_after:
            backend = self.api_backend
            backend_name = 'api'
        else:
            backend = self.qwen_backend or self.api_backend
            backend_name = 'qwen' if self.qwen_backend else 'api'
        self._call_trace.append({
            'call': self._call_count,
            'backend': backend_name,
        })
        return backend, backend_name

    def evaluate(self, state: dict[str, Any], thought: str) -> float:
        """Heterogén értékelés — deep vagy tömeges a hívás alapján."""
        backend, name = self._choose()
        score = backend.evaluate(state, thought)
        # Ha deep backendet használtunk és a thought még a placeholder
        # formátumú, akkor is a deep értékelés eredménye érvényes
        return score

    def generate_candidates(self, state: dict[str, Any]) -> list[str]:
        """Heterogén generálás — deep vagy tömeges a hívás alapján."""
        backend, name = self._choose()
        candidates = backend.generate_candidates(state)
        return candidates

    def get_stats(self):
        """Statisztika: hány hívás, milyen eloszlásban."""
        api_calls = sum(1 for t in self._call_trace if t['backend'] == 'api')
        qwen_calls = sum(1 for t in self._call_trace if t['backend'] == 'qwen')
        return {
            'total_calls': self._call_count,
            'api_calls': api_calls,
            'qwen_calls': qwen_calls,
            'switch_after': self.switch_after,
            'call_trace': self._call_trace[-10:],  # utolsó 10
        }


class ReasoningPipeline:
    """Heterogén reasoning pipeline: MCTS + yggdrasil fázisok + Qwen/API."""

    def __init__(self, exploration_weight: float = 1.414,
                 max_iterations: int = 50, max_depth: int = 5,
                 use_qwen: bool = True, simulator_mode: str = 'auto',
                 export_tree: bool = True,
                 search_strategy: str = 'mcts', beam_width: int = 2):
        self.exploration_weight = exploration_weight
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.use_qwen = use_qwen
        self.simulator_mode = simulator_mode  # 'auto', 'qwen', 'api'
        self.export_tree = export_tree  # MCTS fa JSON export a mcts_trees-be
        self.search_strategy = search_strategy  # 'mcts' vagy 'beam'
        self.beam_width = beam_width  # beam search top-k ágak
        self.qwen_backend = QwenSimulatorBackend() if use_qwen else None
        self.api_backend = APISimulatorBackend()
        self.phase_log = []
        self._backend_calls = {'qwen': 0, 'api': 0}
        self._last_tree = None  # utolsó MCTS/beam fa (exporthoz)

    def _log_phase(self, phase, message, data=None):
        ts = datetime.now(timezone.utc).isoformat()
        entry = {'timestamp': ts, 'phase': phase,
                 'message': message, 'data': data or {}}
        self.phase_log.append(entry)
        with open(EVENTS_LOG, 'a') as f:
            f.write(f"[{ts}] [INFO] [reasoning:{phase}] {message}\n")

    def _choose_backend(self, depth: int, total_nodes: int):
        """Heterogén szimulátor választás.

        simulator_mode:
          'auto'  — sekély fánál API, mélyebbnél Qwen (heterogén)
          'qwen'  — mindig Qwen (tömeges rollout)
          'api'   — mindig API agent (magasabb szintű gondolkodás)
        """
        if self.simulator_mode == 'qwen':
            backend = self.qwen_backend or self.api_backend
            self._backend_calls['qwen' if backend == self.qwen_backend else 'api'] += 1
            return backend
        elif self.simulator_mode == 'api':
            self._backend_calls['api'] += 1
            return self.api_backend
        else:  # 'auto'
            # Csak a mélyebb (depth >= 2) vagy sűrűbb (>10 node) résznél Qwen
            if depth >= 2 or total_nodes >= 10:
                backend = self.qwen_backend or self.api_backend
                self._backend_calls['qwen' if backend == self.qwen_backend else 'api'] += 1
                return backend
            self._backend_calls['api'] += 1
            return self.api_backend

    def _make_evaluator(self, backend) -> Evaluator:
        def evaluator(state, thought):
            return backend.evaluate(state, thought)
        return evaluator

    def _make_generator(self, backend) -> CandidateGenerator:
        def generator(state):
            return backend.generate_candidates(state)
        return generator

    def _compute_switch_after(self, problem: str,
                              max_iterations: int, max_depth: int) -> int:
        """Adaptív switch_after számítás a HeterogeneousBackend-hez.

        A switch_after határozza meg, hány kezdeti hívás legyen deep
        reasoning (API/Qwen deep profil, ~30s/hívás) a gyökér közelében,
        mielőtt átváltunk Qwen tömeges rollout-ra (~3-5s/hívás).

        Tényezők:
          - Base: 1 (egy deep hívás a gyökérnél — irányt ad)
          - Komplexitás bonus: hosszabb probléma vagy kulcsszavak
            (komplex, kritikus, architektúra, biztonság, teljesítés)
          - Iteráció bonus: több iteráció → több deep hívás (capped 2)
          - Mélység penalty: mélyebb fa → kevesebb deep (rollout kell)
        """
        base = 1
        # Komplexitás: probléma hossza + kulcsszavak
        complexity = 0
        if len(problem) > 200:
            complexity += 1
        complexity_keywords = [
            'komplex', 'kritikus', 'architektura', 'biztonsag',
            'teljesites', 'architektúra', 'biztonság', 'teljesítés',
            'kritikus', 'komplex', 'critical', 'complex', 'security',
            'architecture', 'performance',
        ]
        problem_lower = problem.lower()
        complexity += min(sum(1 for kw in complexity_keywords
                             if kw in problem_lower), 2)
        # Iteráció bonus: 10 iterációnként +1 (max 2)
        iter_bonus = min(max_iterations // 10, 2)
        # Mélység penalty: 3 feletti mélységnél -1/2 mélységenként
        depth_penalty = max(0, (max_depth - 3) // 2)
        switch_after = max(1, base + complexity + iter_bonus - depth_penalty)
        # Cap: max 4 deep hívás (drága, ~120s)
        return min(switch_after, 4)

    def plan(self, problem: str, context: dict = None) -> dict:
        """Végrehajt egy teljes reasoning pipeline-t a problémán.

        Fázisok: init → clarify → explore → evaluate → finalize.
        """
        context = context or {}
        self._log_phase('init', f'Reasoning pipeline inditasa: {problem[:80]}')

        # --- FÁZIS 1: init ---
        root_state = {'problem': problem, 'context': context, 'phase': 'init'}
        root_thought = problem
        self._log_phase('init', 'Gyoker gondolat inicializalva')

        # --- FÁZIS 2: clarify ---
        clarifying_qs = self._generate_clarifying_questions(problem, context)
        self._log_phase('clarify', f'{len(clarifying_qs)} kerdes generalva',
                        {'questions': clarifying_qs})
        root_state['clarifying_questions'] = clarifying_qs

        # --- FÁZIS 3: explore + evaluate (MCTS vagy beam search) ---
        if AGENTIC_OS_AVAILABLE:
            if self.search_strategy == 'beam':
                result = self._run_beam_search(root_thought, root_state)
            else:
                result = self._run_mcts(root_thought, root_state)
        else:
            result = self._run_heuristic(root_thought, root_state)

        # --- FÁZIS 5: finalize ---
        best_path = result.get('best_path', [])
        final_plan = self._finalize(best_path, problem, context)
        self._log_phase('finalize', f'Terv kesz: {len(best_path)} lepes',
                        {'plan': final_plan})

        self._save_to_memory(problem, result, final_plan)

        # MCTS fa exportálása perzisztenciához (JSON + vizualizáció)
        tree_file = None
        tree_visualization = result.get('tree_visualization')
        if self.export_tree and AGENTIC_OS_AVAILABLE:
            tree_file = self._save_tree(getattr(self, '_last_tree', None), problem)
            if tree_file:
                self._log_phase('finalize',
                                f'MCTS fa exportalva: {tree_file}',
                                {'tree_file': tree_file})

        return {
            'problem': problem,
            'phases_completed': PLANNING_PHASES,
            'mcts_available': AGENTIC_OS_AVAILABLE,
            'iterations': result.get('iterations', 0),
            'best_path': best_path,
            'final_plan': final_plan,
            'phase_log': self.phase_log,
            'backend_calls': self._backend_calls,
            'simulator_mode': self.simulator_mode,
            'hetero_stats': getattr(self, '_hetero_stats', None),
            'tree_file': tree_file,
            'tree_visualization': tree_visualization,
            'tree_size': result.get('tree_size', 0),
        }

    def _generate_clarifying_questions(self, problem, context):
        qs = [
            f'Mi a pontos celja: {problem[:50]}?',
            'Milyen korlatozasok vannak?',
            'Milyen eroforrasok allnak rendelkezesre?',
        ]
        return qs

    @staticmethod
    def _export_tree(tree) -> dict:
        """ThoughtTree szerializálása JSON-mentes dict-té.

        Rekurzívan bejárja a fát: thought, score, visits, avg_score, depth,
        és children. Így az MCTS fa teljes struktúrája perzisztenssé válik,
        később vizsgálható/újratölthető. Az ephemeral fa nem vész el.
        """
        if tree is None or not getattr(tree, 'root', None):
            return {'root': None, 'size': 0}

        def _node_to_dict(node):
            return {
                'thought': node.thought,
                'score': round(node.score, 4),
                'visits': node.visits,
                'avg_score': round(node.avg_score, 4),
                'depth': node.depth,
                'children': [_node_to_dict(c) for c in node.children],
            }

        return {
            'root': _node_to_dict(tree.root),
            'size': getattr(tree, '_size', 0),
            'max_depth': tree.max_depth,
            'max_children': tree.max_children,
        }

    def _save_tree(self, tree, problem: str) -> str | None:
        """MCTS fa exportálása JSON fájlba a mcts_trees könyvtárba.

        Visszatér a fájl útvonalával, vagy None-szal ha a fa üres.
        """
        if tree is None or not getattr(tree, 'root', None):
            return None
        os.makedirs(MCTS_TREES_DIR, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        safe_problem = ''.join(c if c.isalnum() else '_' for c in problem[:40])
        fname = f'mcts_tree_{ts}_{safe_problem}.json'
        fpath = os.path.join(MCTS_TREES_DIR, fname)
        export = self._export_tree(tree)
        with open(fpath, 'w') as f:
            json.dump(export, f, ensure_ascii=False, indent=2)
        return fpath

    def _run_mcts(self, root_thought, root_state):
        """Agentic-os-core MCTS motor futtatása.

        Auto módban HeterogeneousBackend-et használ: az első hívás deep
        reasoning (gyökér közel), utána Qwen tömeges rollout.
        """
        self._log_phase('explore', 'MCTS fa epitese (agentic-os-core)',
                        {'simulator_mode': self.simulator_mode,
                         'use_qwen': self.use_qwen})

        # Backend választás a simulator_mode alapján
        if self.simulator_mode == 'qwen' and self.qwen_backend:
            # Végig Qwen (tömeges rollout) — HeterogeneousBackend switch_after=0
            # így a híváskövetés pontos (get_stats számlálja a hívásokat)
            backend = HeterogeneousBackend(
                self.qwen_backend, self.api_backend, switch_after=0)
            self._log_phase('explore',
                            'Pure Qwen mode (switch_after=0, mindig Qwen rollout)',
                            {'switch_after': 0, 'adaptive': False})
            self._hetero_stats = None
        elif self.simulator_mode == 'api':
            # Végig deep reasoning
            backend = self.api_backend
            self._backend_calls['api'] += 1
            self._hetero_stats = None
        else:
            # AUTO mód: HeterogeneousBackend (deep → Qwen váltás)
            # Adaptív switch_after: probléma komplexitás + iterációk +
            # mélység alapján (base=1, max=4)
            problem_text = root_state.get('problem', root_thought)
            adaptive_switch = self._compute_switch_after(
                problem_text, self.max_iterations, self.max_depth)
            self._adaptive_switch_after = adaptive_switch
            if self.qwen_backend:
                backend = HeterogeneousBackend(
                    self.qwen_backend, self.api_backend,
                    switch_after=adaptive_switch)
                self._log_phase('explore',
                                f'Heterogen backend: elso {adaptive_switch} '
                                f'hivas deep, utana Qwen tomeges rollout',
                                {'switch_after': adaptive_switch,
                                 'adaptive': True})
            else:
                backend = self.api_backend
                self._backend_calls['api'] += 1
            self._hetero_stats = None

        mcts = MCTS(exploration_weight=self.exploration_weight,
                    max_iterations=self.max_iterations,
                    max_depth=self.max_depth)

        evaluator = self._make_evaluator(backend)
        generator = self._make_generator(backend)

        tree = mcts.search(root_thought=root_thought,
                           root_state=root_state,
                           generator=generator,
                           evaluator=evaluator)

        # Fa elkapása perzisztenciához (export, vizualizáció)
        self._last_tree = tree

        best_path = tree.get_best_path() if hasattr(tree, 'get_best_path') else []
        path_texts = [n.thought for n in best_path] if best_path else []

        # Heterogén backend statisztika (auto módban)
        if hasattr(backend, 'get_stats'):
            self._hetero_stats = backend.get_stats()
            # Frissítjük a _backend_calls-t a tényleges hívásokkal
            self._backend_calls['qwen'] = self._hetero_stats['qwen_calls']
            self._backend_calls['api'] = self._hetero_stats['api_calls']

        self._log_phase('evaluate',
                        f'MCTS kesz, legjobb ut: {len(path_texts)} lepes',
                        {'path': path_texts,
                         'backend_calls': self._backend_calls,
                         'hetero_stats': self._hetero_stats})
        return {
            'iterations': self.max_iterations,
            'best_path': path_texts,
            'tree_size': getattr(tree, '_size', 0),
            'tree_visualization': tree.visualize() if hasattr(tree, 'visualize') else None,
        }

    def _run_beam_search(self, root_thought, root_state):
        """Beam search: top-k ágak megtartása mélységenként.

        Alternatíva az MCTS UCB1 alapú keresésével szemben. A beam search
        minden szinten generál kandidátumokat, értékeli őket, és csak a
        top-k (beam_width) legjobb ágat tartja meg. Ez determinisztikusabb
        és kevesebb iterációt igényel, mint az MCTS.
        """
        self._log_phase('explore',
                        f'Beam search inditasa (beam_width={self.beam_width}, '
                        f'max_depth={self.max_depth})')

        # Backend választás a simulator_mode alapján (ugyanaz mint MCTS)
        if self.simulator_mode == 'qwen' and self.qwen_backend:
            backend = HeterogeneousBackend(
                self.qwen_backend, self.api_backend, switch_after=0)
            self._log_phase('explore',
                            'Beam search: pure Qwen (switch_after=0)',
                            {'switch_after': 0})
        elif self.simulator_mode == 'api':
            backend = self.api_backend
            self._backend_calls['api'] += 1
        else:
            # AUTO: adaptív switch_after
            switch_after = self._compute_switch_after(
                root_state.get('problem', ''), self.max_iterations,
                self.max_depth)
            backend = HeterogeneousBackend(
                self.qwen_backend, self.api_backend,
                switch_after=switch_after)
            self._log_phase('explore',
                            f'Beam search: heterogen backend '
                            f'(switch_after={switch_after})',
                            {'switch_after': switch_after, 'adaptive': True})

        evaluator = self._make_evaluator(backend)
        generator = self._make_generator(backend)

        # ThoughtTree létrehozása
        tree = ThoughtTree(max_children=self.beam_width * 3,
                           max_depth=self.max_depth)
        root_node = tree.set_root(root_thought, root_state)

        # Kezdeti beam: csak a root
        beam = [(root_node, root_state)]
        all_scored = []  # (node, score, depth) az összes csomópont

        for depth in range(self.max_depth):
            new_beam = []
            for node, state in beam:
                # Generáljunk kandidátumokat
                candidates = generator(state)
                for cand in candidates:
                    score = evaluator(state, cand)
                    child_state = dict(state)
                    child_state['depth'] = depth + 1
                    child = tree.add_thought(node, cand,
                                             state=child_state, score=score)
                    if child:
                        new_beam.append((child, child_state, score))
                        all_scored.append((child, score, depth + 1))

            if not new_beam:
                break

            # Top-k kiválasztása score szerint
            new_beam.sort(key=lambda x: -x[2])
            beam = [(n, s) for n, s, _ in new_beam[:self.beam_width]]

            self._log_phase('explore',
                            f'Beam depth {depth+1}: {len(new_beam)} kandidatum, '
                            f'top-{self.beam_width} megtartva',
                            {'depth': depth + 1,
                             'candidates': len(new_beam),
                             'kept': min(self.beam_width, len(new_beam))})

        best_path = tree.get_best_path() if hasattr(tree, 'get_best_path') else []
        path_texts = [n.thought for n in best_path] if best_path else []

        # Heterogén backend statisztika
        if hasattr(backend, 'get_stats'):
            self._hetero_stats = backend.get_stats()
            self._backend_calls['qwen'] = self._hetero_stats['qwen_calls']
            self._backend_calls['api'] = self._hetero_stats['api_calls']

        self._last_tree = tree

        self._log_phase('explore',
                        f'Beam search kesz: {tree._size} csomopont, '
                        f'{len(path_texts)} lepeses best_path',
                        {'tree_size': tree._size,
                         'best_path_steps': len(path_texts)})

        return {
            'iterations': tree._size,
            'best_path': path_texts,
            'tree_size': tree._size,
            'tree_visualization': tree.visualize() if hasattr(tree, 'visualize') else None,
            'search_strategy': 'beam',
            'beam_width': self.beam_width,
        }


    def _run_heuristic(self, root_thought, root_state):
        """Heurisztikus fallback ha az agentic-os-core nem elérhető."""
        self._log_phase('explore', 'Heurisztikus fa epites (fallback)')
        backend = self._choose_backend(depth=0, total_nodes=0)
        candidates = backend.generate_candidates(root_state)
        scored = [(c, backend.evaluate(root_state, c)) for c in candidates]
        scored.sort(key=lambda x: -x[1])
        best = scored[0] if scored else (root_thought, 0.5)
        return {
            'iterations': len(candidates),
            'best_path': [root_thought, best[0]],
            'tree_size': len(candidates),
        }

    def _finalize(self, best_path, problem, context):
        steps = []
        for i, thought in enumerate(best_path):
            steps.append({
                'step': i + 1,
                'title': thought[:60],
                'description': thought,
                'complexity': 'medium',
            })
        return {
            'problem': problem,
            'steps': steps,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }

    def _save_to_memory(self, problem, result, final_plan):
        try:
            with open(MEMORY_FILE, 'r') as f:
                mem = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            mem = {}

        mem.setdefault('reasoning_results', [])
        mem['reasoning_results'].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'problem': problem,
            'iterations': result.get('iterations', 0),
            'best_path': result.get('best_path', []),
            'mcts_available': AGENTIC_OS_AVAILABLE,
            'tree_size': result.get('tree_size', 0),
        })
        mem['reasoning_results'] = mem['reasoning_results'][-20:]

        with open(MEMORY_FILE, 'w') as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Reasoning Pipeline')
    parser.add_argument('--problem', type=str, required=True,
                        help='A problema amit meg kell oldani')
    parser.add_argument('--iterations', type=int, default=30,
                        help='MCTS iteraciok szama')
    parser.add_argument('--depth', type=int, default=4,
                        help='Max fa melyseg')
    parser.add_argument('--no-qwen', action='store_true',
                        help='Qwen kikapcsolasa (csak API/heur)')
    parser.add_argument('--simulator', type=str, default='auto',
                        choices=['auto', 'qwen', 'api'],
                        help='Szimulator mode: auto (heterogen), qwen (mindig Qwen), api (mindig API)')
    parser.add_argument('--no-tree-export', action='store_true',
                        help='MCTS fa JSON export kikapcsolasa')
    parser.add_argument('--strategy', type=str, default='mcts',
                        choices=['mcts', 'beam'],
                        help='Keresesi strategia: mcts (UCB1) vagy beam (top-k)')
    parser.add_argument('--beam-width', type=int, default=2,
                        help='Beam search ablakmeret (top-k) (default: 2)')
    args = parser.parse_args()

    pipeline = ReasoningPipeline(
        max_iterations=args.iterations,
        max_depth=args.depth,
        use_qwen=not args.no_qwen,
        simulator_mode=args.simulator,
        export_tree=not args.no_tree_export,
        search_strategy=args.strategy,
        beam_width=args.beam_width,
    )
    result = pipeline.plan(args.problem)
    print(json.dumps(result, ensure_ascii=False, indent=2))




