# Régime-Bias Diagnózis — TRÉNINGABLAK
*2026-09-23 22:10*

## Adatok időszak: 2026-06-15 → 2026-09-01

| Hónap | Ármozgás | % | Régime |
|---|---|---|---|
| 2026-06 | -318.5 | -7.36% | Bearish selloff |
| 2026-07 | +70.5 | +1.63% | Konszolidáció |
| 2026-08 | +384.1 | +8.87% | Erős rally |
| 2026-09 | -100.5 | -2.32% | Korrekció |

## Label eloszlás: Long=14,418 / Short=11,537 / Noise=5,184
**Long/Short = 1.25** — 25%-kal több Long címke!

## Gyökérok:
A tréningablak aszimmetrikus:
- Június: -7.36% esés (bearish)
- Augusztus: +8.87% rally (bullish) — **ez dominál**
- A modell a rally-ből tanulja: "árak emelkednek" → Long bias
- Short belépések a rally alatt **ellentétesek a trenddel** → opposite

## Konklúzió:
**NEM modell struktúra probléma, NEM instrumentum-specifikus**
→ **TRÉNINGABLAK RÉGIME-BIAS**

## Megoldások:
1. **Hosszabb tréningablak** — 6-12 hónap (több regime)
2. **Regime-stratifikált tanítás** — külön tanítás bullish/bearish/sideways periodusokon
3. **Sample weight** — inverse regime frequency súlyozás
4. **Walk-forward** — rolling retrain, mindig friss régime
5. **Adaptive labeling** — PT/SL ATR-scaled (rally-ban nagyobb PT, esésben kisebb)
