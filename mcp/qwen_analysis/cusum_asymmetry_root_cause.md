# CUSUM Long vs Short aszimmetria — GYÖKÉROKOK

## 🔴 OK #1: TRIPLE BARRIER PT/SL ASZIMMETRIA

**PT=1.5, SL=1.0 → PT/SL = 1.5**

Ez a legfőbb ok. A TB labeling aszimmetrikus:

- **SL közelebb van (1.0) mint PT (1.5)**
- Bármely irányú event-nél: könnyebb elérni -SL (=1.0) mint +PT (=1.5)
- **Ez biasolja a TB label-eket SHORT-ra!**

Számok:
- Long event-ek: **PT_reached=8,802** vs **SL_reached=11,390** (56% SL!)
- Short event-ek: **PT_reached=9,054** vs **SL_reached=11,171** (55% SL!)

**A TB 56%-ban SL-et ér el Long event-eknél!** Még ha CUSUM UP jelet ad,
az ár 56%-ban eléri -1.0-ot mielőtt +1.5-öt → a label SHORT lesz!

Ez magyarázza:
- CUSUM Long WR=43.6% — a Long jelek 56%-a SL-et ér el
- CUSUM Short WR=55.2% — a Short jelek is sok SL-t érnek, de a PT/SL aszimmetria a Short javára dolgozik

## 🔴 OK #2: CUSUM EVENT UTÁNI CONTINUATION HIÁNYZIK

Long event utáni 1 bar price change:
- **mean = -0.0069** (NEGATÍV! Az UP event utáni bar átlagban LEFELE megy!)
- positive=10,499 vs negative=10,797 — alig több a negatív

Short event utáni 1 bar price change:
- **mean = +0.0076** (POZITÍV! A DOWN event utáni bar átlagban FELFELE megy!)
- positive=10,799 vs negative=10,536

**Ez reversion!** CUSUM UP event → next bar DOWN. CUSUM DOWN event → next bar UP.

## 🔍 Bar_Direction a CUSUM event-nél

Long event-nél: **mean_BD=-0.011** (negatív! a bar ami triggereli az UP event-et, átlagban bearish!)
Short event-nél: **mean_BD=+0.004** (pozitív! a bar ami triggereli a DOWN event-et, átlagban bullish!)

**Ez teljesen logikus:** a CUSUM s_pos akkor nő ha az ár FELFELE megy,
de mire triggereli az event-et, a move már megtörtént → reversion!

## JAVÍTÁS

### 1. PT = SL (szimmetrikus TB)
Ha PT=SL=1.0 vagy PT=SL=1.5, akkor a TB nem biasol.
Próbáljuk: PT=1.0, SL=1.0

### 2. PT < SL (conservative)
Ha PT=1.0, SL=1.5 — "könnyű nyerni, nehéz veszíteni"
De ez kevesebb trade-et ad.

### 3. CUSUM threshold aszimmetrikus
Külön h_up és h_down — ha a Short jobb, lehet h_up > h_down
(szigorúbb Long event-ek, lazább Short event-ek)

### 4. Várj N bar-ot CUSUM event után
Ha reversion van, ne trade-elj azonnal — várj 1-2 bar-ot.
De ez ellentmond a CUSUM filozófiájának (event-driven).

### 5. Fordítsd meg a CUSUM Long jelet
Ha CUSUM UP → reversion → SHORT!
Ha CUSUM DOWN → reversion → LONG!
Ez a "fade the CUSUM" stratégia.
