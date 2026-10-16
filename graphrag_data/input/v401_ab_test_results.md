# Scalper Copilot v4.01 — A/B Teszt Eredmények
## Dátum: 2026-10-16

## Összehasonlítás: v4.0 vs v4.01 (különböző konfigurációk)

| Konfiguráció | 1min L | 1min S | 2min L | 2min S | 3min L | 3min S | Átlag |
|---|---|---|---|---|---|---|---|
| **v4.0 TBM** (baseline) | 0.555 | 0.535 | 0.548 | 0.547 | 0.550 | 0.544 | **0.547** |
| v4.01 (minden BE) | 0.551 | 0.538 | 0.539 | 0.536 | 0.552 | 0.538 | 0.542 |
| v4.01 (no weights) | 0.534 | 0.545 | 0.540 | 0.539 | 0.544 | 0.538 | 0.540 |
| v4.01 (no weights, no $thr) | 0.534 | 0.545 | 0.540 | 0.539 | 0.544 | 0.538 | 0.540 |

## Meta-labeling AUC (jelek szűrése):

| Konfiguráció | 1min ML | 1min MS | 2min ML | 2min MS | 3min ML | 3min MS |
|---|---|---|---|---|---|---|
| v4.01 (minden BE) | 0.549 | 0.552 | 0.555 | 0.538 | 0.544 | 0.547 |
| v4.01 (no weights) | **0.561** | **0.555** | **0.555** | 0.538 | 0.551 | 0.547 |

## Következtetés:
1. **Sample weights ROSSZABAT** csinált az AUC-n → a dollár-bár sample-k nem time-overlappedak eléggé
2. **Feature interakciók** nem javítottak — a fa alapból non-lineáris
3. **Meta-labeling AUC > 0.55** — a meta model TUD szűrni, de a primary AUC nem javult
4. **Dollar-bar threshold** nem számít (már a signal threshold szűr)
5. **v4.0 baseline a legjobb** eddig!

## Javasolt következő irány:
- Nem a feature engineering a probléma (a fa non-lineáris)
- A CÍMKÉZÉS és az ADAT a szűk keresztmetszet
- Próbáljuk: --full dataset (több adat → stabilabb fa)
- Próbáljuk: meta-labeling GATE a predikciókon (nem csak tanítás)
