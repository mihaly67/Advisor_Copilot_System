# V5 CFD ML — Diagnózis és Új Terv

## 🔴 DIAGNÓZIS: A modell NEM ÉRTI a feature-k jelentését

### A számok
| Metrika | OOS | VIZSGA |
|---------|-----|--------|
| AUC | 0.4973 | 0.4823 |
| Meta WR | 50.6% | 17.9% |
| Fade CUSUM WR | 51.0% | 50.8% |
| Fade+ML WR | 52.9% | 52.7% |
| VIZSGA Short WR | — | **7.1%** |

### Feature importance — szinte EGYENLŐ (8-11%)
Ez azt jelenti: **egyetlen feature sem domináns** → egyik sem informatív a meta-label-re nézve.

### Mi a baj? (3 fundamentális probléma)

---

## PROBLÉMA 1: CÍMKE (Label) — Véletlenszerű

**Triple Barrier PT=SL=2×ATR, MAX_BARS=15**
- XAUUSD dollár bar ATR14 medián = $2.50
- Barrier = 2 × $2.50 = $5.00
- MAX_BARS = 15 bar → ~15 perc lookahead

**Probléma**: Szimmetrikus barrier + rövid lookahead = **~50/50 Long/Short label**
- Random walk-ban az ár ~50% eséllyel megy fel 2×ATR, mielőtt lemegy 2×ATR
- A CUSUM event időpontban a label lényegében VÉLETLENSZERŰ
- Ha a label random → a modell is random lesz (AUC ≈ 0.50)

**Megoldás**:
1. **Aszimmetrikus barrier a signal irányához**:
   - Fade Long (CUSUM DOWN): PT=1.5×ATR, SL=3.0×ATR (kisebb PT, nagyobb SL = reálisabb)
   - Fade Short (CUSUM UP): PT=1.5×ATR, SL=3.0×ATR
2. **Hosszabb lookahead**: MAX_BARS=30 (több idő a barrier elérésére)
3. **VAGY**: Return-based label = jövő N bar return előjele (egyszerűbb, kevesebb hiba)

---

## PROBLÉMA 2: FEATURE-K — NEM ÉRTI A JELENTÉSÜKET

A fa **split**-eket keres. Ha `Dist_Micro_S = 1.5`, a fa keres egy threshold-ot (pl. 1.2),
DE nem érti hogy:
- `Dist_Micro_S > 0` = ár a support FELETT = **bullish kontextus**
- `Dist_Micro_S < 0` = ár a support ALATT = **bearish kontextus** (support broken)

### Mit csinálnak a profik? (AlphaPy, freqtrade)

**AlphaPy** explicit **boolean feature-ket** használ:
- `abovema(f, c, p)` — True/False: ár az MA felett?
- `belowma(f, c, p)` — True/False: ár az MA alatt?
- `higher(f, c, o)` — True/False: magasabb mint előző?
- `lower(f, c, o)` — True/False: alacsonyabb mint előző?

Ezek **kategória feature-k** — a fa ONE split-tel szétválasztja a két csoportot!

**freqtrade FreqAI**:
- `sample_weight` temporal weighting (Prado uniqueness)
- RSI, EMA, SMA **több timeframe-en** (expand_all)
- **Nem** normalizál LightGBM-hez (csak .to_numpy())

**LightGBM-Quant-Model (Two Sigma Kaggle)**:
- **StandardScaler**-t használ feature-ken (outlier kezelés)
- Market residual returns (risk-adjusted)
- **Confidence scoring** (P(up) - P(down))

### Konkrét javaslat — Boolean/Categorical feature-k

Ahelyett hogy `Dist_Micro_S = 1.5` (continuous), adjunk hozzá:

| Új Feature | Definíció | Jelentés |
|------------|-----------|----------|
| `Above_Support` | Dist_Micro_S > 0 | Ár a support felett = bullish |
| `Near_Support` | 0 < Dist_Micro_S < 0.5 | Ár közel a support-höz = bounce setup |
| `Below_Resistance` | Dist_Micro_R > 0 | Resistance az ár felett = bearish cap |
| `Near_Resistance` | 0 < Dist_Micro_R < 0.5 | Ár közel a resistance-hez = reject setup |
| `RSI_Oversold` | Micro_RSI_14 < 30 | Oversold = Long setup |
| `RSI_Overbought` | Micro_RSI_14 > 70 | Overbought = Short setup |
| `Bullish_Bar` | Bar_Direction > 0 | Bullish candle |
| `Bearish_Bar` | Bar_Direction < 0 | Bearish candle |
| `CUSUM_Up` | CUSUM_Direction > 0 | Felfelé momentum |
| `CUSUM_Down` | CUSUM_Direction < 0 | Lefelé momentum |
| `Trend_Up` | Trend_EMA_Fast_Dist > 0 | Ár az EMA felett |
| `Trend_Down` | Trend_EMA_Fast_Dist < 0 | Ár az EMA alatt |

