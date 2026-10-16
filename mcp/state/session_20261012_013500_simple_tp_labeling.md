# Session: simple_tp_labeling
*Időbélyeg: 2026-10-12T01:35:00.091597*

Simple TP címkézés (SL nélkül) implementálva és tesztelve.

Kulcsfelismerés: SL = zaj forrás. SL nélkül tiszta bináris kérdés: eléri-e a TP-t X percen belül?

Eredmények ($30 TP, 5 perc, 5m EMA20):
- Long WR: 58.9%, Short WR: 59.4%, EMA filtered WR: 64.1%
- Info: +14.1% vs random 50%
- Nincs SL zaj, nincs timeout ambiguity

Grid search top: $20 TP/30bar/5m_EMA20 = 80.6% WR (+30.6% info)
Reális: $30 TP/18bar/5m_EMA20 = 64.1% WR (+14.1% info)

Config frissítve: SIMPLE_TP_DIST=30, SIMPLE_TP_MAX_BARS=18, SIMPLE_TP_EMA_PERIOD=20, SIMPLE_TP_EMA_RS_SEC=300

Következő: 02_label_simple_tp.py teljes pipeline implementálás, feature generálás, LightGBM tréning