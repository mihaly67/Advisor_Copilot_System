#!/usr/bin/env python3
"""
GPU vs CPU ML Benchmark — Scalper Copilot kontextusban
  CPU: Xeon E5-2673 v4 @ 2.30GHz, 40 thread (1 socket, 20 core, HT)
  GPU 0: Quadro P4000 — 1792 CUDA cores, 8GB VRAM, compute 6.1
  GPU 1: Quadro P2000 — 1024 CUDA cores, 5GB VRAM, compute 6.1
  RAM: 62 GB

  Tesztek: LightGBM CPU vs GPU, sklearn RF vs cuML RF, KNN, CPU↔GPU overhead
"""
import os, sys, time, warnings
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

N_ROWS = [10_000, 100_000, 500_000, 1_000_000]
N_FEAT = 41; N_TREE = 300; SEED = 42

print("=" * 72)
print("GPU vs CPU ML BENCHMARK")
print(f"  CPU: Xeon E5-2673 v4 @ 2.30GHz, 40 thread")
print(f"  GPU: Quadro P4000 (1792 CUDA, 8GB)")
print("=" * 72)

def make_data(n_rows, n_feat=N_FEAT, seed=SEED):
    np.random.seed(seed)
    X = np.random.randn(n_rows, n_feat)
    y = (X[:,0]*X[:,1] + 0.5*X[:,2] - 0.3*X[:,3]*X[:,4] + 
         0.1*np.sin(X[:,5]*3) + np.random.randn(n_rows)*0.5) > 0
    return X, y.astype(int)

# ═══════════════════════════════════════════════════════════════
# 1. LIGHTGBM CPU vs GPU
# ═══════════════════════════════════════════════════════════════
print("\n" + "═"*50 + "\n1. LIGHTGBM — CPU vs GPU\n" + "═"*50)
lgbm_results = []

for n in N_ROWS:
    X, y = make_data(n)
    X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.2, random_state=SEED)
    
    # CPU (40 thread)
    dtr = lgb.Dataset(X_tr, label=y_tr)
    dva = lgb.Dataset(X_va, label=y_va, reference=dtr)
    p_cpu = {'objective':'binary','metric':'auc','learning_rate':0.05,'num_leaves':31,
             'feature_fraction':0.7,'bagging_fraction':0.8,'bagging_freq':5,
             'seed':SEED,'verbose':-1,'min_data_in_leaf':50,'lambda_l1':1.0,'n_jobs':40}
    t0 = time.time()
    m_cpu = lgb.train(p_cpu, dtr, N_TREE, [dva], callbacks=[lgb.early_stopping(30,verbose=False)])
    t_cpu = time.time() - t0
    auc_cpu = roc_auc_score(y_va, m_cpu.predict(X_va))
    
    # GPU (P4000)
    dtr_g = lgb.Dataset(X_tr, label=y_tr, free_raw_data=False)
    dva_g = lgb.Dataset(X_va, label=y_va, reference=dtr_g, free_raw_data=False)
    p_gpu = {k:v for k,v in p_cpu.items() if k != 'n_jobs'}
    p_gpu['device'] = 'gpu'; p_gpu['gpu_platform_id'] = 0; p_gpu['gpu_device_id'] = 0
    
    t0 = time.time()
    try:
        m_gpu = lgb.train(p_gpu, dtr_g, N_TREE, [dva_g], callbacks=[lgb.early_stopping(30,verbose=False)])
        t_gpu = time.time() - t0
        auc_gpu = roc_auc_score(y_va, m_gpu.predict(X_va))
    except Exception as e:
        t_gpu = -1; auc_gpu = -1; print(f"    GPU ERROR: {e}")
    
    sp_ = t_cpu/t_gpu if t_gpu > 0 else -1
    w = "🏆 GPU" if sp_ > 1.0 else "🏆 CPU"
    print(f"  N={n:>10,} | CPU: {t_cpu:.2f}s AUC={auc_cpu:.4f} | GPU: {t_gpu:.2f}s AUC={auc_gpu:.4f} | {sp_:.2f}x {w}")
    lgbm_results.append({'n':n,'t_cpu':t_cpu,'auc_cpu':auc_cpu,'t_gpu':t_gpu,'auc_gpu':auc_gpu,'speedup':sp_})

# ═══════════════════════════════════════════════════════════════
# 2. RANDOM FOREST — sklearn vs cuML
# ═══════════════════════════════════════════════════════════════
print("\n" + "═"*50 + "\n2. RANDOM FOREST — sklearn vs cuML\n" + "═"*50)
cuml_available = False
try:
    from cuml.ensemble import RandomForestClassifier as cuRF
    from cuml.neighbors import KNeighborsClassifier as cuKNN
    import cudf
    cuml_available = True
    print("  cuML elérhető! ✅")
except ImportError:
    print("  cuML Nincs telepítve ❌")

