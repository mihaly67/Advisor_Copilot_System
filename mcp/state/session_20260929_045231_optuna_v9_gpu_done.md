# Session: optuna_v9_gpu_done
*Időbélyeg: 2026-09-29T04:52:31.650014*

OPTUNA V9 GPU BEFEJEZŐDÖTT:
- 300 trial P4000 GPU, Best P=$+2,790
- WPR period=5, OB=82, OS=12
- 4D: th_L=0.377, th_S=0.372, th_NL=0.402, th_NS=0.405
- LGBM: lr=0.0325, leaves=58, depth=10, mc=10, n_estimators=1000+early_stopping(50)
- 28 feature (minden 7 WPR feature benne)
- Modell: models/v9_optuna_best/ (model.pkl, features.txt, metrics.json)
- GPU: device='gpu', gpu_platform_id=0, gpu_device_id=0
- Idő: 82 perc (GPU ~5x gyorsabb CPU-nál)
- CPU összehasonlítás: Best=$2,670 → GPU +4.5% javulás