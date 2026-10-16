# Session: labelling_deep_study_20261009
*Időbélyeg: 2026-10-09T18:15:17.971006*

Labelling deep study complet. 3 levels of notes saved to /data/Brain/_qwen_analysis/:
- labelling_study_level1.md: Repo catalog, 5 key insights, correct pipeline diagram
- labelling_study_level2.md: Feature engineering (AlphaPy boolean, meta-labeling-alpha-filter real features, FreqAI, sample weights)
- labelling_study_level3_synthesis.md: FINAL SYNTHESIS - XAUUSD CFD labeling plan with:
  1. The QUESTION: P(TP hit | side, N bars, profit_mult×ATR) - binary per side
  2. CORRECT PIPELINE: Dollar Bar → CUSUM Filter → Side (+1/-1) → Side-aware TB → Meta-label → 2 Models
  3. Fork sources with line numbers from 4 repos
  4. What changes vs old V5 (7 items)
  5. 15-step implementation order (Phase 1-5)
  6. Key code: triple_barrier_xauusd() with side-aware barriers
  
KEY INSIGHT: The old V5 used symmetric TB (PT=SL=2×ATR) → random labels → AUC≈0.50. The fix is:
- CUSUM direction = side (primary model)
- Side-aware triple barrier (PT≠SL, different for Long vs Short)
- Boolean features (Above_EMA20, RSI_Oversold) for tree interpretability
- Context combinations (Fade_Short_Setup, Bounce_Long_Setup)
- 2 separate models (Long + Short)
- Sample uniqueness weights
- Purged walk-forward CV with beta benchmark