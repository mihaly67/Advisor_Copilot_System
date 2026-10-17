# Session: v11_deep_study_complete
*Időbélyeg: 2026-10-10T00:49:51.295718*

V11 DEEP STUDY COMPLETE — 5 jegyzet:
1. WHY NN OVERFITS (globális param vs lokális tree, gradiens aszimmetria, 5 ok-okozat lánc)
2. 6+ DETECTION METHODS (train/val gap, purged CV, learning curve, label permutation, bootstrap CI, dropout sensitivity, +2)
3. INTERACTIONS + FINANCIAL SPECIFIC (non-i.i.d., regime change, double descent, scale-free design)
4. EMPIRICAL EVIDENCE (32→18 feature, ρ=+1.0 redundáns párok, ρ₁=0.84 autokorreláció, N_eff=61% nominális)
5. FOCAL LOSS MATH + PER-BAR LABEL DESIGN + IMPLEMENTATION PLAN

KULCS FELFEDEZÉSEK:
- ema8_gap_f ↔ ema8_slope_f ρ=+1.000 → matematikailag ekvivalens!
- body_sign_f ↔ Bullish_Bar_f ρ=+0.999 → definíció!
- body_f ↔ PastRet_1_f ρ=+0.996 → body ≈ return!
- 32→18 feature redukció: 44% kevesebb param, data/param 49→72
- ticks_inv_f ρ₁=0.837 → NAGYON korrelált temporálisan
- wick_u_r_f ρ₁=-0.001 → tökéletesen független! (scale-free design működik!)
- RSI [0,100] nem centred → (RSI-50)/50 kell
- Focal Loss γ=2: könnyű sample gradiens 5× kisebb, nehéz 2.6× nagyobb
- Per-bar binary meta-label: 72:1 imbalance → Focal Loss kezelheti