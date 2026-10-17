# Session: scalper_v3_plus_advisors
*Időbélyeg: 2026-10-14T02:03:17.122042*

SCALPER V3 + ADVISORS TUDÁSBŐVÍTÉS (2026-10-13)

## V3 Pipeline State
- Dollar bar labels ($10M threshold) + MTF tick features → $50 TP / 60s horizon
- Optuna AUC 0.7035, 5-fold retrain Long=0.6715 Short=0.6461
- Top features: tv_60, tv_20, atr_pct, micro_sqz, rsi_n

## Advisors Knowledge Build (ÚJ!)
- 11 GitHub repo klónozva /data/Brain/advisors/ (~16MB, 826 fájl)
- Kulcs felfedezések mások signal logikájából:
  1. Volume Profile POC — mágneses S/R szint (NINCS még nálunk)
  2. Fair Value Gap — low[i]>high[i-1] gap detektálás (NINCS még)
  3. Order Block — strukturális S/R zónák (NINCS még)
  4. Kill Zone / Session filter — idő-alapú szűrés (NINCS még)
  5. Meta-labeling — primary=side, secondary=size (JAVÍTANÁ modellen)
  6. Multi-confirmation scoring (6/8 vagy 4/7 minimum) — validálja megközelítésünket
  7. Fresh Trigger — csak első bar szignál (JAVÍTANÁ signal minőségen)

## Next Steps (prioritás sorrend)
1. Add Volume Profile POC feature to MTF tick features
2. Add FVG + Order Block detection features
3. Add Session/Kill Zone time-of-day feature
4. Try Meta-labeling approach (combined model)
5. Walk-forward validation
6. Integrate into scalper_continuous.py
