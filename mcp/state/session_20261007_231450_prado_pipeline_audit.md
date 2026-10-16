# Session: prado_pipeline_audit
*Időbélyeg: 2026-10-07T23:14:50.448993*

## PIPELINE FUNDAMENTAL AUDIT - Prado Methodology vs Jules Implementation

### KRÍTIKUS KÉRDÉS: Miért rosszabb a véletlennél a Long WR (~45%)?

### 1. PRADO HELYES PIPELINE (AFML CH2-CH3)

**Helyes sorrend:**
1. **Tick adatok → Dollar bars** (information-driven sampling, pl. $444K threshold)
2. **Dollar bar Close → CUSUM filter** → esemény-időpontok (t_events) ahol irányváltás történt
3. **t_events → Triple Barrier labeling** (Close áron, de a CUSUM által szelektált eseményeken!)
4. **Features computed at t_events** (dollar bar OHLC + M1 window context)
5. **Train model on labeled events**

**CUSUM filter (Snippet 2.4, p.39):**
```
s_pos = max(0, s_pos_prev + y_t - y_t-1)
s_neg = min(0, s_neg_prev + y_t - y_t-1)
if s_pos >= threshold → UP event (s_pos=0, s_neg=0 reset)
if s_neg <= -threshold → DOWN event (s_pos=0, s_neg=0 reset)
```
A CUSUM **IRÁNYT** is detektál (up vs down), nem csak időpontot!

**Prado elve:**
- Dollar bars = information-equivalent sampling (nem time-based)
- CUSUM filter = további szűrés: csak ahol strukturális shift van
- Triple barrier = a CUSUM eseményeken label-el, NEM minden dollar bar-on
- A modell eldönti: a CUSUM esemény actionalbe-e vagy noise

### 2. JULES JELENLEGI IMPLEMENTÁCIÓ - HIBÁK

**Hiba #1: NINCS CUSUM FILTER**
- Jules: minden dollar bar-t label-el triple barrier-rel
- Prado: csak a CUSUM által szelektált eseményeket label-el
- Hatás: rengeteg noise label (bars ahol nincs irányváltás, Close alig mozdul)

**Hiba #2: DOLLAR BAR IRÁNY NEM SZÁMÍT**
- Jules: Dollar bar OHLC csak aggregáció (Open, High, Low, Close, Num_Ticks)
- Prado: Dollar bar irány (Close vs Open sign) = buy/sell pressure proxy
- A $444K threshold bár mindkét irányban (fel és le) kumulálódhat
- Ha Close > Open → buying pressure dominált → bullish kontextus
- Ha Close < Open → selling pressure dominált → bearish kontextus
- Jelenleg ez az információ ELVÉSZ!

**Hiba #3: LABELING DOLLAR BAR CLOSE-ON**
- Jules: `price = df['Close'].iloc[i]` → Triple barrier a dollar bar Close-on
- Prado: Triple barrier a CUSUM esemény Close-on (ami dollár bar Close lehet, de szelektált!)
- A nem-szelektált bar-ok label-elése noise-t visz be

**Hiba #4: FEATURE KOMPUTÁLÁS DOLLAR BAR OHLC-BŐL**
- Jules: Pulse_DF_Curve = Close.diff().diff() → dollar bar OHLC-n számolva
- Probléma: $444K bar ~103 tick → 1 bar átlagosan 103 másodperc → diff() nagyon ritka
- Prado: Features a M1 window-ból számolva a dollar bar event időpontjában
- A dollar bar OHLC túl "durva" a momentum/velocity feature-khez

**Hiba #5: FEATURE-DIRECTION KORRELÁCIÓ ~0**
- Audit eredmény: Dist_* és irány feature-k korrelációja a next-bar Close.diff()-el ~0
- Ez azért van, mert:
  a) Dollar bar Close.diff() nem reprezentálja a valós árirányt (bar képződés zajos)
  b) Label noise miatt a modell nem tanul irányt
  c) Nincs CUSUM szelektálás → túl sok noise sample

### 3. JAVÍTÁSI TERV

**Lépés 1: CUSUM filter implementálása**
- Input: dollar_bars Close sorozat
- Output: t_events (időpontok ahol s_pos >= threshold vagy s_neg <= -threshold)
- Plusz: event_direction = +1 (up) vagy -1 (down)

**Lépés 2: Dollar bar irány feature (Bar_Sign)**
- Bar_Sign = sign(Close - Open) → [-1, 0, +1]
- Ez a buying/selling pressure proxy
- Kritikus: ez az egyetlen feature ami DIREKTEN kódolja az irányt!

**Lépés 3: CUSUM-vezérelt labeling**
- Csak a CUSUM eseményeken label-eljünk triple barrier-t
- Ez drasztikusan csökkenti a noise label-eket
- Az ML modell feladata: eldönteni, hogy a CUSUM esemény actionalbe-e

**Lépés 4: Feature-k M1 window-ból**
- Dollar bar event időpontjában visszanézünk az M1 candle-okra
- Momentum, velocity, RSI stb. az M1 OHLC-n számolva (nem dollar bar OHLC-n)
- Ez finomabb felbontású információt ad

**Lépés 5: Meta-labeling (Prado CH3)**
- Primary model: CUSUM direction (up/down) → side prediction
- Secondary model: ML → size/bet (meta-label: 1=kövesd, 0=nem kövesd)
- Ez szétválasztja az irány-döntést a méret-döntéstől

### 4. FÁJLOK
- `/data/dev/projects/z-ai-copilot/src/prado_dollar_bars.py` — dollar bar generátor (adaptív ATR)
- `/data/dev/projects/z-ai-copilot/src/dom_labeler_v5.py` — triple barrier labeler
- `/data/dev/projects/z-ai-copilot/src/jules_cfd_v3.py` — v3 pipeline (14 feature, Ter 2x)
- `/data/ml/Quant_Repos/mlfinlab/` — Prado hivatalos lib (stub, fizetős kód)
- `/data/ml/triple_barrier-main/` — triple barrier lib (működő)
- `/data/ml/barrier-method-main/` — barrier method kiegészítés