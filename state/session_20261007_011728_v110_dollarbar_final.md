# Session: v110_dollarbar_final
*Időbélyeg: 2026-10-07T01:17:28.115627*

V110 DOLLAR BAR PIPELINE CFD-NEK

prado_dollar_bars.py logika: Dollar_Value = Mid_Price x 1.0 (tick-count proxy)
Adaptiv ATR-normalt kuszob: weight = (Mid_Price x ATR) / (threshold x ATR_median)
Ez MUKODIK vizsgan is (nem kell volume!)

Eredmenyek (8 konfiguracio):
444K-adapt-18f-MB5: OOS=44.2% Viz=47.7% Gap=-3.5% (legjobb WR)
444K-fix-18f-MB5: OOS=41.7% Viz=42.1% Gap=-0.4% (legstabilabb)
444K-adapt-18f-MB8: OOS=44.0% Viz=48.9% Gap=-4.9%

Osszehasonlitas volbar vs dollarbar:
- Volbar ($3.0 ATR): OOS=50.4% Viz=51.3% Gap=-0.9%
- Dollarbar ($444K adapt): OOS=44.2% Viz=47.7% Gap=-3.5%

A volbar jobb WR-t ad, de a dollarbar a Jules eredeti megkozelitese.
A Jules threshold konzervativ (STABILITY_WINDOW=3), lehet optimalizalni.

Fontos: a jules_v110_reproduction.py HASZNALTA a Bid_Volume+Ask_Volume-t
ami vizsgan 0 -> 0 sor ment volna bele! A prado_dollar_bars.py viszont
Mid_Price x 1.0 proxy-t hasznal ami mukodik volume nelkul.
