# PT/SL Aszimmetria — A KÍSÉRLET EREDMÉNYEI

## 4 konfiguráció összehasonlítása (VIZSGA)

| PT | SL | Ratio | Long WR | Short WR | Összes WR | Profit | Noise |
|----|-----|-------|---------|----------|-----------|--------|-------|
| **1.5** | **1.0** | **1.5** | **43.8%** ❌ | **55.7%** ✅ | 49.7% | **$930** | 5.6% |
| 1.0 | 1.0 | 1.0 | 48.8% | 50.8% | 49.8% | $-17 | 2.8% |
| **1.0** | **1.5** | **0.7** | **53.8%** ✅ | **45.4%** ❌ | 49.6% | $-992 | 5.5% |
| 1.5 | 1.5 | 1.0 | 48.9% | 50.1% | 49.5% | $-56 | 10.0% |

## 🔴 A FELFEDEZÉS

### PT/SL ratio MEGFORDÍTJA a Long/Short aszimmetriát!

- **PT > SL (1.5/1.0)**: Short WR=55.7%, Long WR=43.8% → **Short dominál**
- **PT < SL (1.0/1.5)**: Long WR=53.8%, Short WR=45.4% → **Long dominál**
- **PT = SL**: Mindkettő ~50% → **nincs dominancia**

### Miért?

A Triple Barrier aszimmetria **nem a CUSUM direction-ból jön — a TB LABELING-ből jön!**

Ha PT=1.5, SL=1.0:
- Bármely irányban: az ár 1.0-ot gyorsabban ér el mint 1.5-öt
- Long signal: ár megy UP → de ha bármikor lemegy -1.0-ot, az SL = SHORT label
- **A TB a közelebbi határt preferálja!**
- Mivel SL közelebb van (1.0 < 1.5), az SL gyakrabban aktiválódik

**Ez egy FUNDAMENTÁLIS TB labeling hiba — nem a CUSUM filter hibája!**

### A profit különbsés is magyarázható:

- PT=1.5/SL=1.0: profit=$930 → **mert amikor nyer, $1.5-öt nyer, amikor veszt, $1.0-ot veszt**
- PT=1.0/SL=1.0: profit=$-17 → szimmetrikus, de WR~50% → várhatóan ~0
- PT=1.0/SL=1.5: profit=$-992 → **mikor nyer $1.0, mikor veszt $1.5**

## ✅ JAVÍTÁS: PT=SL vagy PT/SL < 1

Ha a cél: **Long jeleket is használni**:
- PT=1.0, SL=1.0 → szimmetrikus, Long WR=48.8%
- PT=0.8, SL=1.0 → "könnyű nyerni" → Long WR még jobb?

Ha a cél: **max profit**:
- PT=1.5, SL=1.0 → csak Short trade-elj! (WR=55.7%)
- Vagy: PT=1.5, SL=1.0 de csak Short signal → $746 profit

Ha a cél: **igazságos labeling** (Prado szerint):
- PT=SL → a TB nem preferál semelyik irányt
- De akkor WR≈50% és profit≈0 — **nincs él!**

## 🔑 A VALÓDI PROBLÉMA

**A CUSUM filter + TB labeling kombináció alapvetően korlátozott:**

1. CUSUM event → reversion (mean change ellentétes az event irányával!)
2. TB labeling PT>SL → Short bias
3. TB labeling PT<SL → Long bias
4. PT=SL → semleges, de WR~50% → nincs előny

**A CUSUM event-ek NEM folytatásjelzések — REVERSION jelek!**

- CUSUM UP → az ár már ment UP → következő lépés: DOWN (reversion)
- CUSUM DOWN → az ár már ment DOWN → következő lépés: UP (reversion)

**Ezért működik a Short CUSUM PT>SL-nél:**
- CUSUM DOWN → reversion UP → de PT=1.5 messze van
- Ha az ár menne DOWN (folytatás), eléri -1.0 SL-t → Short profit!
- **A Short CUSUM signal a FOLYTATÁST profitálja, nem a reversiót!**

## KÖVETKEZTETÉS

### Opció A: "Fade the CUSUM" (reversion trade)
- CUSUM UP → SHORT (reversion)
- CUSUM DOWN → LONG (reversion)
- PT=1.0, SL=1.5 (könnyű nyerni a reversion-on)

### Opció B: "Follow the CUSUM" csak Short
- Csak CUSUM DOWN → SHORT
- CUSUM UP → skip
- PT=1.5, SL=1.0

### Opció C: Szimmetrikus TB + ML
- PT=SL (pl. 1.0/1.0)
- CUSUM direction mint feature, NEM mint label
- ML tanulja meg az irányt feature-kből
