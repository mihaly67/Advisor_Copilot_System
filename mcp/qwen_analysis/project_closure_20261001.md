# Z.ai Copilot — Projekt Lezaras + Kovetkezo Feladat

**Datum**: 2026.10.01

## Eredmeny: +4,780 profit (+89.1%) vs v1.04

## !! KOVETKEZO SESSION: PREDIKCIO LAG VIZSGALAT !!

A viz_v106_pred.html-ben lathato: a predikcio **6-7 barnyi kesessel** mozog az ar mogott.

### Vizsgalandi okok:
1. Feature lag (RSI_M15, EMA, Pivot szintek look-ahead-je)
2. Label lag (Target_Label szamitasa idopontja)
3. Prediction lag (P(Long) peak vs ar valtozas idopontja)
4. CSV idosorrend

### Teszt terv:
1. P(Long) es ar valtozas cross-correlation lag=-7..+7
2. Feature-ok look-ahead audit (cross-correlation)
3. Label szamitas logika ellenorzes (dom_labeler)
4. Predikcio vs ar valtozas idopont osszehasonlitas
