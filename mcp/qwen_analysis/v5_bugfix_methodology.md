# v5 Bugfix & Metodika — Visszakövethető leírás

## Bug #1: CUSUM Threshold Dimenzióhiba

### Felfedezés módszere
1. Első futtatás: "Train: 42,681 events (99.9%)" — gyanús, minden bar CUSUM event
2. Ránéztem a `prado_cusum_filter.py` forráskódjára:
   - `diff = close_prices.diff().fillna(0).values` → **dollárban** számol
   - Threshold = 0.000496 → **ez is dollárban értelmezve** = $0.0005
3. XAUUSD átlagos bar move ~$2-8 → $0.0005 threshold = minden bar triggerel

### Javítás
```python
# ROSSZ (v4-ből öröklött):
ret_tr = bars_tr['Close'].pct_change().fillna(0)
vol_tr = ret_tr.std()
cthr = vol_tr * CUSUM_VOL_MULT  # = 0.000496 (%-ban!)

# JÓ (v5):
daily_ret = bars_tr['Close'].pct_change().fillna(0)
daily_vol = daily_ret.std()  # = 0.000331 (%-ban)
avg_price = bars_tr['Close'].mean()  # = $4235
cthr = daily_vol * avg_price * CUSUM_VOL_MULT  # = $2.10 (dollárban!)
```

### Verifikáció
- CUSUM event rate: 99.9% → **35.4%** ✓
- Train: 15,137 events / 42,742 bars — reális

---

## Bug #2: Short Label Kizárva Event Mask-ból

### Felfedezés módszere
1. "Train: Long=7,369 Short=0 Noise=22,188" — Short=0 lehetetlen PT=SL=1.0-nál
2. Végiggondoltam a label encoding-ot:
   - `lb[i]=2` ha Long, `lb[i]=0` ha Short
   - `ev_tr = cm_tr & (lb_tr != 0)` — **lb=0 (Short) kizárva!**
3. A Python `0` egyszerre jelent "Short label" és "False/ini érték"

### Javítás
```python
# ROSSZ:
lb[i] = 2  # Long
lb[i] = 0  # Short  ← ez!=0 kizárja!
ev_tr = cm_tr & (lb_tr != 0)

# JÓ:
lb[i] = 1   # Long = +1
lb[i] = -1  # Short = -1
# lb[i] = 0  # Noise/timeout (nem CUSUM event)
ev_tr = cm_tr & (lb_tr != 0)  # Most helyes: -1 és 1 is != 0
```

### Verifikáció
- Long=7,369, Short=7,436 — **szimmetrikus** ✓ (PT=SL=1.0 elvárás)

---

## Bug #3: 3-class LGBM de hiányzik Noise osztály

### Felfedezés módszere
1. `ValueError: 1 is not in list` az `apply_threshold`-ban
2. Csak CUSUM event-eken tanítunk → nincs Noise sample → classes=[0,2]
3. A 3-class threshold kód `list(classes).index(1)`-et keresett

### Javítás
- Binary LGBM (0=Short, 1=Long) — a CUSUM event-eken nincs is Noise
- `objective='binary'`, `metric='binary_logloss'`
- Egyszerűbb és helyesebb: csak 2 döntés van event-ken

---

## Bug #4: CUSUM_Direction Feature = 0 shift(1) után

### Felfedezés módszere
1. Feature importance-ben CUSUM_Direction NINCS a top 10-ben
2. Debug script: kinyomtattam `cd[i]` és `cd_series.iloc[i]` (shifted) értékeket event pozícókon
3. Eredmény: **shifted=0.0** a legtöbb event-nél, mert:
   - CUSUM event-ek ritkák (35%)
   - `shift(1)` az ELŐZŐ bar CUSUM_dir-jét veszi
   - Ha előző bar nem CUSUM event → cd=0

### Javítás (Forward-fill)
```python
# ROSSZ:
df['CUSUM_Direction'] = pd.Series(cusum_dir, index=df.index).shift(1)

# JÓ:
raw_cd = pd.Series(cusum_dir, index=df.index)
ff_cd = raw_cd.replace(0, np.nan).ffill().fillna(0)  # last known direction
df['CUSUM_Direction'] = ff_cd.shift(1)
```

### Megjegyzés
Forward-fill után SEM jelent meg a top 10-ben — a feature nem elég prediktív lineáris modellekhez. **Nemlineáris interakció** (CUSUM_dir × Bar_Dir × RSI) kell → MLP.

---

## Metodika: Hogyan teszteltünk

### Konfiguráció sweep
1. **PT=SL=1.0** → szimmetrikus baseline
2. **PT=1.5/SL=1.0** → Short-bias (v4 konfig, Fade CUSUM nyer)
3. **PT=1.0/SL=1.5** → Long-bias (tükrözött, Fade CUSUM ront)

### Stratégiák minden konfiguráción
1. **CUSUM baseline**: CUSUM UP→Long, DOWN→Short (naiv)
2. **Fade CUSUM**: CUSUM UP→Short, DOWN→Long (reversion)
3. **ML only**: Binary LGBM predikció
4. **Fade + ML conf**: Fade irány ha ML egyetért, ML irány ha erősen disagree

### Értékelési metrika
- WR (win rate %), Profit ($), Trade count
- Long/Short WR breakdown
- OOS vs VIZSGA gap (overfitting detekció)
