# V110 VolBar Final - Teljes eredmeny

## Vegetes konfiguracio
- Bar: Volatility bar, ATR_target=$3.0
- CSV: Scalper_Copilot_MTF_Data_v2.csv (tanito), _kulon_vizsga.csv (vizsga)
- Triple Barrier: PT=$1.5, SL=$1.0, max_bars=8
- Threshold (opt): THL=0.384, THS=0.501, THN=0.202

## Bar tipus osszehasonlitas (40 kombinacio)
TOP 5 Vizsga WR (stabil, gap<3%):
1. volbar_3_PT1.5_SL1.0_MB8: OOS=50.4% Viz=51.3% Gap=-0.9% P=$717+$279
2. volbar_3_PT2.0_SL1.5_MB8: OOS=49.5% Viz=50.3% Gap=-0.8% P=$562+$222
3. 100tick_PT2.0_SL1.5_MB8: OOS=50.9% Viz=49.5% Gap=+1.4% P=$200+$94

## Threshold opt vegetes
OOS WR=50.8% Viz WR=51.7% Gap=-0.9% STABIL

## Mit tanultunk
- Volatility bar MUKODIK - a korabbi problema a PT/SL/MB rossz beallitasa
- MB=8 >> MB=5
- PT=$1.5 SL=$1.0 a legjobb arany volbar_3-hoz
- volbar_5 overfitting (gap 10%)
- Threshold opt kritikus (THS=0.501 szigoru short)
