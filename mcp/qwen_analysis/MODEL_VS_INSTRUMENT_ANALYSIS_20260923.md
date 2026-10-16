# Modell struktúra vs Instrumentum specifikus probléma?
*2026-09-23 22:00 — Analízis*

## A kérdés: Modell struktúra vagy XAUUSD-specifikus?

### Válasz: **MINDKETTŐ, de elsősorban instrumentum-specifikus**

---

## 1. XAUUSD Instrumentum-specifikus tényezők

### Arany strukturális aszimmetria
- **Long bias**: Gold safe haven + inflációs hedge → strukturális felárrés
- **Short esélyek eseményvezéreltek**: USD erősödés, risk-on, Fed hawkish surprise
- **"Arany liften megy le, lépcsőn megy fel"** — sharp drops, slow rises
- Short entry-k **nem microstructure-vezéreltek**, hanem **macro/regime-vezéreltek**

### CFD korlátozások
- **Nincs DOM/order book** — a microstructure proxy-k gyengék
- **Nincs valódi volume** — Num_Ticks proxy, nem valódi turnover
- **Dollar bar $444k** — aszimmetrikusan aggregál (éles esés = több tick/bar = más bar-struktúra)

### Számok amik bizonyítják:
| Metrika | Long | Short |
|---|---|---|
| Precision (V9) | 51% | 39% |
| Opposite rate (asymmetric Optuna) | 22.8% | 47.4% |
| Cohen d (legjobb feature) | -0.058 | +0.058 |

A Short opposite 47.4% = **rosszabb mint véletlenszerű** (33% lenne 3 osztályú random)

---

## 2. Modell struktúra problémák

### Symmetric model, asymmetric instrument
- **1 modell** szolgálja ki Long és Short irányt is
- Ugyanazok a feature-ök mindkét irányhoz
- De XAUUSD-nál Long és Short **fundamentálisan különböző generátorokkal** rendelkezik

### Cohen d < 0.08 minden feature-re
- Ez NEM modell probléma — ez **adat probléma**
- A feature-ök nem diszkriminálnak Long vs Short entry-k között
- **A címkék maguk zajosak** — PT/SL labeling 1-8 bar horizonton túl rövid

### Nincs memória/temporal structure
- Rolling window feature-ök — nincs LSTM/Transformer
- Nincs regime detection — minden market állapotban ugyanazt predikálja

---

## 3. Bizonyítékok más instrumentumokból

Ha instrumentum-specifikus, akkor **EURUSD-nél szimmetrikusabb** kellene legyen:
- EURUSD: nincs safe-haven bias, Long/Short szimmetrikusabb
- EURUSD microstructure: Kyle lambda, VPIN szimmetrikusabban diszkriminál
- **Hipotézis**: EURUSD-nél a Short opposite rate << 47%

---

## 4. Konklúzió

| Tényező | Súly | Megoldás |
|---|---|---|
| **XAUUSD Long bias** | 60% | Long-only stratégia VAGY separate models |
| **CFD nincs DOM** | 20% | VPIN/Kyle proxy-k finomítása |
| **Symmetric model** | 15% | Asymmetric model / meta-labeling |
| **Labeling zaj** | 5% | Nagyobb PT/SL vagy meta-labeling |

### Ajánlott megoldások (prioritás sorrendben):

1. **Long-only stratégia** — azonnali, XAUUSD-nál racionális
   - th_long=0.62, th_noise_long=0.20
   - 123 trades, 37.4% win, 22.8% opposite → használható

2. **Két külön modell** — Long model + Short model
   - Long: jelenlegi feature-ök + microstructure
   - Short: **regime feature-ök** (DXY, VIX, yield curve) + event detection
   - Short csak risk-on / USD-bull regimében

3. **Meta-labeling** (de Prado AFML Ch.3)
   - Stage 1: Event detection (van-e lehetőség?)
   - Stage 2: Direction prediction (Long vagy Short?)
   - A direction model csak event-ekre tanul → kevesebb zaj

4. **Instrumentum validáció** — EURUSD pipeline futtatása
   - Ha EURUSD-nél is rossz Short → modell struktúra probléma
   - Ha EURUSD-nél szimmetrikus → instrumentum-specifikus
