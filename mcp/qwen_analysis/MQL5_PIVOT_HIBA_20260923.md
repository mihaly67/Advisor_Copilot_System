# MQL5 Pivot Hiba Diagnózis — Gyökérok
*2026-09-23*

## Forráskód: Scalper_Copilot_Miner_v1.mq5 (sor 83-93, 221-224)

### CalcSR függvény (sor 83-93)
```mql5
void CalcSR(MqlRates &rates[], int count, int idx, int lookback, double &resistance, double &support)
{
   int start = (int)MathMax(0, idx - lookback);
   resistance = rates[start].high;
   support = rates[start].low;
   for(int j = start + 1; j <= idx; j++)
   {
      if(rates[j].high > resistance) resistance = rates[j].high;
      if(rates[j].low < support) support = rates[j].low;
   }
}
```

### Hívás (sor 221-224)
```mql5
CalcSR(rates_1m,  copied_1m,  idx_1m,  15, micro_r, micro_s);  // 15 × M1  = 15 min
CalcSR(rates_15m, copied_15m, idx_15m, 5,  sec_r, sec_s);      //  5 × M15 = 75 min
CalcSR(rates_30m, copied_30m, idx_30m, 3,  ter_r, ter_s);      //  3 × M30 = 90 min
```

## 3 HIBA

### 1. Nem ZigZag pivotok — hanem rolling High/Low
A "Micro_R/Sec_R/Ter_R" nevek pivotot sugallnak, de valójában egyszerű
rolling High/Low-ok. Ezek NEM strukturális pivot szintek (nem ZigZag alapúak).

### 2. Sec és Ter lookback ablakok túl hasonlóak
- Sec: 75 min (5 × M15)
- Ter: 90 min (3 × M30)
- Különbség: csak 15 min!
- Eredmény: r=0.994 → gyakorlatilag duplikátum

### 3. Pulse_DF_Curve nem ATR-normalizált
```python
df['Pulse_DF_Curve'] = (pulse_macd.macd() - bb.bollinger_mavg()).shift(1)
```
Ez abszolút árszintet hordoz → r=-0.999 minden árszinttel (Close, Micro_R, Sec_S).

## MQL5 javítás
```mql5
// Ter lookback növelése: 3 → 10 (300 min = 5h)
CalcSR(rates_30m, copied_30m, idx_30m, 10, ter_r, ter_s);

// VAGY: más timeframe használata
CalcSR(rates_30m, copied_30m, idx_30m, 6, ter_r, ter_s);  // 180 min = 3h
```

## Python javítás (feature engineer)
```python
# Pulse_DF_Curve normalizálás ATR-rel
df['Pulse_DF_Curve'] = ((pulse_macd.macd() - bb.bollinger_mavg()) / atr_m15).replace([np.inf, -np.inf], 0).fillna(0).shift(1)
```
