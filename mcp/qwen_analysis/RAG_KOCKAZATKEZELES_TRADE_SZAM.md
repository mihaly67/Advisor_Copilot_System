# RAG Kutatás: Kockázatkezelés + Trade Szám Növelés

## Felhasználói kontextus
- **Manuális kereskedő** — a modell copilot, nem robot
- **60 trade/nap** — kevés, több kell (nyitástól zárásig alig van lehetőség)
- **th=0.35**: Win 50.8%, Opposite 49.2%, Profit $3237 — de profit kockázatkezelés nélkül
- **th=0.65**: Win 65.6%, Opposite 34.4% — de csak 273 trade (túl kevés)

## RAG Találatok

### 1. XAUUSD Scalping AI (score: 0.64) — KÖZVETLEN XAUUSD!
- **Aszimmetrikus pozícióméret**: Long 2%, Short 0.02% (100x különbség!)
- **Aszimmetrikus TP/SL**: Long TP=1000pt SL=400pt, Short TP=10pt SL=20pt
- **Long = nagy pozíció, ritkán** | **Short = kis pozíció, gyakran**
- **Win rate**: Short 70%+, Long 60%+
- **Session**: London/NYC (mi is 08:00-23:59 szűrünk)
- **Meta-model**: entry_clf + lstm + transformer + xgb → meta.joblib (ensemble)

### 2. DART Risk Management (score: 0.64)
- **Kelly Criterion**: f* = (p·b - q) / b
  - p = win probability, q = 1-p, b = avg_win/avg_loss
- **Volatility-Adjusted Sizing**: Size = (Account × Risk%) / (ATR × Multiplier)
- **Fractional Kelly** — gyakorlatban 0.5x vagy 0.75x Kelly
- **Drawdown limit**: 15% felett trading csökkentése/leállítás

### 3. Tensortrade "Path to Profitability" (score: 0.48)
- **Reduce frequency** — 10x kevesebb trade
- **Position sizing** binary BSH helyett
- **Confidence threshold** — csak erős szignálnál trade
- **Time-based filtering** — minimum holding period

### 4. Kalshi Edge Filter (score: 0.46)
- **Edge = AI_probability - market_probability**
- **Min edge 8%** (high confidence 6%, low confidence 12%)
- **Min confidence 50%** (eredetileg 65% volt, csökkentették)
- Konkrét implementáció: `EdgeFilter` class

### 5. mlfinlab Meta-Labeling (score: 0.53)
- **Side prediction** → get_bins() → bináris 0/1
- **Secondary model probability** → bet sizing

## Szintézis — Mit tegyünk?

### A. Trade szám növelése (60 → 150+)
**Opció 1: Kisebb dollar bar threshold**
- Jelenleg: $444,000 → ~546 bar/nap
- Ha $222,000 (fele): ~1092 bar/nap → 2x több trade
- Ha $150,000: ~1600 bar/nap → 3x
- **Kockázat**: kisebb bar = több noise, de a modell szűrhet

**Opció 2: th=0.45-0.50 (nem 0.65)**
- th=0.50: 3133 trade, Win 52.6%, Opposite 47.4%
- th=0.45: 5104 trade, Win 51.5%, Opposite 48.5%
- **Kockázatkezeléssel** (lásd lent) ez elfogadható

### B. Kockázatkezelés (profit → valós profit)
1. **Fractional Kelly sizing**:
   - th=0.35: p=0.508, b=2.0/1.0=2.0
   - f* = (0.508×2 - 0.492) / 2 = 0.262 → 26% tőke/trade (túl agresszív)
   - **0.5x Kelly = 13%** (még mindig sok)
   - **0.25x Kelly = 6.5%** — reális

2. **Volatility-adjusted sizing**:
   - Size = (Account × Risk%) / (ATR × Multiplier)
   - Magas ATR = kisebb pozíció, alacsony ATR = nagyobb

3. **Aszimmetrikus sizing (XAUUSD repo minta)**:
   - Ha Long win rate > Short: Long nagyobb pozíció
   - Ha Short win rate > Long: Short nagyobb pozíció
   - th=0.65: Long win=? Short win=65.6% → Short nagyobb pozíció

4. **Confidence-graded sizing**:
   - P(trade) 0.35-0.50: 0.5x alap méret
   - P(trade) 0.50-0.65: 1.0x alap méret
   - P(trade) 0.65+: 1.5x alap méret

### C. Megoldási javaslat

**Kombinált megközelítés:**
1. **Dollar bar threshold csökkentése**: $444K → $222K (2x több bar)
2. **Trade threshold: th=0.45** (nem 0.35, nem 0.65)
3. **Fractional Kelly sizing (0.25x)**: 
   - Alap méret = 1% tőke
   - P(trade) alapján skálázva: 0.5x-1.5x
4. **Drawdown limit**: napi -5% → stop trading aznapra
