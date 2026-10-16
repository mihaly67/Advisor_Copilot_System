# OPTUNA V1.10 JULES CFD — VÉGSŐ EREDMÉNYEK

## 4 Konfiguráció Összehasonlítás

| Config | WR | Trades | Long | L_WR | Short | S_WR | Profit |
|--------|-----|--------|------|------|-------|------|--------|
| Original (Jules) | 47.7% | 2,331 | 1,442 | 45.8% | 889 | 51.0% | 451.5 |
| Profit-opt | 47.5% | 11,336 | 5,823 | 47.4% | 5,513 | 47.6% | 2,119.0 |
| WR-opt | **61.0%** | 200 | 47 | 55.3% | 153 | **62.7%** | 105.0 |
| Balanced | **59.3%** | 273 | 123 | 52.8% | 150 | **64.7%** | 132.0 |

## Optuna Best Params

### Profit-optimized (v2, 200 trials)
- THL=0.3547 THS=0.3415 THN=0.5243
- stoch_long_kill=-0.0448 stoch_short_kill=0.1933
- stoch_deadzone=0.2937
- stability_window=0

### WR-optimized (300 trials)
- THL=0.5019 THS=0.4712 THN=0.3098
- stoch_long_kill=-0.2591 stoch_short_kill=0.2858
- stoch_deadzone=0.3699
- stability_window=4

### Balanced (300 trials)
- THL=0.5051 THS=0.4648 THN=0.3290
- stoch_long_kill=-0.2514 stoch_short_kill=0.2732
- stoch_deadzone=0.3845
- stability_window=4

## KULCS FELFEDEZÉSEK

### 1. Short WR > Long WR — CFD Short-bias!
- Balanced: S_WR=64.7% vs L_WR=52.8%
- WR-opt: S_WR=62.7% vs L_WR=55.3%
- A CFD-n a Short irány JOBBAN működik

### 2. Stoch deadzone a legfontosabb paraméter
- 0.29 (profit) → 0.37 (WR) → 0.38 (balanced)
- |Stoch|<deadzone → Stoch filter KIKAPCSOL — nem öl jeleket
- Ez a Jules eredeti pipeline-ban NEM VOLT — hiányzik!

### 3. Aszimmetrikus Stoch kill
- stoch_long_kill ≈ -0.25 (csak erős bearish Stoch öl Long-ot)
- stoch_short_kill ≈ 0.27-0.29 (csak erős bullish Stoch öl Short-ot)
- Jules eredeti: 0.0/0.0 — túl agresszív!

### 4. THL > THS — aszimmetrikus threshold
- WR-opt: THL=0.50 > THS=0.47
- A modellnek kevesebb magabiztos Long jele van
- De a Long jelek is kevésbé pontosak (L_WR < S_WR)

### 5. Stability window=4 a WR-optimalizáltnál
- A magasabb threshold + stability=4 → nagyon szelektív
- Csak 200-273 trade, de WR 59-61%

### 6. KONFÚZIÓS MÁTRIX BUG FIX
- Az eredeti analízis PredShort=0 BUG volt!
- A sig encoding (0=Short,1=Noise,2=Long) != y encoding (-1,0,1)
- A javított mátrix mutatja: VAN Short predikció

## Gyökéroka: CFD Volume Proxy
- Futures: TICK_FLAG_BUY/SELL → Bid≠Ask 66% → irányinformáció
- CFD: tick-count → Bid≈Ask 97.7% → NINCS irányinformáció
- A modell ~47-48% WR-t tud elérni nagy trade számmal
- Magas WR (59-61%) csak nagyon szelektíven, kevés trade-del
