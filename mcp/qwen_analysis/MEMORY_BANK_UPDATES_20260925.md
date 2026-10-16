# Memory Bank Updates — Kézi frissítéshez (2026.09.25. 03:30)

## activeContext.md — Cserélendő szöveg

### Feladat sor (6):
**Jules fusion_v5 pipeline javítása — causal ZigZag + újratanítás + OOS validáció**

### Új szekció hozzáadása (a lookahead bias szekció után):

```
## Dollar Bar + Indikátor Architekturális Felismerés (2026.09.25.)

A klasszikus indikátorok (RSI, Stoch, MACD) EGYENES időközű adaton értelmesek.
Dollar bar nem időalapú → "14 periódus" = változó időtartam (2sec vagy 30perc).

**Két megközelítés:**
- **Z.ai (volume-synchronized):** Indikátor KÖZVETLENÜL dollár baron — AFML style, információ-hatékonyabb aktív piacon. Működik: 54.3% WR.
- **Jules (idő-kompatibilis):** Indikátor M1-en + merge_asof backward — klasszikus értelmezés valid, de pivotoknak causalisnak kell lenniük.

**Kulcs felismerés:** `Scalper_Copilot_MTF_Data.csv` már tartalmazza az EA-sent CAUSALIS pivotokat! Nem kell új Python ZigZag engine — elég ezt használni a `Master_ZigZag_GCEQ26_M1.csv` helyett.

## Jules Pipeline Javítási Terv

1. **Causal pivot forrás:** Scalper_Copilot_MTF_Data.csv (port 5555 EA-sent pivotok)
2. **Dollar bar építés:** tick adatból ($444K threshold)
3. **Causal pivot merge_asof:** backward a dollar barokra
4. **Feature számítás:** Jules formula (10 feature)
5. **Modell újratanítás:** jún 15 - aug 15 (causalis), OOS: aug 16 - szept 1
6. **Összehasonlítás:** új Jules causal vs Z.ai v1.04 ensemble

Ha WR > 55%: pivot feature-ök értékesek, új kiindulópont
Ha WR < 50%: pivot koncepció nem működik causalis környezetben
```

## progress.md — Hozzáadandó szekció

```
## Jules Pipeline Javítás (2026.09.25.) ⏳
- [x] **Lookahead bias BIZONYÍTVA** — OOS WR=25.7% (véletlen alatt!)
- [x] **Szivárgás forrása azonosítva** — Master_ZigZag_GCEQ26_M1.csv batch export
- [x] **Feature előjel mismatch dokumentálva** — Jules (Micro_R-Close)/ATR vs Z.ai (Close-Micro_R)/ATR
- [x] **Dollar bar + indikátor probléma felismerve** — volume-synchronized vs idő-kompatibilis
- [x] **Causal pivot forrás azonosítva** — Scalper_Copilot_MTF_Data.csv (EA-sent, port 5555)
- [x] **Teljes kontextus dokumentálva** — /data/Brain/_qwen_analysis/JULES_PIPELINE_JAVITAS_KONTEXTUS.md
- [ ] **Causal pivot dataset építés** — Scalper_Copilot_MTF_Data.csv → dollar bar + M1 pivot merge
- [ ] **Jules modell újratanítás** — causalis feature-ökön (jún 15 - aug 15)
- [ ] **OOS validáció** — aug 16 - szept 1 (true blind)
- [ ] **Eredmény értékelés** — WR > 55% vagy < 50%?
```
