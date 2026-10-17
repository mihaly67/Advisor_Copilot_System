# Session: rag_risk_trade_research
*Időbélyeg: 2026-09-24T04:11:46.504823*

RAG kutatás befejezve. 5 kulcs repo találat:

1. XAUUSD Scalping AI (score 0.64): Aszimmetrikus pozícióméret Long 2% Short 0.02%, aszimmetrikus TP/SL Long 1000pt/400pt Short 10pt/20pt. Win rate Short 70%+ Long 60%+. Session London/NYC.

2. DART Risk Management (score 0.64): Kelly Criterion f*=(p·b-q)/b, fractional Kelly (0.5-0.75x), volatility-adjusted sizing Size=(Account×Risk%)/(ATR×Multiplier), drawdown limit 15%.

3. Tensortrade (score 0.48): Reduce frequency 10x, position sizing binary BSH helyett, confidence threshold, time-based filtering.

4. Kalshi Edge Filter (score 0.46): Edge=AI_prob-market_prob, min edge 8%, min confidence 50%.

5. mlfinlab meta-labeling: side_prediction + secondary probability → bet sizing.

Jelenlegi adatok: 546 bar/nap átlag, $444K threshold, 57 nap adat. Felhasználó: manuális kereskedő, 60 trade/nap kevés, th=0.35 profit $3237 de kockázatkezelés nélkül.

Javaslat: (A) Dollar bar threshold $444K→$222K (2x több bar), (B) th=0.45 (középút), (C) Fractional Kelly 0.25x sizing, (D) Confidence-graded sizing 0.5x-1.5x.