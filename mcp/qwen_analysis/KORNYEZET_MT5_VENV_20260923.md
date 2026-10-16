# Környezet Rögzítés — MT5 + venv + Útvonalak
*Időbélyeg: 2026-09-23*

## MetaTrader 5 (Wine)
- **Útvonal:** `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/`
- Scripts: `.../MQL5/Scripts/`
- Indicators: `.../MQL5/Indicators/Indicators/`
- Files (CSV): `.../MQL5/Files/`
- **NEM kell telepíteni** — Wine alatt fut
- **MetaTrader5 Python csomag NEM kell** — offline pipeline MT5 nélkül megy

## Központi venv: `/home/Jules/jules_venv/`
- Python: `/home/Jules/jules_venv/bin/python3`
- Pip: `/home/Jules/jules_venv/bin/pip`

### Telepítve:
ta 0.11.0, lightgbm 4.7.0, optuna 5.0.0, scikit-learn 1.8.0, pandas 3.0.3, numpy 1.26.4, joblib 1.5.3, pyzmq 27.2.0, PyQt5 5.15.10, pyqtgraph 0.14.0, matplotlib 3.11.1, catboost 1.2.10

### Hiányzik:
- **shap** → `/home/Jules/jules_venv/bin/pip install shap`

### Opcionális:
- MetaTrader5 (csak éles copilothoz, offline pipeline nem kell)

## Projekt útvonalak
- Gyökér: `/home/Jules/LGBM_mlops/`
- Master CSV: `/home/Jules/LGBM_mlops/Master_csv/`
- Pipeline: `/home/Jules/LGBM_mlops/Micro_LGBM/src/`
- Terv: `/data/Brain/_qwen_analysis/SCALPER_PIPELINE_PLAN_20260923.md`
- NavSystem: `/data/Brain/_qwen_analysis/NAVSYSTEM_V222_PYTHON_FORDITAS_20260923.md`

## Pipeline futtatás
```bash
cd /home/Jules/LGBM_mlops/Micro_LGBM/src
/home/Jules/jules_venv/bin/python3 pipeline_master.py
```

## ta könyvtár megjegyzés
- tartalmaz: RSI, MACD, MFI, Stoch, EMA, BB, ATR, ROC, CCI, ADX, Keltner
- WPR hiányozhat → talib.WILLR vagy manuál