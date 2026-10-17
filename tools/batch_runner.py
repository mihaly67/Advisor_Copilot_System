#!/usr/bin/env python3
"""Batch runner: runs Qwen GPU analysis on a range of repos via the orchestrator."""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, '/data/mcp_server/tools')
from master_orchestrator import MasterOrchestrator

if len(sys.argv) < 3:
    print("Usage: batch_runner.py <start_idx> <end_idx> [--force]")
    sys.exit(1)

start = int(sys.argv[1])
end = int(sys.argv[2])
force = '--force' in sys.argv

orch = MasterOrchestrator()
all_repos = sorted([d for d in os.listdir('/data/Brain')
                   if os.path.isdir(f'/data/Brain/{d}') and d != '_qwen_analysis'])
batch = all_repos[start:end]

print(f"🚀 BATCH: {len(batch)} repó (index {start}-{end}) Qwen GPU elemzés (force={force})")
print("=" * 60)

results = []
for i, repo in enumerate(batch):
    repo_path = f'/data/Brain/{repo}'
    print(f"\n[{i+1}/{len(batch)}] 🤖 Qwen elemzi: {repo}")
    print("-" * 60)
    r = orch.analyze_repo(repo_path, force_reanalyze=force)
    if r.get('source') == 'qwen_gpu':
        print(f"  ✅ KÉSZ: {r.get('qwen_elapsed_sec',0):.1f}s, "
              f"confidence={r.get('confidence',0):.3f} ({r.get('recommendation','N/A')})")
    else:
        print(f"  ⚠️ {r.get('source','?')}: {r.get('error','')}")
    results.append(r)

print("\n" + "=" * 60)
print("📊 BATCH ÖSSZEGZÉS")
print("=" * 60)
qwen_runs = [r for r in results if r.get('source') == 'qwen_gpu']
failures = [r for r in results if r.get('source') not in ('qwen_gpu', 'cache')]
print(f"Qwen GPU futtatások: {len(qwen_runs)}/{len(batch)}")
print(f"Hibák: {len(failures)}")
if qwen_runs:
    total_time = sum(r.get('qwen_elapsed_sec', 0) for r in qwen_runs)
    avg_conf = sum(r.get('confidence', 0) for r in qwen_runs) / len(qwen_runs)
    print(f"Összes Qwen idő: {total_time:.1f}s")
    print(f"Átlag confidence: {avg_conf:.3f}")

batch_file = f'/data/mcp_server/context/batch_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(batch_file, 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print(f"\nEredmények: {batch_file}")
