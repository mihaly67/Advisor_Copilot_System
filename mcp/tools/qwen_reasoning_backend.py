#!/usr/bin/env python3
"""
Qwen Reasoning Backend — külön script a reasoning pipeline Qwen hívásaihoz.

Ezt a scriptet a reasoning_pipeline.py subprocess-ként hívja, nem pedig
egy -c argumentumban. Ez sokkal robosztusabb (nincs shell escaping probléma,
nincs repr() fügés, tiszta argumentumok).

Használat:
    python3 qwen_reasoning_backend.py --mode generate --problem "..." 
    python3 qwen_reasoning_backend.py --mode evaluate --problem "..." --thought "..."

Kimenet: sima szöveg (a hívó feldolgozza)
"""

import sys
import os
import argparse

# Környezet beállítása (CUDA, model path, LD_LIBRARY_PATH)
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
os.environ.setdefault('CUDA_DEVICE_ORDER', 'PCI_BUS_ID')

# CUDA runtime library path (kritikus a llama_cpp betöltéséhez)
_CUDA_LIBS = (
    '/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:'
    '/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cublas/lib'
)
_existing = os.environ.get('LD_LIBRARY_PATH', '')
if _CUDA_LIBS not in _existing:
    os.environ['LD_LIBRARY_PATH'] = (
        f'{_CUDA_LIBS}:{_existing}' if _existing else _CUDA_LIBS
    )

MODEL_PATH = os.environ.get(
    'QWEN_MODEL_PATH',
    '/data/ml/hf_cache/models--Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/snapshots/13fb94bfda8c8cf22497dc57b78f391a9acb426a/qwen2.5-coder-7b-instruct-q5_k_m.gguf'
)
GPU_LAYERS = int(os.environ.get('QWEN_GPU_LAYERS', '35'))


def load_llm():
    """Betölti a Qwen modellt (lusta betöltés)."""
    from llama_cpp import Llama
    return Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=GPU_LAYERS,
        n_ctx=2048,
        verbose=False,
    )


def generate_candidates(llm, problem):
    """Generál 3-5 lehetséges megközelítést a problémához (tömeges rollout profil)."""
    prompt = (
        f'Generálj 3-5 lehetséges megközelítést a probléma megoldásához.\n'
        f'Probléma: {problem}\n'
        f'Minden megközelítés új sorban, "#"- nélkül. Csak a megközelítések.'
    )
    response = llm.create_chat_completion(
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=200,
        temperature=0.5,
    )
    text = response['choices'][0]['message']['content']
    candidates = [c.strip() for c in text.split('\n')
                  if c.strip() and not c.strip().startswith('#')
                  and not c.strip().startswith('-')]
    return candidates[:5]


def deep_generate_candidates(llm, problem):
    """Sekély-deep reasoning profil: hosszabb, részletesebb megközelítések.

    A QwenSimulatorBackend-től eltérő profil:
      - System prompt a mélyebb analizishez
      - Alacsonyabb temperature (0.15) a koncentráltabb válaszért
      - Hosszabb max_tokens (400) a részletezett megközelítésekért
    """
    system = (
        'Te egy mély gondolkodású reasoner agent vagy. '
        'A feladatod, hogy egy problémához strukturált, '
        'részletezett megközelítéseket adj — mindegyiket '
        'indoklással és várható kockázattal. '
        'Ne felszínes válaszokat adj, hanem mély, '
        'átgondolt stratégiákat.'
    )
    prompt = (
        f'Probléma: {problem}\n\n'
        f'Generálj 3 strukturált, részletezett megközelítést. '
        f'Mindegyiket így formázd:\n'
        f'MEGKÖZELÍTÉS [betű]: [rövid név] — [indoklás] (kockázat: [magas/medium/alacsony])\n'
        f'Csak a megközelítések, minden új sorban.'
    )
    response = llm.create_chat_completion(
        messages=[{'role': 'system', 'content': system},
                  {'role': 'user', 'content': prompt}],
        max_tokens=400,
        temperature=0.15,
    )
    text = response['choices'][0]['message']['content']
    candidates = [c.strip() for c in text.split('\n')
                  if c.strip() and c.strip().startswith('MEGKÖZELÍTÉS')]
    return candidates[:3]


