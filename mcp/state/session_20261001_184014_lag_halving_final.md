# Session: lag_halving_final
*Időbélyeg: 2026-10-01T18:40:14.939274*

LAG FELEZÉS TESZT KÉSZ — 2026-10-01

## Derivált EGYÉNI lag: KIVÁLÓ (-8→-1, 88% csökkentés!)
## MODELL P(Long) lag: -8 maradt MINDEN változatnál!

| Modell | Feat | LblWR | FwdL | Profit | P(L)Lag |
|--------|------|-------|------|--------|---------|
| Eredeti | 65 | 61.2% | 48.1% | 10446 | -8 |
| Cserélt | 65 | 58.4% | 48.7% | 9375 | -8 |
| Hibrid | 73 | 61.4% | 48.2% | 10523 | -8 |

GYÖKÉR OK: a LABEL (5perc triple barrier) inherensen lassú!
A modell a lassú feature-ket preferálja mert azok jobban korrelálnak a 5-perces label-lel.

Fájlok:
- /data/dev/projects/z-ai-copilot/src/lag_halving_test.py
- /data/dev/projects/z-ai-copilot/src/lag_audit_v106.py
- /data/dev/projects/z-ai-copilot/models/v106/lag_halving_results.json
- /data/dev/projects/z-ai-copilot/models/v106/lag_audit_results.json