for n in N_ROWS:
    X, y = make_data(n)
    X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.2, random_state=SEED)
    
    t0 = time.time()
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, n_jobs=40, random_state=SEED)
    rf.fit(X_tr, y_tr)
    t_sk = time.time() - t0
    auc_sk = roc_auc_score(y_va, rf.predict_proba(X_va)[:,1])
    
    if cuml_available:
        t0 = time.time()
        cu_rf = cuRF(n_estimators=100, max_depth=10, random_state=SEED)
        cu_rf.fit(cudf.DataFrame(X_tr), cudf.Series(y_tr))
        t_cu = time.time() - t0
        auc_cu = roc_auc_score(y_va, cu_rf.predict_proba(cudf.DataFrame(X_va)).to_numpy()[:,1])
    else:
        t_cu = -1; auc_cu = -1
    
    sp_ = t_sk/t_cu if t_cu > 0 else -1
    w = "🏆 GPU" if sp_ > 1.0 else "🏆 CPU"
    cu_str = f"{t_cu:.2f}s AUC={auc_cu:.4f}" if t_cu > 0 else "N/A"
    print(f"  N={n:>10,} | sklearn: {t_sk:.2f}s AUC={auc_sk:.4f} | cuML: {cu_str} | {sp_:.2f}x {w}")

# ═══════════════════════════════════════════════════════════════
# 3. KNN
# ═══════════════════════════════════════════════════════════════
print("\n" + "═"*50 + "\n3. KNN — sklearn vs cuML\n" + "═"*50)
for n in [10_000, 100_000, 300_000]:
    X, y = make_data(n)
    X_tr, X_va, y_tr, y_va = train_test_split(X, y, test_size=0.2, random_state=SEED)
    
    t0 = time.time()
    knn = KNeighborsClassifier(n_neighbors=20, n_jobs=40)
    knn.fit(X_tr, y_tr)
    t_sk = time.time() - t0
    auc_sk = roc_auc_score(y_va, knn.predict_proba(X_va)[:,1])
    
    if cuml_available:
        t0 = time.time()
        cu_knn = cuKNN(n_neighbors=20)
        cu_knn.fit(cudf.DataFrame(X_tr), cudf.Series(y_tr))
        t_cu = time.time() - t0
        auc_cu = roc_auc_score(y_va, cu_knn.predict_proba(cudf.DataFrame(X_va)).to_numpy()[:,1])
    else:
        t_cu = -1; auc_cu = -1
    
    sp_ = t_sk/t_cu if t_cu > 0 else -1
    w = "🏆 GPU" if sp_ > 1.0 else "🏆 CPU"
    cu_str = f"{t_cu:.2f}s AUC={auc_cu:.4f}" if t_cu > 0 else "N/A"
    print(f"  N={n:>10,} | sklearn: {t_sk:.2f}s AUC={auc_sk:.4f} | cuML: {cu_str} | {sp_:.2f}x {w}")

# ═══════════════════════════════════════════════════════════════
# 4. CPU↔GPU ADATÁTVITEL
# ═══════════════════════════════════════════════════════════════
print("\n" + "═"*50 + "\n4. CPU↔GPU overhead\n" + "═"*50)
try:
    import cupy as cp; cupy_ok = True
    print("  CuPy ✅")
except ImportError:
    cupy_ok = False; print("  CuPy ❌")

if cupy_ok:
    for n in [100_000, 500_000, 1_000_000]:
        X = np.random.randn(n, N_FEAT)
        t0 = time.time(); X_g = cp.asarray(X); cp.cuda.Stream.null.synchronize()
        t_up = time.time() - t0
        t0 = time.time(); X_b = cp.asnumpy(X_g)
        t_dn = time.time() - t0
        print(f"  N={n:>10,} | Upload: {t_up*1000:.1f}ms | Download: {t_dn*1000:.1f}ms | Total: {(t_up+t_dn)*1000:.1f}ms")

# ═══════════════════════════════════════════════════════════════
# ÖSSZESÍTŐ
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*72}\nÖSSZESÍTŐ\n{'='*72}")
for r in lgbm_results:
    s = r['speedup']
    v = "GPU nyer 🏆" if s > 1.2 else ("CPU nyer 🏆" if s < 0.8 else "≈ egyforma")
    print(f"  LightGBM N={r['n']:>10,}: CPU={r['t_cpu']:.2f}s GPU={r['t_gpu']:.2f}s → {s:.2f}x ({v})")

print(f"\nKÖVETKEZTETÉS:")
print(f"  • P4000 (Pascal, compute 6.1) — RÉGI architektúra, limitált double prec.")
print(f"  • E5-2673v4 40 thread — ERŐS multi-thread, LightGBM kiválóan skáláz")
print(f"  • Scalper adat: 660K×41 — KICSI, GPU overhead dominálhat")
print(f"  • cuML (RF/KNN): 100K+ soron lehet GPU gyorsulás")
print(f"  • LightGBM GPU: Pascal arch-nál gyakran LASSABB mint CPU 40 thread!")
print(f"  • AJÁNLÁS: LightGBM marad CPU(n_jobs=40), cuML telepítése RF/KNN-re")
print(f"{'='*72}")