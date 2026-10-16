# Jules Advisor — Projekt Cél és Architektúra

## CÉL (végleges, 2026.09.26.)

**Az emberi döntéshozatal támogatása.** A copilot NEM kereskedik, NEM nyomja a gombokat.
Csak **valószínűségeket mond** — valószínű irány + valószínűségi érték — hogy az ember jobban döntsön.

A gép mindent összevet, amit az ember nem tud egyszerre figyelni:
- 6 pivot szint (Micro/Sec/Ter R/S) + interakciók (bounce, breakout, rejection)
- 11 NavSystem indikátor + pivot távolságok
- Threshold crossing események → valószínűség növelés

A kimenet: **P(Long), P(Short), P(Noise)** görbe + threshold szintek → az ember látja a valószínűséget és dönt.

---

## Architektúra (meglévő, működő)

```
MT5 EA ──TCP 5555──→ Python Copilot ──ZMQ PUB 5557──→ HUD (PyQt5)
                            │
                       LGBM model
                    predict_proba()
                  → P(Long), P(Short), P(Noise)
```

- **EA** (MQ5): Tick aggregáció → dollar bar → JSON TCP send
- **Python Copilot** (`mt5_live_copilot_v2.0`): Feature-ök + LGBM inferencia → ZMQ broadcast
- **HUD** (`hud_v1.17_nn`): PyQt5 chart + P(Long)/P(Short)/P(Noise) görbék + pivot szintek + threshold vonalak

---

## NavSystem Indikátorok — MIT MUTATNAK?

### 1. PULSE modul (Trend impulzus + anómália)

| Indikátor | Tartomány | Nulla = | Pozitív = | Negatív = |
|---|---|---|---|---|
| **Pulse_MACD_Hist** | [-∞, +∞] | Nincs trend | Bullish momentum növekszik | Bearish momentum növekszik |
| **Pulse_DF_Curve** | [-∞, +∞] | MACD = BB közép | MACD BB felett (bullish anómália) | MACD BB alatt (bearish anómália) |

**Emberi olvasat:**
- MACD_Hist > 0 és növekszik → bullish trend erősödik
- MACD_Hist < 0 és csökken → bearish trend erősödik
- DF_Curve nagy pozitív → az ár "túl messze" van a BB középtől felfelé → lehetséges overextension
- DF_Curve nagy negatív → az ár "túl messze" van a BB középtől lefelé → lehetséges overextension

### 2. FLOW modul (Pénzáramlás + volumenz)

| Indikátor | Tartomány | Nulla/Közép = | Magas = | Alacsony = |
|---|---|---|---|---|
| **Flow_MFI_5** | [0, 100] | 50 = semleges | Buying pressure dominál (Pénz beáramlik) | Selling pressure dominál (Pénz kiáramlik) |
| **Flow_Delta_10** | [-∞, +∞] | 0 = nincs netto flow | Vételi nyomás felhalmozódott (10 bar) | Eladási nyomás felhalmozódott (10 bar) |
| **Flow_VROC_5** | [-100, +∞] | 0 = nincs volumen változás | Volumen növekszik (aktivitás nő) | Volumen csökken (aktivitás csökken) |

**Emberi olvasat:**
- MFI > 80 → erős buying pressure (ár felé mozog + volumen is felé)
- MFI < 20 → erős selling pressure (ár lefelé mozog + volumen is lefelé)
- Delta_10 nagy pozitív → az elmúlt 10 bar-ban a vételi flow felülírja az eladási flow-t
- Delta_10 nagy negatív → az elmúlt 10 bar-ban az eladási flow dominál
- VROC_5 > 0 → volumen növekszik = "valami történni fog" (breakout közeledik?)

### 3. MOMENTUM modul (Trend erő + irány)

| Indikátor | Tartomány | Nulla/Értéke = | Magas = | Alacsony = |
|---|---|---|---|---|
| **WPR_14** | [-100, 0] | -50 = semleges | -20 felett: overbought (túl drága) | -80 alatt: oversold (túl olcsó) |
| **Stoch_K** | [0, 100] | 50 = semleges | 80 felett: overbought | 20 alatt: oversold |
| **Stoch_D** | [0, 100] | 50 = semleges | K vonal simítása → trend irány megerősítés | |

**Emberi olvasat:**
- WPR < -80 → oversold: az ár a 14 bar-os range alján van → valószínű pattanás (Long)
- WPR > -20 → overbought: az ár a 14 bar-os range tetején → valószínű visszahúzás (Short)
- Stoch K < 20 + K/D bullish cross → oversold + momentum fordul felfelé → Long signal
- Stoch K > 80 + K/D bearish cross → overbought + momentum fordul lefelé → Short signal

### 4. RSI modul (Relatív erő)

