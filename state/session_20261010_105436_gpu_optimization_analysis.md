# Session: gpu_optimization_analysis
*Időbélyeg: 2026-10-10T10:54:36.183281*

GPU OPTIMALIZÁCIÓ ANALÍZIS (2026-10-10)

Hardver:
- CPU: Intel Xeon E5-2673 v4 × 40 mag @ 2.30GHz
- GPU 0: Quadro P4000 — 14 SM, ~1792 cores, 8GB VRAM, Pascal
- GPU 1: Quadro P2000 — 8 SM, ~640 cores, 5GB VRAM, Pascal

MLP Training Benchmark (bs=2048):
- V12 MLP (3k params): P4000=3.0ms/step, P2000=3.3ms/step → P2000 90% of P4000
- Nagy MLP (87k params): P4000=4.5ms, P2000=4.5ms → AZONOS!
- Transformer (471k params): P4000=5.8ms → P2000 nem mérve de ~6ms

LGBM GPU Benchmark:
- 50k×25: CPU=0.4s, P4000=1.1s, P2000=1.0s → GPU LASSABB!
- 500k×25: CPU=3.7s, P4000=5.5s → GPU még mindig lassabb
- 500k×100, 1000 fa: CPU=18.8s, P4000=28.8s → GPU TOVÁBBRAIG LASSABB
- KÖVETKEZET: LGBM GPU Pascal arch-on SOHA nem gyorsabb CPU-nál ezen a méreten!

DDP Speedup Estimate:
- V12 MLP (3k params): 1.82x speedup 2 GPU-n (AllReduce=2μs, elhanyagolható)
- Nagy MLP (87k params): 1.78x speedup (AllReduce=58μs)
- Transformer (471k params): 1.65x speedup (AllReduce=314μs)

FŐ MEGÁLLAPÍTÁSOK:
1. MLP túl kicsi → GPU alul kihasznált → P2000≈P4000 (memory-bound, nem compute-bound)
2. LGBM GPU Pascal-on LASSABB mint CPU (feature histogram párhuzamosítás Pascal GPU-n nem optimalizált)
3. 2×P4000 DDP: 1.65-1.82x speedup MLP-n (AllReduce elhanyagolható kis modellnél)
4. IGAZI bottleneck: DataLoader GIL, nem GPU compute
5. CPU 40 mag: csak feature engineering + Numba CUSUM/TB tudja kihasználni