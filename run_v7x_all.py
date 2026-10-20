#!/usr/bin/env python3
"""Runner — futtatja az 5 Optuna kísérletet szekvenciálisan, eredményt JSON-be gyűjti."""
import subprocess, sys, json, time
from pathlib import Path
from datetime import datetime

EXPERIMENTS = [
    {"name": "c25_auc",   "args": ["--contra_max", "0.25", "--obj", "auc",    "--n_trials", "40"]},
    {"name": "c30_auc",   "args": ["--contra_max", "0.30", "--obj", "auc",    "--n_trials", "40"]},
    {"name": "c25_wrauc", "args": ["--contra_max", "0.25", "--obj", "wr_auc", "--n_trials", "40"]},
    {"name": "c20_wrauc", "args": ["--contra_max", "0.20", "--obj", "wr_auc", "--n_trials", "40"]},
    {"name": "c25_ev",    "args": ["--contra_max", "0.25", "--obj", "ev",     "--n_trials", "40"]},
]

SRC = Path("/data/LGBM_copilot/src")
LOGD = Path("/data/LGBM_copilot")
RESULT_FILE = LOGD / "v7x_all_results.json"

all_results = {}
for exp in EXPERIMENTS:
    name = exp["name"]
    logf = LOGD / f"v7x_{name}.log"
    print(f"\n{'='*60}\n{datetime.now():%H:%M:%S} START: {name}\n{'='*60}", flush=True)
    
    cmd = [sys.executable, "-u", str(SRC / "scalper_optuna_v7x.py")] + exp["args"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=False, timeout=3600,
                            stdout=open(logf, 'w'), stderr=subprocess.STDOUT)
        elapsed = time.time() - t0
        print(f"  DONE in {elapsed:.0f}s (rc={proc.returncode})", flush=True)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after 3600s!", flush=True)
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
    
    # Read result JSON
    tag_map = {"c25_auc": "c25%_auc", "c30_auc": "c30%_auc", 
               "c25_wrauc": "c25%_wr_auc", "c20_wrauc": "c20%_wr_auc", "c25_ev": "c25%_ev"}
    tag = tag_map.get(name, name)
    rfile = LOGD / "charts" / f"optuna_v7x_{tag}.json"
    if rfile.exists():
        all_results[name] = json.loads(rfile.read_text())
        print(f"  Results loaded: {list(all_results[name].keys())}", flush=True)
    else:
        print(f"  No result file: {rfile}", flush=True)

RESULT_FILE.write_text(json.dumps(all_results, indent=2, default=str))
print(f"\n{'='*60}\nALL DONE — results: {RESULT_FILE}", flush=True)
for name, res in all_results.items():
    for hn, bp in res.items():
        c = bp.get('constraints', {})
        print(f"  {name}/{hn}: val={bp.get('value',0):.4f} contra={c.get('contra',0):+.1%}", flush=True)
