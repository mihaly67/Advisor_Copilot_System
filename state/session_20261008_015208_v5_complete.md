# Session: v5_complete
*Időbélyeg: 2026-10-08T01:52:08.968512*

V5 PIPELINE KÉSZ. 4 bug javítva (CUSUM threshold dimenzió, Short label kizárás, 3-class→binary, CUSUM_dir shift=0). Eredmények: PT=1.5/SL=1.0 Fade CUSUM = legjobb (OOS 50.5%/$758, VIZSGA 51.2%/$394). Fade+ML conf VIZSGA 57.0%! ML alone overfitting. KÖVETKEZÉS: Optuna + shallow MLP (PyTorch P4000) + regime/pivot feature-k + embedding→LGBM. Környezet: PyTorch 2.4.1+cu121, Optuna 5.0.0, P4000 8GB free.