# Jules V1.10 Pipeline — Tick-alapú Dollar Bar eredmények

## V2 CSV Volume elemzés (BID+ASK flag javítás UTÁN)
- Sorok: 4,150,493
- Bid+Ask mindkettő >0: 4,056,391 (97.7%) ✅
- Bid_only: 49,588 (1.2%)
- Ask_only: 44,514 (1.1%)
- Nincs volume: 0 (0.0%) ✅
- Ask/Bid arány: 0.998 (imbalance -0.1%) ✅

## Pipeline futás #1 (threshold=$444K)
- Dollar Bars: 575,843 (átlag 7.1 sec/bar) ← TÚL SOK
- Labeled: 431,903 bars
- WR: 18.9% (threshold), 18.4% (stoch), 18.8% (stability) ← GYENGE
- Circ: 0.0713
- Probléma: $444K threshold tick-count proxy-val túl kicsi → túl sok bar → túl zajos

## Threshold rescaling
- Dollar/sec = 444000 / 7.1 = $62,535/sec (tick-count proxy)
- 20 sec/bar → threshold = $1,250,700
- Cél: ~210K dollar bars (mint Jules eredeti)

## Pipeline futás #2 (threshold=$1.25M) — FOLYAMATBAN
- A pipeline lefut, de lassú (4M+ sor betöltés + dollar bar + feature + label + train)
- Eredmények várva: ~210K bars, jobb WR

## MQL5 Script javítások
1. TICK_FLAG_BUY/SELL → nem létezik CFD-n
2. TICK_FLAG_BID/ASK → BID=eladó, ASK=vevő (CFD fő flag-ek)
3. `else if` → független `if` (BID+ASK egyszerre jön)
4. Eredmény: Bid_Volume ≈ Ask_Volume (97.7% mindkettő > 0)
