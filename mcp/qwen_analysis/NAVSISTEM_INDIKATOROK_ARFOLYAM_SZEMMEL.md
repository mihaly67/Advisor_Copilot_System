# NavSystem Indikátorok — ÁRFOLYAM SZEMMEL (LGBM fordítás)

## 1. Jules_Hybrid_Momentum_Pulse_v1.05

### Két kimenet:

#### A) MACD_Hist (hisztogram, nulla = semleges)
```
raw_macd = EMA(3) - EMA(6)
final = raw_macd * 4.0 / 7.0
```

**MIT MUTAT AZ ÁRFOLYAM SZEMMEL:**
| Érték | Árfolyam jelentés |
|---|---|
| **> 0 és NÖVEKSZIK** | Árfolyam EMELKEDIK, bullish momentum erősödik |
| **> 0 és MEGTORPAN** | Árfolyam emelkedése LASSUL, trend kifullad |
| **> 0 és CSÖKKEN** | Árfolyam emelkedése MEGÁLL, közelít a nullához |
| **= 0** | Árfolyam NEM MOZOG (vagy EMA(3)=EMA(6)) |
| **< 0 és CSÖKKEN** | Árfolyam CSÖKKEN, bearish momentum erősödik |
| **< 0 és MEGTORPAN** | Árfolyam csökkenése LASSUL, trend kifullad |
| **< 0 és NÖVEKSZIK** | Árfolyam csökkenése MEGÁLL, közelít a nullához |

**Nulla = választóvonal:** Felette = Long tartomány, alatta = Short tartomány.
**A nulla ELÉRÉSE irányból = trend vége.**

#### B) DeltaForce (görbe, nulla = semleges)
```
diff = (close[i] - close[i-1]) / Point()
if diff > 0: bull_power += diff; bear_power = 0
if diff < 0: bear_power += diff; bull_power = 0
df = (bull_power + bear_power) * scale / 7.0
```

**MIT MUTAT AZ ÁRFOLYAM SZEMMEL:**
| Érték | Árfolyam jelentés |
|---|---|
| **> 0 és NÖVEKSZIK** | Árfolyam EMELKEDIK, felhalmozódik a bullish nyomás |
| **> 0 és STABIL** | Árfolyam emelkedett, de MEGÁLLT (torpanás) |
| **> 0 és CSÖKKEN → 0** | Árfolyam TORPAN, közelít a fordulóponthoz |
| **= 0** | Fordulópont! Árfolyam irányváltás |
| **< 0 és CSÖKKEN** | Árfolyam CSÖKKEN, felhalmozódik a bearish nyomás |
| **< 0 és STABIL** | Árfolyam csökkent, de MEGÁLLT (torpanás) |
| **< 0 és NÖVEKSZIK → 0** | Árfolyam TORPAN, közelít a fordulóponthoz |

**KULCS:** DeltaForce > 0 = LONG tartomány (amíg fenn van, addig Long).
DeltaForce < 0 = SHORT tartomány (amíg lenn van, addig Short).
**Nulla átlépése = irányváltás!**
Növekedés = gyorsulás. Megtorpanás = lassulás. Csökkenés = árfolyam is visszafele.

---

## 2. HybridFlowIndicator_v1.126

### Három kimenet:

#### A) MFI (vonal, [0-100], 50 = semleges)
```
raw_mfi = iMFI(period=3)  // standard MFI
hybrid_mfi = raw_mfi + offset_curve  // Delta korrekcióval
```

**MIT MUTAT AZ ÁRFOLYAM SZEMMEL:**
| Érték | Árfolyam jelentés |
|---|---|
| **> 80** | Erős VÉTELI nyomás — pénz BEÁRAMLIK, árfolyam felé mozog |
| **50-80** | Mérsékelt vételi nyomás — árfolyam enyhén emelkedik |
| **≈ 50** | SEMLEGES — nincs netto pénzáramlás irány |
| **20-50** | Mérsékelt eladási nyomás — árfolyam enyhén csökken |
| **< 20** | Erős ELADÁSI nyomás — pénz KIÁRAMLIK, árfolyam lefelé mozog |

**50 = választóvonal:** Felette = pénz beáramlik (Long tartomány), alatta = pénz kiáramlik (Short tartomány).

