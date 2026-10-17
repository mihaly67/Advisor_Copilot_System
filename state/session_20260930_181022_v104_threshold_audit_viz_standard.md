# Session: v104_threshold_audit_viz_standard
*Időbélyeg: 2026-09-30T18:10:22.658896*

# v1.04 Threshold Audit + Viz Standard Kész — 2026.09.30

## THRESHOLD TISZTAZAS

### Korábbi probléma
- thresholds.txt: th_long=0.100, th_short=0.100, th_noise=0.900 (túl alacsony, grid search tartomány hibás)
- train_jules_v104.py grid: thl [0.10-0.40], ths [0.10-0.40], thn [0.70-0.90] — alsó határ túl alacsony!
- optuna_v104_gpu.py viszont: thl [0.30-0.45], ths [0.40-0.55], thn [0.35-0.60] — realisztikusabb

### Audit eredmény (teljes OOS, 12889 bar)
- **ZERO opposite (Long↔Short swap)** — a modell SOHA nem cseréli fel L és S-t!
- Minden hiba = "irányt jósol Noise bar-on" (DirAsNoise)

| THL | THS | THN | Trades | WR% | Profit | DirAsNoise |
|-----|-----|-----|--------|-----|--------|------------|
| 0.20 | 0.30 | 0.70 | 12173 | 61.3 | 10216 | 4710 |
| 0.35 | 0.40 | 0.50 | 10081 | 62.4 | 7806  | 3792 |
| 0.45 | 0.50 | 0.40 | 8051  | 63.8 | 5269  | 2911 |

### Választott: THL=0.35, THS=0.40, THN=0.50 (kiegyensúlyozott)

### Konfúziós mátrix (THL=0.35 THS=0.40 THN=0.50)
```
              Actual S   Actual N   Actual L
Pred Short     3214       1973          0
Pred Noise      571       1256        981
Pred Long         0       1819       3075
```

## VIZUALIZACIO STANDARD v1.0
- Sablon: /data/dev/projects/z-ai-copilot/src/viz_standard_template.py
- Doksi: /data/dev/projects/z-ai-copilot/docs/v104/VIZ_STANDARD.md
- 10/10 checklist garantált
- Színek RÖGZÍTVE: Long=#228B22, Short=#B22222, Noise=#888888

## FAJLOK
- Audit script: /data/dev/projects/z-ai-copilot/src/threshold_audit_v104.py
- Viz script: /data/dev/projects/z-ai-copilot/src/viz_v104_pred.py
- Sablon: /data/dev/projects/z-ai-copilot/src/viz_standard_template.py
- HTML: /data/dev/projects/z-ai-copilot/docs/v104/viz_v104_pred.html (444 KB)
- Thresholds: /data/dev/projects/z-ai-copilot/models/v104/thresholds.txt (THL=0.350, THS=0.400, THN=0.500)
- Audit JSON: /data/dev/projects/z-ai-copilot/models/v104/threshold_audit.json
- Standard MD: /data/dev/projects/z-ai-copilot/docs/v104/VIZ_STANDARD.md

## KÖVETKEZŐ LÉPÉS
- Ellentétes predikciók javítása → valójában DirAsNoise csökkentése
- Lehetőségek: (1) noise_weight növelése, (2) THN csökkentése, (3) új feature-k amik megkülönböztetik a Noise-t
