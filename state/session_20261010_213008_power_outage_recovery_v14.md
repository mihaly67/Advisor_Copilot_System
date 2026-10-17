# Session: power_outage_recovery_v14
*Időbélyeg: 2026-10-10T21:30:08.505559*

ÁRAMSZÜNET RECOVERY (2026-10-10 21:08)

ÁLLAPOT:
- V14 pipeline LEFUTOTT 20:48-kor — modell épségben (mlp_meta_v12.pt, valAUC=0.823)
- Áramszünet 21:08-kor — 20 perccel V14 után
- Ensemble NEM MŰKÖDÖTT: LGBM v5 feature nevek Column_0..Column_16 (névtelenek), V14 nevesített feature-ökkel → 0 közös
- Nincs features.txt a jules_cfd_v5 modellben
- A következő lépés: V14 ensemble javítás — azonos feature-ökkel LGBM tanítás V14 adatokon

V14 MODELL ÁLLAPOT:
- valAUC=0.823, gap=0.0008, OOS=0.807±0.009
- 27 feature, h=64, l=4, dp=0.1, 14849 params
- Modell: /data/dev/projects/z-ai-copilot/models/v14/mlp_meta_v12.pt

KÖVETKEZŐ LÉPÉS:
1. V14 pipeline újrafuttatása (megerősítés)
2. LGBM tanítás V14 dollár bar adatokon azonos 27 feature-ökkel
3. Ensemble: MLP + LGBM weighted average (common features)
4. ZMQ/EA integráció