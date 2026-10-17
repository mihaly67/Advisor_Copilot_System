# Session: gpu_mandatory
*Időbélyeg: 2026-09-28T23:27:51.450505*

GPU KÖTELEZŐ SZABÁLY:
- P4000 (GPU 0) = primary compute minden ML feladathoz (LGBM, SHAP, Optuna, PyTorch)
- P2000 (GPU 1) = secondary (Qwen LLM, data prep)
- LGBM: device='gpu', gpu_platform_id=0, gpu_device_id=0 — SOHA device='cpu'
- OpenCL: /etc/OpenCL/vendors/nvidia.icd, NVIDIA CUDA 13.0 OpenCL 3.0
- Benchmark: LGBM GPU 2.9x faster vs CPU
- Beégve: .clinerules/universal.md, .clinerules/ml-python.md, memory-bank/techContext.md