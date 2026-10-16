# Meta-Labeling Diagnosztika — A kemény igazság

## 🔴 A meta model NEM tanul — csak kizár

### Sharpe-like összehasonlítás (WR/100 * √N)

| Config | OOS N | OOS WR | OOS SL | VZ N | VZ WR | VZ SL |
|--------|-------|--------|--------|------|-------|-------|
| **CUSUM-only** | **8,084** | 50.2% | **45.16** | **3,825** | 49.7% | **30.75** |
| Meta 0.40 | 7,258 | 50.6% | 43.07 | 3,450 | 49.7% | 29.20 |
| Meta 0.50 | 4,121 | 51.4% | 32.99 | 1,917 | 50.6% | 22.15 |
| Meta 0.55 | 2,004 | 52.4% | 23.48 | 913 | 51.3% | 15.49 |

**A CUSUM-only baseline (SL=45.16) DOMINÁLJA a meta-labelinget (SL=23.48)!**

## Miért?

### 1. A meta model közel-zero diszkriminatív erő
- P(follow) eloszlás: mean=0.499, std=0.075
- **A model 50/50 körül oszcillál ±7.5% szórással**
- Binned actual follow rate alig monotón:
  - P[0.00-0.40): actual=47.3%
  - P[0.55-0.60): actual=52.7%
  - **Ennyi: 5.4% spread a 0→0.6 tartományon** — ez nem előjelző erő

### 2. Feature korreláció a meta-labellel: gyenge
- Price_Velocity: r=-0.027 (p=0.015) — alig szignifikáns
- Bar_Direction: r=-0.023 (p=0.042) — marginális
- **Nav/Regime feature-k: NaN (mindig 0)** — nem elérhetők!

### 3. A "WR javulás" csak survivorship bias
- CUSUM-only: 8,084 trades, 50.2% WR → SL=45.16
- Meta 0.55: 2,004 trades, 52.4% WR → SL=23.48
- A meta kizár 75% trade-et, a maradék 2.2% WR javulás NEM kompenzálja a √N veszteséget

## Gyökérok

1. **A feature-k nem tartalmaznak elég információt** a "follow/skip" döntéshez
   - S/R dist + Bar_Direction + momentum: ezek az IRÁNYT jósolják, nem a BIZONYTALANSÁGOT
   - Ami kéne: bid-ask spread szélesség, volume microstructure, recent WR, regime uncertainty
   
2. **Nav/Regime = 0** — a legerősebb potenciális feature-k hiányoznak
   - DF_Direction, MACD_Direction, Nav_Consensus: mind 0
   - Regime_ADX, Regime_Trending: mind 0

3. **A meta-labeling Prado CH3 feltevése nem teljesül**:
   - Prado: "primary model has side, secondary model learns bet SIZE"
   - Itt: a primary (CUSUM) ~50% WR — alig jobb mint random
   - Ha a primary már gyenge, a secondary nem tud "megtanulni" mit kövessen

## Javaslat

1. **Dobjuk a meta-labelinget** — CUSUM-only a jobb (SL=45 vs 23)
2. **Vagy**: javítsuk a primary model-t (CUSUM direction) — ha az 55%+ WR-re jut, a meta is működik
3. **Kulcs**: Nav/Regime feature-k Python-ból történő számítása (nem mindig 0)
4. **Új feature-k a meta-hoz**: recent WR, avg spread, vol regime, tick intensity
