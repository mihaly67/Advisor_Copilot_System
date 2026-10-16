# P4000 GPU Setup + V11 Class Weights Results
*2026-09-23 23:15*

## GPU Setup — P4000 LightGBM
- Installed: nvidia-opencl-icd 580.178.04 (NVIDIA OpenCL ICD)
- Installed: clinfo (OpenCL platform verification)
- LightGBM 4.7.0 with device='gpu' mode
- OpenCL 3.0 CUDA 13.0.100 platform
- P4000: 8GB VRAM, GPU training works
- CPU n_jobs=1 → VSCode nem fagy ki

## Trainer config:
```python
clf = lgb.LGBMClassifier(
    n_estimators=781,
    learning_rate=0.0142,
    num_leaves=57,
    max_depth=6,
    min_child_samples=24,
    colsample_bytree=0.566,
    class_weight={0: 1.5, 1: 0.5, 2: 1.3},  # 0=Short 1=Noise 2=Long
    objective='multiclass',
    num_class=3,
    random_state=42,
    n_jobs=1,          # CPU kímélés
    device='gpu',       # P4000 OpenCL
    gpu_platform_id=0,
    gpu_device_id=0,
    verbose=-1
)
```

## V11 Final Results (regime labeling + class weights 1.5/0.5/1.3):
- Accuracy: 46.8%
- Short Recall: 29.1%, Precision: 36.2%
- Long Recall: 81.8%, Precision: 47.8%
- Opposite: 18.6% (was 30.7% at V9!)
- Cohen d Regime_ADX: 1.151 (was 0.049)

## Evolution:
| Version | Accuracy | Long R | Short R | Opposite |
|---|---|---|---|---|
| V9 (microstructure) | 40.2% | 44.3% | 33.8% | 30.7% |
| V10 (regime features) | 40.5% | 43.9% | 35.5% | 30.6% |
| V11 (regime labeling) | 45.9% | 14.3% | 93.3% | 20.7% |
| V11 (weights 1.5/0.5/1.3) | 46.8% | 81.8% | 29.1% | 18.6% |

## Next:
- Optuna threshold calibration on V11 model
- SHAP analysis on new model
- Visualization update
