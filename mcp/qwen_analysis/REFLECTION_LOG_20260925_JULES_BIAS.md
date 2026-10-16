# Reflection Log — 2026.09.25. Jules Pipeline Bias Bizonyítás + Javítás

## Task: Jules fusion_v5 lookahead bias bizonyítás és pipeline javítás

### Kihívások
1. **ZigZag state machine batch export lookahead bias** — a CZigZagEngine extreme_search visszamenőleg módosítja a korábbi pivotokat, amikor új pivotot ismer fel. Batch export a teljes történeten → jövőbeli információ szivárog vissza.
2. **Feature előjel mismatch** — Jules (Micro_R - Close)/ATR vs Z.ai (Close - Micro_R)/ATR — ellentétes előjel, ami először zavaró volt, de végül a formula JO, csak a bemeneti adat volt biasos.
3. **Dollar bar + indikátor probléma** — klasszikus indikátorok nem egyértelműen értelmesek dollár baron. Két megközelítés létezik: volume-synchronized (Z.ai, AFML) és idő-kompatibilis (Jules, merge_asof).

### Sikerek
1. **Bias bizonyítva OOS teszttel** — WR 84.5% → 25.7% (véletlen alatt). Anti-correlated pattern = smoking gun.
2. **Szivárgás forrása pontosan azonosítva** — Master_ZigZag_GCEQ26_M1.csv batch export, nem a formula, nem a merge_asof, nem a label.
3. **Causal pivot forrás azonosítva** — Scalper_Copilot_MTF_Data.csv már tartalmazza az EA-sent causal pivotokat! Nem kell új ZigZag engine.
4. **Port architektúra validálva** — 3 port (5555/5556/5557) causalis élesben, a szivárgás csak offline pipeline-ben.
5. **Dollar bar + indikátor architekturális felismerés** — két valid megközelítés, különböző információt kódolnak.

### Tanulságok
1. **Minden állapottartó indikátor batch exportja potenciális lookahead bias** — ZigZag, fractal, renko, swing high/low detektor. Csak shift(1)-es history-független indikátorok biztonságosak.
2. **WR < véletlen = szisztematikus anti-pattern = data leakage** — nem overfit, hanem inverz minták.
3. **Az EA élben küldött adat már causális** — a tanítási pipeline-nek ezt kell használnia, nem a batch exportot.
4. **Volume-synchronized indikátorok (AFML) empirikusan működnek** — Z.ai 54.3% WR dollár bar RSI/Stoch-on. Információ-hatékonyabb aktív piacon.
5. **A Jules pivot koncepció potenciálisan értékes** — ha causalis környezetben betanítjuk, kiderül, mennyit ér. Lehet meglepetés.
