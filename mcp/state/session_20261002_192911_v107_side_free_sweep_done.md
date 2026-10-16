# Session: v107_side_free_sweep_done
*Időbélyeg: 2026-10-02T19:29:11.603932*

v1.07 Side-Független Labeler + Periódus Sweep — 2026-10-02

SWEEP EREDMÉNYEK (178 sec):

| Ver | WR | Profit | Lag | FwdL | FwdS | Circ(Side) | Circ(Slp) | ThN |
|-----|-----|--------|-----|------|------|------------|-----------|-----|
| v106_baseline | 61.0 | 10,555 | -8 | 49.5 | 50.1 | 0.9461 | 0.7523 | 0.89 |
| p5_side_free | 37.8 | 1,498 | -1 | 51.4 | 52.7 | -0.0949 | -0.1114 | 0.32 |
| p7_side_free | 36.9 | 1,365 | -1 | 53.8 | 51.8 | -0.0917 | -0.1278 | 0.54 |
| p9_side_free | 37.4 | 1,408 | -1 | 52.1 | 50.5 | -0.0992 | -0.0935 | 0.34 |
| p14_side_free | 37.6 | 1,571 | -1 | 49.3 | 51.8 | -0.0773 | -0.0850 | 0.40 |

KULCS FELFEDEZÉSEK:

1. KÖRKÖRÖSSÉG MEGSZAKADT: Circ(Side) 0.9461 → -0.08!!! 
   A modell NEM követi többé az indikátort. Corr közel 0 = nincs körkörösség.

2. LAG ELTŰNT: P(Long) lag -8 → -1 minden periódusnál!
   A modell már nem 8 bar-ral késik.

3. DE WR ZUHANT: 61.0% → 37-38% (MINDEN változatnál!)
   Ez alatt az 50%-os véletlenszint — a modell ROSSZABB mint véletlen!

4. Forward WR javult: 49.5% → 51-53% (p5, p7)
   A modell valójában KICSIT jobban prediktálja a következő bar irányát,
   de a label WR rossz — a triple barrier maga nem elég prediktív.

5. ThN nagyon alacsony: 0.32-0.54 (vs baseline 0.89)
   A modell nem tudja megkülönböztetni a Noise-t a Dir-től.

6. Top5 feature-k megváltoztak: RSI_M15, Regime_ADX → Wick_Lower_ATR, Wick_Upper_ATR
   Teljesen más döntési logika!

DIAGNÓZIS:
- A Side-free label "igaz" — nem körkörös
- De a PT=1.2$/SL=1.0$ triple barrier 5 percen belül MINDKÉT irányba gyakran hit
  → L≈36%, S≈37%, N≈27% (vs Side-alapú L=29%, S=33%, N=38%)
  → Túl sok irányos label — zaj van bennük
- A modell "összezavarodik" — nem tudja, melyik irány a helyes

KÖVETKEZŐ LÉPÉS:
- A label struktúra a probléma, nem a feature periódus
- Lehetőségek: (1) aszimmetrikus PT/SL, (2) időablak csökkentés, 
  (3) min_move threshold, (4) Regime-alapú irány szűrés (de nem Side!)