def evaluate_thought(llm, problem, thought):
    """Értékel egy gondolatot 0..1 skálán (tömeges rollout profil)."""
    prompt = (
        f'Értékeld ezt a megközelítést 0..1 skálán (1=optimális, 0=használhatatlan).\n'
        f'Probléma: {problem}\n'
        f'Megközelítés: {thought}\n'
        f'Válasz: csak egyetlen szám 0..1 között.'
    )
    response = llm.create_chat_completion(
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=20,
        temperature=0.2,
    )
    text = response['choices'][0]['message']['content'].strip()
    # Szám kinyerése
    import re
    match = re.search(r'[0-9]*\.?[0-9]+', text)
    if match:
        score = float(match.group())
        return max(0.0, min(1.0, score))
    return 0.5


def deep_evaluate_thought(llm, problem, thought):
    """Sekély-deep reasoning profil: részletes értékelés indoklással.

    Nem csak egy számot ad, hanem indokoltan értékel —
    mélyebb következtetés a gondolat minőségéről.
    """
    system = (
        'Te egy mély gondolkodású értékelő agent vagy. '
        'A feladatod, hogy egy megközelítést részletesen '
        'értékelj: erősségek, gyengeségek, kockázatok. '
        'A végén adj egy 0..1 közötti pontszámot (1=optimális).'
    )
    prompt = (
        f'Probléma: {problem}\n'
        f'Megközelítés: {thought}\n\n'
        f'Értékeld: erősségek, gyengeségek, kockázatok. '
        f'A végén: PONTSZÁM: [0..1]'
    )
    response = llm.create_chat_completion(
        messages=[{'role': 'system', 'content': system},
                  {'role': 'user', 'content': prompt}],
        max_tokens=300,
        temperature=0.15,
    )
    text = response['choices'][0]['message']['content'].strip()
    # PONTSZÁM kinyerése a válasz végéről
    import re
    match = re.search(r'PONTSZÁM[:\s]*([0-9]*\.?[0-9]+)', text, re.IGNORECASE)
    if match:
        score = float(match.group(1))
        return max(0.0, min(1.0, score))
    # Fallback: bármilyen szám
    match = re.search(r'[0-9]*\.?[0-9]+', text)
    if match:
        score = float(match.group())
        return max(0.0, min(1.0, score))
    return 0.5


def main():
    parser = argparse.ArgumentParser(description='Qwen Reasoning Backend')
    parser.add_argument('--mode', type=str, required=True,
                        choices=['generate', 'evaluate',
                                 'deep-generate', 'deep-evaluate'],
                        help='Művelet: generate/evaluate (tömeges) vagy '
                             'deep-generate/deep-evaluate (sekély-deep)')
    parser.add_argument('--problem', type=str, required=True,
                        help='A probléma szövege')
    parser.add_argument('--thought', type=str, default=None,
                        help='A gondolat amit értékelni kell (evaluate módban)')
    args = parser.parse_args()

    try:
        llm = load_llm()
        if args.mode == 'generate':
            candidates = generate_candidates(llm, args.problem)
            import json
            print(json.dumps(candidates, ensure_ascii=False))
        elif args.mode == 'deep-generate':
            candidates = deep_generate_candidates(llm, args.problem)
            import json
            print(json.dumps(candidates, ensure_ascii=False))
        elif args.mode == 'evaluate':
            score = evaluate_thought(llm, args.problem, args.thought)
            print(f'{score:.3f}')
        elif args.mode == 'deep-evaluate':
            score = deep_evaluate_thought(llm, args.problem, args.thought)
            print(f'{score:.3f}')
    except Exception as e:
        # Hiba esetén fallback kimenet
        if 'generate' in args.mode:
            print('[]')
        else:
            print('0.500')
        sys.stderr.write(f'Qwen backend hiba: {e}\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
