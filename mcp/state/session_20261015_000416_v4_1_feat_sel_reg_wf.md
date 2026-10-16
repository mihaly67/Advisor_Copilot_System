# Session: v4_1_feat_sel_reg_wf
*Időbélyeg: 2026-10-15T00:04:16.346427*

Scalper Copilot v4.0 — V4.1: Feature Selection + Regularization + Walk-Forward

IMPLEMENTÁLT:
1. Feature Selection: baseline quick train (3-fold, 100 round) → max(L_importance, S_importance) → csak >0.5% feature-k
   - 51 → 22-23 feature per horizon (28-29 eldobva)
   - Eldobva: ret_10, mom_persistence, flow_delta, ema_d_30, kill_zone_overlap, vol_ret_5, fvg_size, rsi_14, stb.

2. Regularization: reg_alpha 0.05→0.1, reg_lambda 0.3→0.5

3. Walk-Forward: 5 expandáló ablak, 12% test, idő-alapú (nincs shuffle!)
   - Train növekszik: [0→t1], [0→t2], ..., [0→t5]
   - Test mindig azonnal utána

AUC WALK-FORWARD (VALÓS):
  1min: L=0.577 S=0.658
  2min: L=0.571 S=0.556
  3min: L=0.579 S=0.562

AUC KFOLD (OVERFITTED, referencia):
  1min: L=0.698 S=0.608
  2min: L=0.649 S=0.610
  3min: L=0.591 S=0.570

KULCS FELISMERES:
- A KFold AUC ~0.65 ILLÚZIÓ volt! Walk-forward 0.55-0.58 a valós kép
- 1min Short a legerősebb (WF AUC=0.658) — a bar_dt panik-detektor működik
- 2min Long nagyon gyenge WF-en (0.571) — overfitting volt
- A direction feature-k (htf_trend, poc_dist, pv_corr) top-10-ben vannak
- noise_class mindenhol 0 importance — eldobható

KÖVETKEZŐ LÉPÉS:
- A WF AUC alacsony = a modell nem generál elég erős signált
- Meta-labeling: csak a valóban profitábilis szignálokat tanítsuk
- Több adat kell (full dataset) — jelenleg csak 4 nap külön vizsga