| Indikátor | Tartomány | Nulla/Közép = | Magas = | Alacsony = |
|---|---|---|---|---|
| **RSI_Fast_5** | [0, 100] | 50 = semleges | 80 felett: overbought (gyors) | 20 alatt: oversold (gyors) |
| **RSI_M15** | [0, 100] | 50 = semleges | 70 felett: overbought (makro) | 30 alatt: oversold (makro) |
| **Micro_RSI_14** | [0, 100] | 50 = semleges | 70 felett: overbought (mikro) | 30 alatt: oversold (mikro) |

**Emberi olvasat:**
- RSI_Fast_5 < 20 → gyors oversold, azonnali reakció várható
- RSI_M15 < 30 → makro oversold, nagyobb timeframe támogatja a Long-ot
- Micro_RSI_14 50 körül → NINCS irányjelzés (Noise!) — ez a "közepe=Noise" felismerés

---

## Pivot Szintek — MIT MUTATNAK?

| Szint | Jelentés | Interakció | Valószínűség |
|---|---|---|---|
| **Micro_S/R** | Azonnali (micro) támasz/ellenállás | Bounce/Breakdown/Breakout | 54-55% WR |
| **Sec_S/R** | Szekunder (közép) támasz/ellenállás | Bounce/Breakdown/Breakout | 53-57% WR |
| **Ter_S/R** | Terciér (nagy) támasz/ellenállás | Bounce/Breakdown/Breakout | 52-54% WR |

**Távolság ATR-ben (Dist_*_ATR):**
- 0 ATR = pont a pivot szinten → legmagasabb valószínűségű reakció
- 0.5-1.0 ATR = közel → mérsékelt valószínűség
- >1.5 ATR = messze → a pivot nem releváns most

---

## Indikátor + Pivot KOMBINÁCIÓ = ESEMÉNY (ami ÉR valamit)

A nyers indikátorértékek NEM prediktálnak (|r|<0.05 a forward return-nel).
De az **ESEMÉNYEK** (threshold crossing, pivot interakció) 53-57%-os WR-t adnak.

| Esemény | H5_dir% | avg_fwd5 | Emberi logika |
|---|---|---|---|
| Micro_S bounce + bullish | 54.7% | +0.20 ATR | Támasz pattanás → Long |
| Ter_S bounce | 52.6% | +0.42 ATR | Erős támasz → Long |
| Sec_R breakout + bullish | 53.9% | +0.18 ATR | Ellenállás áttörés → Long |
| Sec_S breakdown + bearish | 57.5% | +0.47 ATR | Támasz áttörés + bearish → Short |
| RSI14 < 30 | 55.4% | +0.36 ATR | Oversold → Long |
| RSI5 < 20 | 54.1% | +0.22 ATR | Gyors oversold → Long |
| WPR < -80 | 53.0% | +0.11 ATR | Oversold → Long |

**54-57% valószínűség = PONT elég egy advisor-nak.** Nem 90%, hanem "kicsit több mint fele".

---

## Modell architektúra (CÉL — probability curve)

### 2 LGBM modell kaszkád:

1. **Noise Detector** (2-class): Noise vs Directional
   - Input: NavSystem + Pivot távolságok (~20 feature)
   - Output: P(Noise), P(Directional)
   - Cél: szűrni a bar-okat amikben NINCS irányjelzés

2. **Direction Model** (2-class): Long vs Short
   - Input: Directional bar-ok + esemény feature-ök
   - Output: P(Long), P(Short)
   - Cél: irány valószínűség (ha a Noise detector szerint van irány)

### Végső kimenet:
```
P(Noise) = noise_model.predict_proba()[Noise]
P(Long)  = (1 - P(Noise)) × direction_model.predict_proba()[Long]
P(Short) = (1 - P(Noise)) × direction_model.predict_proba()[Short]
```

### Threshold szintek (az activeContext-ből):
- th_long = 0.350 → P(Long) > 35% → Long signal
- th_short = 0.360 → P(Short) > 36% → Short signal
- th_noise = 0.470 → P(Noise) > 47% → Noise (nincs signal)

---

## HUD kimenet (meglévő, működő)

A HUD (`hud_v1.17_nn.py`) MÁR mutatja:
- **P(Long), P(Short), P(Noise) görbék** (idősoros vonalak a chart-on)
- **Threshold vonalak** (0.35, 0.36, 0.47)
- **6 pivot szint** (Micro/Sec/Ter R/S)
- **Bid/Ask spread**
- **Pozíciók** (live + pending)

Az amit HOZZÁ KELL adni: **NavSystem indikátor panel** — minden indikátor értéke + zero/közép vonal → az ember látja hol van minden, nem csak a végeredményt.