#### B) Delta (hisztogram, 50 = semleges, [0-100] skálán)
```
pos = (close - low) / (high - low)  // bar pozíció: 0=alja, 1=teteje
power = (pos - 0.5) * 2.0           // [-1, +1]: negatív=alsó félgömb, pozitív=felső
delta = tick_volume * power          // volumen * irány
smooth_delta = SMA(delta, 3)        // simítás
offset = smooth_delta / max_vol * 50.0  // normalizálás, 50 körüli közép
DeltaEnd = 50.0 + offset * visual_gain
```

**MIT MUTAT AZ ÁRFOLYAM SZEMMEL:**
| Érték | Árfolyam jelentés |
|---|---|
| **>> 50 (nagy pozitív)** | Erős vételi volumen a bar FELSŐ felében — árfolyam NYOMAKODIK FEL |
| **> 50 (kis pozitív)** | Mérsékelt vételi volumen — árfolyam enyhén felé |
| **= 50** | SEMLEGES — eladási és vételi volumen kiegyenlített |
| **< 50 (kis negatív)** | Mérsékelt eladási volumen — árfolyam enyhén lefelé |
| **<< 50 (nagy negatív)** | Erős eladási volumen a bar ALSÓ felében — árfolyam NYOMAKODIK LE |

**50 = választóvonal:** Felette = vételi dominancia (Long tartomány), alatta = eladási dominancia (Short tartomány).

#### C) VROC (DRAW_NONE, EA-nak, volumene változás)
```
vroc = (tick_volume[i] - tick_volume[i-period]) / tick_volume[i-period] * 100
```

**MIT MUTAT AZ ÁRFOLYAM SZEMMEL:**
| Érték | Árfolyam jelentés |
|---|---|
| **>> 0 (nagy pozitív)** | Volumen NAGYON megnőtt — aktivitás robbanás (breakout közeledik?) |
| **> 0** | Volumen növekszik — aktivitás nő |
| **= 0** | Volumen változatlan |
| **< 0** | Volumen csökken — aktivitás hanyatló (trend kifullad?) |

---

## 3. Hybrid_Momentum_WPR_Stoch_v1_04

### Két kimenet:

#### A) Stoch %K (hisztogram, 50 = semleges, [0-100])
```
K = SMA(close-low, slowing) / SMA(high-low, slowing) * 100
Base = 50 (hisztogram bázis)
Szín: >= 50 = zöld (bullish), < 50 = piros (bearish)
```

**MIT MUTAT AZ ÁRFOLYAM SZEMMEL:**
| Érték | Árfolyam jelentés |
|---|---|
| **> 80** | Árfolyam a range TETEJÉN van — overbought, várható visszahúzás |
| **50-80** | Árfolyam a range FELSŐ felében — bullish tartomány |
| **= 50** | Árfolyam a range KÖZEPÉN — semleges |
| **20-50** | Árfolyam a range ALSÓ felében — bearish tartomány |
| **< 20** | Árfolyam a range ALJÁN van — oversold, várható pattanás |

**50 = választóvonal:** Felette = Long tartomány, alatta = Short tartomány.
**> 80 = overbought figyelmeztetés** (árfolyam túl magas a range-hez képest).
**< 20 = oversold figyelmeztetés** (árfolyam túl alacsony a range-hez képest).

#### B) WPR (vonal, [0-100] skálán, eredeti [-100,0] + 100 eltolás)
```
wpr = -100 * (MaxHigh - Close) / (MaxHigh - MinLow)
WPR_display = wpr + 100  // [0, 100] skálán
```

**MIT MUTAT AZ ÁRFOLYAM SZEMMEL:**
| Érték | Árfolyam jelentés |
|---|---|
| **> 80** | Árfolyam a periódus HIGH-jához KÖZEL van — overbought |
| **50-80** | Árfolyam a range FELSŐ felében — bullish |
| **= 50** | Árfolyam a range KÖZEPÉN — semleges |
| **20-50** | Árfolyam a range ALSÓ felében — bearish |
| **< 20** | Árfolyam a periódus LOW-jához KÖZEL van — oversold |

**50 = választóvonal** (ugyanaz mint a Stoch-nál).
**> 80 = overbought**, **< 20 = oversold**.

---

## ÖSSZEFOGLALÓ: VÁLASZTÓ ÉRTÉKEK

