# KULCSFELISMERÉS: LightGBM Fa Korlát + Régime Feature Megoldás
*2026-09-23 22:20 — ALAPVETŐ FELISMERÉS*

## A probléma gyökere

### LightGBM = f(x₁, x₂, ..., xₙ) — minden bar FÜGGETLENÜL dönt
- Nincs memória, nincs szekvencia, nincs "tudom hogy 2 éve felfelé megyünk"
- A fa csak lokális mintát lát: "+200 után → Short (korrekció jön)"
- De XAUUSD: +200 → -80 → +150 → -60 → +300 → nettó +410 (uptrend korrekciókkal)
- A fa nem tudja: "ez uptrend korrekciója, nem trendforduló"

### XAUUSD instrumentum-specifikum
- **2 éve folyamatos longban** — elképesztő emelkedési tempó, visszaesésekkel tarkítva
- Átlagban "nincs emelkedés" (fel-le 100-200), DE nettó felfelé
- A fa megtanulja: "+200 → Short" ami ROSSZ mert korrekció után folytatódik uptrend
- **Tréningablak**: 2026-06 (-318) → 2026-07 (+70) → 2026-08 (+384) → 2026-09 (-100)
- **Long/Short label = 1.25** — 25%-kal több Long címke

### Short opposite 47.4% = a fa aktívan rontja a Short-ot
- Mert uptrend-ben Short = ellentétes a kontextussal
- A fa nem látja a kontextust (2 éves uptrend)

## A megoldás: Régime Feature-ök → a fa kondicionál

| Feature | Mit kódol | Fa elágazás |
|---|---|---|
| Close vs EMA_200 | Hosszú trend irány | Ha > 0 → uptrend kontextus |
| ADX | Trend erősség | Ha > 25 → trendelő |
| Z-score (Close vs 100-bar mean) | Hol vagyunk a tartományban | Ha <-1.5 → korrekció uptrend-ben |
| D1/H4 trend slope | Napos trend | Ha pozitív → ne Short-olj |

### Fa döntés így:
"Haz EMA_200 felett ÉS ADX>25 ÉS Z-score<-1 → Long (korrekció uptrend-ben)"
"Haz EMA_200 felett ÉS ADX<20 → sideways → Short is OK"

## Eredmények eddig (V9)
- Accuracy: 40.2%, Long precision: 51%, Short precision: 39%
- Long opposite: 22.8%, Short opposite: 47.4%
- Long-only: 123 trades, 37.4% win → használható
- Short: katasztrófa, regime feature nélkül nem működik

## Amit NEM lehet
- Hosszabb tréningablak — nincs tick tárolás, csak gyertya
- Az arany 2 éve longban → hosszabb ablak is csak Long-ot támogatja
- RL/PPO — túl bonyolult a jelenlegi framework-ben

## Amit LEHET
1. Régime feature-ök (EMA_200, ADX, D1 slope, Z-score) — azonnal
2. Conditional labeling (uptrend-ben korrekció = Long entry)
3. Meta-labeling (stage 1: regime, stage 2: direction)
