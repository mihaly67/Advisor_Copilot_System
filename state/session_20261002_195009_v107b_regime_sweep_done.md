# Session: v107b_regime_sweep_done
*Időbélyeg: 2026-10-02T19:50:09.166722*

v1.07b Regime-Szurt Side-free + Ablak Sweep — 2026-10-02

SWEEP EREDMÉNYEK (277 sec):

| Tag | WR | Profit | Lag | FwdL | FwdS | Circ(Side) | ThN | Opp |
|-----|-----|--------|-----|------|------|------------|-----|-----|
| v106_base | 61.0 | 10,555 | -8 | 49.5 | 50.1 | 0.9461 | 0.89 | 0 |
| free_3min_p7 | 35.2 | 647 | -1 | 53.0 | 47.6 | -0.0774 | 0.44 | 3906 |
| free_3min_p14 | 35.2 | 648 | -1 | 53.4 | 50.3 | -0.0888 | 0.44 | 3932 |
| regime_5min_p7 | 38.4 | 460 | 2 | 49.9 | 46.6 | -0.0708 | 0.21 | 1117 |
| regime_5min_p14 | 36.7 | 504 | 1 | 48.8 | 48.9 | -0.0724 | 0.48 | 1848 |
| regime_3min_p7 | 35.8 | 247 | 2 | 49.6 | 47.0 | -0.0715 | 0.30 | 1150 |
| regime_3min_p14 | 36.8 | 350 | 4 | 52.4 | 51.7 | -0.0720 | 0.31 | 1147 |

KULCS MEGÁLLAPÍTÁSOK:

1. KÖRKÖRÖSSÉG MINDEN VÁLTOZATBAN MEGSZŰNT: Circ ≈ -0.07 to -0.09 (vs 0.9461)
2. LAG JAVULT: -1 to +4 (vs -8) — de ez nem segít ha WR rossz
3. WR MINDIG 35-38% — TOVÁBBRA IS rosszabb mint véletlen!
4. PROFIT ZUHANT: 10,555 → 247-648

REGIME SZŰRÉS HATÁSA:
- Regime=Yes → 70-73% Noise (vs 34% regime-free)
- Kevesebb Opp error (1117-1848 vs 3906-3932)
- DE WR nem javult (35-38%)

ABLAK CSÖKKENTÉS HATÁSA (5→3 min):
- 3min → több Noise (34%→34% free, 70%→73% regime)
- Profit kisebb, Opp nem javult jelentősen

DIAGNÓZIS:
A Side-free labeler FUNDAMENTÁLIS problémája:
- PT=1.2$, SL=1.0$ 3-5 percen belül MINDKÉT irányba gyakran hit
- A "melyik hit először" question NEM elég prediktív
- Az ár 3 percen belül ingadozik — a Long/Short döntés zaj

A v1.06 61%-os WR ILLÚZIÓ volt — a modell csak az indikátort követte
A side-free 35%-os WR az IGAZSÁG — a triple barrier önmagában nem prediktív

KÖVETKEZŐ IRÁNY:
Nem a labeler módosítása segít, hanem:
(1) ASZIMMETRIKUS barrier — PT>SL (pl. PT=2.0, SL=0.8) — az árnak ERŐSEBBEN kell mozdulnia
(2) Vagy EGYIRÁNYÚ barrier — csak Long VAGY csak Short (regime alapján)
    de NEM Slope_Close_14-al, hanem más indikátorral (pl. Trend_Strength_20 + EMA50)
(3) Vagy ACCEPT: a v1.06 "követő" modell az ami van, és más szűréssel javítsuk