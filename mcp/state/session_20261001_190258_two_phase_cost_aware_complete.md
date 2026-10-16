# Session: two_phase_cost_aware_complete
*Időbélyeg: 2026-10-01T19:02:58.542640*

KÉTFÁZISÚ MODELL + KÖLTSÉGTUDATOS ELEMZÉS KÉSZ — 2026-10-01

## VÉGSŐ EREDMÉNYEK

### Költségtudatos profit (cost_per_trade = $0.80):
| Modell | N | WR | LblProfit | Költség | NetP |
|---|---|---|---|---|---|
| v106 baseline | 12570 | 61.0% | 10446 | 10056 | $390 |
| S1×S2 kétfázisú | 11691 | 61.4% | 9831 | 9353 | $478 |

**NETTO: +$88 jobb a kétfázisú!**

### Költségszenzitivitás:
- cost<$0.70: v106 jobb (kevés a költség)
- cost=$0.80: kétfázisú +$88 jobb ✅
- cost>$0.90: kétfázisú egyre jobb (+$176, +$264...)
- **Minél nagyobb a költség, annál értékesebb a trade szűrés!**

### FELFEDEZÉS: A lag=-8 NEM BAJ!
1. PT=1.5$ miatt a trade 5-15 perc → trend kitart
2. Lassú feature-ök STABIL irányt adnak → lag nem veszély  
3. Vánszorgó trend: lag kiszűri veszélyes mikrotrendeket
4. Markáns trend: 8 bar késés sembaj → trend 30+ barig tart

### Deriváltak szerepe: TIMING, nem irány
- Slope_Close_14_Vel: lag=-1 (88% csökkentés!)
- Nem irányt mondanak, hanem "most jó a belépés?"
- S1=irány (lassú) × S2=timing (derivált) → szebbített belépés

### Fájlok:
- /data/dev/projects/z-ai-copilot/src/two_phase_model.py
- /data/dev/projects/z-ai-copilot/src/cost_aware_analysis.py
- /data/dev/projects/z-ai-copilot/src/lag_audit_v106.py
- /data/dev/projects/z-ai-copilot/src/lag_halving_test.py
- /data/dev/projects/z-ai-copilot/models/v106/two_phase_results.json