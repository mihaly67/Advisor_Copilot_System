# Session: v107e_alt_direction_breakthrough
*Időbélyeg: 2026-10-02T22:22:12.320594*

v107e ALT IRANY-INDIKATOR — ÁTTÖRÉS! 2026-10-02

EREDMÉNYEK:

| Side indikátor | WR | Profit | Lag | FwdL | Circ(Side) | Opp |
|----------------|-----|--------|-----|------|------------|-----|
| Slope_Close_14 (v1.06) | 61.0% | 10,555 | -8 | 49.5 | **0.946** | 0 |
| **Trend_Strength_20** | **52.3%** | **7,332** | **-7** | 48.9 | **0.501** | 0 |
| **Mom10_Direction** | **52.0%** | **7,218** | **-5** | 50.4 | **0.712** | 0 |

KULCS FELFEDEZÉSEK:

1. TREND_STRENGTH_20: Circ 0.95→0.50 — KÖRKÖRÖSSÉG FELEZŐDÖTT!
   WR 61%→52% — MÉG MINDIG >50% (igazi prediktív erő!)
   Profit 10,555→7,332 — 70% a baseline-nak, de NEM rosszabb mint véletlen!
   Lag -8→-7 — kis javulás
   Opp=0 — nincs ellentétes error

2. MOM10_DIRECTION: Circ 0.95→0.71 — KEVESEBB körkörösség
   WR 52% — igazi prediktív erő!
   Lag -8→-5 — JAVULÁS! (Mom10 gyorsabb mint Slope_14)
   Profit 7,218 — elfogadható

3. EMA50_Slope_Up: SKIP — mindenhol pozitív (nincs Short)
4. Regime_Trending: SKIP — bináris, nincs elég irány-információ

DIAGNÓZIS:
- Trend_Strength_20 a legjobb kompromisszum: Circ=0.50 (fele a baseline-nak)
- A modell MÉG MINDIG követi az indikátort, de KEVESEBBEN
- WR 52% = 2% a véletlenszint felett — van igazi prediktív szignal!
- Profit 7,332 = használható!

KÖVETKEZŐ:
- Trend_Strength_20 alapú label + two-phase S1×S2 szűrés
- P7 feature-kkel (lag javulás)
- Optuna optimalizálás ezen az alapon