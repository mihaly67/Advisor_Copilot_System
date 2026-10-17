# Session: lag_analysis_task_corrected
*Időbélyeg: 2026-10-01T00:43:22.387168*

# Z.ai Copilot — KOVETKEZO SESSION FELADAT (korrigalt)

## PREDIKCIO KESLELTETES (LAG) VIZSGALATA

A viz_v106_pred.html-ben lathato: a predikcio **6-7 barnyi kesessel** mozog az ar mogott.

### FONTos korrekcio: EZ NEM LOOK-AHEAD!
Look-ahead eseten a predikcio ELORE mutatna (korabban jonne), nem kesne!
A 6-7 bar keses az indikatorok lassu reagalasa miatt van — BACKWARD-LOOKING simitas.

### Valoszinu ok: 14-15 periodos indikatorok
- **Slope_Close_14** — 14 periodos slope → ~7 bar keses a trend elejen
- **Micro_RSI_14** — 14 periodos RSI → simit, kesik
- **EMA50_Slope_Up** — 50 periodos EMA → nagyon lassu
- **Trend_Strength_20** — 20 periodos ablak → simit
- **Stoch_D** — 3/3 slowing → szinten simit

Ezek termeszetuknel fogva simitanak es kesnek — nem hiba, hanem
a indikatorok inherens tulajdonsaga. De kerdes: lehet-e csokkenteni
a kesest gyorsabb indikatorok hozzaadasaval?

### Vizsgalandi kerdesek:
1. Melyik indikator okozza a legnagyobb kesest? (cross-correlation lag analizis)
2. Ha hozzaadunk 5-periodos gyors indikatorokat, javul a reakcio?
3. Mennyi lag toleralhato trading szempontbol? (1-2 bar OK, 6-7 mar sok)
4. Lehet-e a predikciot "gyorsitani" rovidebb ablaku indikatorokkal?

### Teszt terv:
1. P(Long) es ar valtozas cross-correlation: lag=-10..+10
2. Feature-onkenti lag meres: melyik indikator mennyit kesik
3. Gyors indikatorok tesztelese: RSI_3, Slope_5, Momentum_3, stb.
4. Lag csokkentese utan ujra teszt: javul-e a WR es profit?

### Celpont: 2-3 bar ala csokkenteni a lag-et (1-3 bar OK, 6-7 bar sok)