| Indikátor | Választó (semleges) | Long tartomány | Short tartomány | Overbought | Oversold |
|---|---|---|---|---|---|
| **DeltaForce** | **0** | > 0 | < 0 | — | — |
| **MACD_Hist** | **0** | > 0 | < 0 | — | — |
| **MFI** | **50** | > 50 | < 50 | > 80 | < 20 |
| **Delta** | **50** | > 50 | < 50 | — | — |
| **VROC** | **0** | > 0 (aktív) | < 0 (halk) | — | — |
| **Stoch K** | **50** | > 50 | < 50 | > 80 | < 20 |
| **WPR** | **50** | > 50 | < 50 | > 80 | < 20 |

---

## LGBM FORDÍTÁS — Hogyan értse meg a modell

### 1. Normalizálás a választóhoz (zero-centering)

A LGBM-nek nem a nyers érték kell, hanem az **eltérés a választótól**:

```python
# DeltaForce: zero = 0
df_norm = DeltaForce  # már 0 körüli

# MACD_Hist: zero = 0  
macd_norm = MACD_Hist  # már 0 körüli

# MFI: zero = 50
mfi_norm = MFI - 50.0  # pozitív = Long, negatív = Short

# Delta: zero = 50
delta_norm = Delta - 50.0  # pozitív = vételi nyomás, negatív = eladási

# Stoch K: zero = 50
stoch_norm = Stoch_K - 50.0  # pozitív = bullish, negatív = bearish

# WPR: zero = 50 (0-100 skálán)
wpr_norm = WPR - 50.0  # pozitív = bullish, negatív = bearish
```

### 2. Irány + Intenzitás feature-ök

```python
# DeltaForce irány: +1 = Long tartomány, -1 = Short tartomány
df_direction = np.sign(DeltaForce)

# DeltaForce intenzitás: messze a nullától = erős trend
df_intensity = np.abs(DeltaForce)

# DeltaForce gyorsulás: növekszik = erősödő, csökken = gyengülő
df_acceleration = DeltaForce - DeltaForce_prev

# Ugyanez MFI-re, Stoch-ra, WPR-re:
mfi_direction = np.sign(MFI - 50)    # +1 = pénz beáramlik
stoch_direction = np.sign(Stoch_K - 50)  # +1 = bullish range
wpr_direction = np.sign(WPR - 50)    # +1 = felső félgömb
```

### 3. Overbought/Oversold események (threshold crossing)

```python
# Oversold → Long signal
rsi_oversold = (RSI < 30).astype(int)      # 55.4% WR
wpr_oversold = (WPR < 20).astype(int)      # 53.0% WR (0-100 skálán)
stoch_oversold = (Stoch_K < 20).astype(int)

# Overbought → Short signal  
rsi_overbought = (RSI > 70).astype(int)    # 51.7% WR
wpr_overbought = (WPR > 80).astype(int)
stoch_overbought = (Stoch_K > 80).astype(int)

# MFI extrém
mfi_strong_buy = (MFI > 80).astype(int)    # erős vételi nyomás
mfi_strong_sell = (MFI < 20).astype(int)   # erős eladási nyomás
```

### 4. Volumen aktivitás

```python
# VROC > 0 = aktivitás nő → breakout közeledik
vroc_active = np.sign(VROC)  # +1 = volumen nő, -1 = volumen csökken

# VROC + DeltaForce egybeesés → erősítés
vol_confirms_trend = (np.sign(DeltaForce) == np.sign(VROC)).astype(int)
```

### 5. KONSZENZUS — minden indikátor egy irányba mutat

```python
# Hány indikátor mutat Long-ot?
n_long = (df_direction > 0) + (mfi_direction > 0) + (stoch_direction > 0) + (wpr_direction > 0) + (delta_norm > 0)

# Hány indikátor mutat Short-ot?
n_short = (df_direction < 0) + (mfi_direction < 0) + (stoch_direction < 0) + (wpr_direction < 0) + (delta_norm < 0)

# Konszenzus erő: mindegyik egy irányba = erős signal
consensus = (n_long - n_short) / 5.0  # [-1, +1] skálán
```

Ez az amit a LGBM MEGÉRT — nem nyers értékeket, hanem:
1. **Irány** a választóhoz képest (+1 Long / -1 Short)
2. **Intenzitás** (messze a választótól = erős)
3. **Gyorsulás** (növekszik = erősödő trend)
4. **Esemény** (threshold crossing = overbought/oversold)
5. **Konszenzus** (több indikátor egy irányba = erősítés)
