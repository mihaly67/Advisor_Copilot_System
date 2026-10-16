# Session: meta_labeling_v1_results
*Időbélyeg: 2026-09-24T03:57:01.595156*

Meta-labeling implementálva és tesztelve. V8 labeler: Primary=Slope_Close_14>0→Long, Triple barrier PT=1.2$/SL=1.0$/8bar. Meta label: Trade 51.6%, Pass 48.4%. 

META_V1 (30 feature): AUC=0.533, Accuracy=51.85%. Legjobb th=0.35: Profit=$3237 de baseline=$3258 — a secondary modell NEM ad hozzá. th=0.65-re szűrve: Win=65.6%, Opp=34.4%, de csak 273 trade.

META_V2 (114 feature): SHAP-ban Wick_Asymmetry és Bar_Direction feljutott top 10-be.

Kulcs felismerés: a secondary modell AUC=0.533 — alig jobb a random-nál. A primary modell (Slope_Close_14) 51.6%-os PT rate — ez a ceiling. A meta-labeling nem segít mert a primary modell túl gyenge. 

Következő lehetőségek:
1. Erősebb primary modell (nem csak slope — pl EMA crossover, vagy multi-signal)
2. Long-only: a th=0.65-nél Short win 65.6% volt — érdemes vizsgálni
3. Más labeling: fixed horizon return > threshold