### Kontextus-kombinációk (AMIK A FA NEM TUD JÓ KOMBINÁCIÓT KERESNI)

| Új Feature | Definíció | Jelentés |
|------------|-----------|----------|
| `Fade_Short_Setup` | CUSUM_Up & RSI_Overbought | Fade UP + overbought = Short |
| `Bounce_Long_Setup` | CUSUM_Down & RSI_Oversold | Fade DOWN + oversold = Long |
| `Trend_Resume_Long` | Trend_Up & Bullish_Bar & Above_Support | Trend folytatódik fel |
| `Trend_Resume_Short` | Trend_Down & Bearish_Bar & Below_Resistance | Trend folytatódik le |
| `Breakdown` | ~Above_Support & CUSUM_Down | Support broken + momentum le |
| `Breakout` | ~Below_Resistance & CUSUM_Up | Resistance broken + momentum fel |

**Ezek a feature-k mondják meg a fának: MI a helyzet!**

---

## PROBLÉMA 3: NORMALIZÁCIÓ — Nem a fő baj, de segít

### Fa alapú modellek és normalizáció

**Tény**: LightGBM **NEM** igényel normalizációt (StandardScaler, MinMaxScaler)
- Histogram-based algorithm → binning → a skálázás nem változtatja meg a split-eket
- Monoton transzformáció (x→2x, x→x+5) nem változtatja meg a fa struktúrát

**DE**: 
1. **Outlier kezelés**: Extrém értékek → extrém bin-ek → pazarolt split-ek
   - Megoldás: **winsorize** (clip extreme values) vagy StandardScaler
2. **Boolean feature-k**: 0/1 értékek → tökéletes bin → 1 split = tiszta szétválasztás
3. **LightGBM categorical support**: `categorical_feature` paraméter → optimális kategória split

### Konklúzió: Normalizáció nem kötelező, de:
- **Boolean/categorical feature-k NAGYON segítik** a fát
- **Continuous feature-k megtartása** (ATR-normalizáltak már)
- **Outlier clipping** javasolt (±5 szórás)

---

## 🟢 ÚJ TERV

### Phase 1: Diagnosztika (15 perc)
1. Feature-label korreláció mátrix (Pearson + Spearman)
2. Label eloszlás vizualizáció
3. Feature eloszlás + outlier detektálás
4. **Ha egyetlen feature sem korrelál a label-lel >0.05 → a rendszer fundamentálisan rossz**

### Phase 2: Feature Engineering — Jelentés definiálása (30 perc)
1. Boolean/categorical feature-k hozzáadása (fenti táblázat)
2. Kontextus-kombinációk hozzáadása
3. Continuous feature-k megtartása (ATR-normalizáltak)
4. LightGBM `categorical_feature` paraméter használata

### Phase 3: Címke javítás (20 perc)
1. **2 opció**:
   - Opció A: **Aszimmetrikus TB** — PT=1.5×ATR, SL=3.0×ATR a signal irányához
   - Opció B: **Return label** — jövő N bar return előjele (egyszerűbb, kevesebb hiba)
2. **Hosszabb lookahead**: MAX_BARS=30
3. **Sample weighting**: Prado uniqueness vagy return magnitude

### Phase 4: 2 Külön modell + Optuna (45 perc)
1. **Long modell**: CUSUM DOWN event-ek, label=1 ha Long PT hit
2. **Short modell**: CUSUM UP event-ek, label=1 ha Short PT hit
3. **Ha mindkettő AUC≈0.50** → fundamentális probléma, nincs mit tenni
4. Optuna hyperopt: n_estimators, learning_rate, num_leaves, max_depth, min_child_samples

### Phase 5: Érvényesítés (15 perc)
1. OOS AUC > 0.55? Ha nem → feature-k nem prediktívak
2. VIZSGA WR > 53%? Ha nem → overfit vagy nem informatív
3. Long és Short WR szimmetrikus? Ha nem → bias
4. Feature importance: kontextus feature-k dominálnak?

### Összesen: ~2 óra

---

## HOGYAN KELL GONDOLKODNI RÓLA

**A fa nem "érti" a feature-ket — csak split-eket keres.**

De ha a feature-k úgy vannak KONSTRUÁLVA, hogy a split-ek **jelentéssel bírnak**, akkor a fa "megtanulja" a jelentést:

```
if Above_Support == True AND CUSUM_Down == True AND RSI_Oversold == True:
    → Bounce_Long_Setup = True → 80% Long WR
```

Ezt a 3 split-et a fa MEGTALÁLJA — de csak ha a feature-k BENNE VANNAK!
Ha csak `Dist_Micro_S = 1.5` van, a fa sokkal nehezebben találja meg a kombinációt.

**A feature engineering LÉNYEGE**: Olyan feature-ket készíteni, amikben a **split-ek jelentéssel bírnak**.
