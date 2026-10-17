# Session: v11_data_overfit_analysis
*Időbélyeg: 2026-10-10T00:25:50.861473*

V11 MLP adat/overfitting analízis KULCS EREDMÉNYEK:
- 2.5 hónap adat: 42,742 dollár bar, 2,642 CUSUM event, 583 TP
- Event-based MLP: LEHETETLEN (2,642 sample, még H=8 L=1 is data/param=6.9 gyenge)
- Per-bar MLP tiny (H=16 L=2): MŰKÖDIK (data/param=39.5), de class imbalance 72:1
- Per-bar MLP medium (H=32 L=2 W=5): OVERFIT (data/param=2.8)
- 1 év per-bar adat: 202,575 sample → medium MLP is OK (data/param=13)
- LGBM miért működik event-eken: tree model nem gradient descent, más dinamika
- Overfitting detektálás: train/val gap, purged CV, learning curve, label permutation, bootstrap CI, dropout sensitivity
- AJÁNLÁS: Opció A (2.5hó per-bar tiny MLP gyors validáció) → Opció B (1+ év medium MLP éles)