# Lag Analízis Session — Végső Összefoglaló (2026-10-01/02)

## Probléma
A v1.06 modell predikciója 6-8 bar lag-gel követi az árat → a trend közepe helyett elején kellene belépni.

## Amit kipróbáltunk (mindent)

### 1. Lag audit → NEM lookahead, inherens lag=-8
### 2. Feature deriváltak → egyedi lag 88%-kal csökkent, modell lag=-8 marad
### 3. Kétfázisú modell → +$88 nettó, de lag=-8 marad
### 4. 3-periódusú indikátorok → feature lag=-1, modell lag=-8 marad
### 5. Label shift +N → lag csökken, de profit zuhan (trade-off)

## Végső konklúzió
**A lag nem csökkenthető.** 3 fix ok: indikátor simítás + lassú label + PT=1.5$ fix.
Lag = inherens tulajdonság, nem bug.

## Következő session: Kikapcsolás (más megoldás kell!)
