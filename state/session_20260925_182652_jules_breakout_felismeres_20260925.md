# Session: jules_breakout_felismeres_20260925
*Időbélyeg: 2026-09-25T18:26:52.106589*

# Jules V5 Breakout Detector Felismerés (2026.09.25.)

## ALAPVETŐ FELISMERÉS

Jules V5 modellje NEM irány-prediktor, hanem REZSIM/KITÖRÉS-prediktor!

### Bizonyítékok (inertia analízis):
- cor_max=0.66, opp_max=0.65 → mindkét irány egyszerre magas
- pct_opp=88.6% → a trend 88.6%-ában ellentétes irányú pred. is >0.20
- P_Long és P_Short majdnem egyenlőek amikor ár közel van pivot szinthez
- A 10 feature NEM hordoz irányinformációt (Dist_* = távolság, nem irány)

### Mit csinált Jules véletlenül:
- Megépített egy KITÖRÉS-DETEKTORT (mikor kereskedjek)
- Nem irány-prediktort (merre kereskedjek)
- Hard Stochastic filter = kétségbeesett próbálkozás, hogy irányt erőszakoljon
- A filter 46.4%-ot blokkol, WR nem javul, profitot felezi

### Két kérdés, két modell:
| Kérdés | Jules V5 | Z.ai NavSystem |
|---|---|---|
| MIKOR kereskedjek? | ✅ (pivot közel = kitörés) | ❌ |
| MERRE kereskedjek? | ❌ (mindkét irány magas) | ✅ (NavSystem irány) |

### Fejlesztési irány: Dual-Model Meta-Labeling
- Primary (irány): Z.ai NavSystem → Long/Short
- Secondary (szűrő): Jules V5 → trade/pass (P(breakout) = P_Long + P_Short > th)
- = Prado meta-labeling modell szinten
- Optuna: th_break, th_dir, w_jules, w_nav kalibráció

### FONTOS: Lépésenként haladni, nem rohanni!
1. Alapos vizsgálat (MIKOR jó a Jules, mikor nem, milyen árfolyam mintáknál)
2. P(breakout) statisztika (P_Long + P_Short eloszlás)
3. Kombináció tervezése
4. Implementáció
5. Validáció