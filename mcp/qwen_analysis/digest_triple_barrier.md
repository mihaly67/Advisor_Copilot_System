# Triple Barrier Method — Code Digest

## Forrás: financial-ml-toolkit + triple_barrier-main
## Dátum: 2026-10-12

---

## 1. VOLATILITY ESTIMATION (barrier width = vol × multiplier)

### EWMA Volatility (labeling.py)
```python
def get_volatility(close, span=20, min_periods=5):
    returns = close.pct_change()
    volatility = returns.ewm(span=span, min_periods=min_periods).std()
    return volatility
```

### Parkinson Volatility (labeling_advanced.py) — high-low alapú
```python
def get_parkinson_volatility(high, low, span=20):
    log_hl = np.log(high / low)
    factor = 1.0 / (4.0 * np.log(2))
    parkinson = np.sqrt(factor * (log_hl ** 2).rolling(span).mean())
    return parkinson
```

### BTCUSD adaptáció
- **EWMA span=20** dollar bar → ~1M USD/trade forgalmú ablak
- Parkinson használata HA high/low elérhető (dollar bar-nál igen!)
- **NE használj fix pip TP/SL!** → `target = vol * profit_mult`

---

## 2. HORIZONTAL BARRIERS (TP és SL szintek)

```python
def get_horizontal_barriers(close, volatility, profit_mult=2.0, stop_mult=1.0):
    barriers['upper'] = close + (volatility * profit_mult)   # Take Profit
    barriers['lower'] = close - (volatility * stop_mult)     # Stop Loss
    return barriers
```

### Kulcs: Aszimmetrikus barrier-ek!
- `profit_mult=2.0, stop_mult=1.0` → TP 2× szélesebb mint SL
- Ez **trend-following** bias-t ad (hagyjuk futni a nyereséget)
- **Counter-trend**: fordítsd meg! `profit_mult=1.0, stop_mult=2.0`

---

## 3. VERTICAL BARRIER (timeout)

```python
def get_vertical_barriers(close, num_bars=50):
    # Exit after num_bars bars if no horizontal barrier hit
    for i, ts in enumerate(timestamps):
        exit_idx = min(i + num_bars, len(timestamps) - 1)
        vertical.iloc[i] = timestamps[exit_idx]
```

### BTCUSD: `num_bars=50` dollar bar → ~50M USD forgalom a timeout-ig

---

## 4. BARRIER HIT DETECTION (Numba JIT)

```python
@jit(nopython=True)
def _find_first_barrier_hit(prices, upper, lower, max_idx):
    for i in range(max_idx):
        if prices[i] >= upper: return i, 1    # TP hit → label +1
        elif prices[i] <= lower: return i, -1  # SL hit → label -1
    return max_idx - 1, 0                      # Timeout → label 0
```

### Label jelentés:
- **+1**: TP hit először → long profit / short loss
- **-1**: SL hit először → long loss / short profit
- **0**: Timeout → bizonytalan, használható vagy eldobható

---

## 5. SIDE-AWARE TBM (labeling_advanced.py)

```python
def triple_barrier_labels(close, volatility=None, ..., side=None):
    # HA side meg van adva:
    # side=1 (long) → upper=TP, lower=SL
    # side=-1 (short) → lower=TP, upper=SL (megcserélve!)
    if side is not None:
        # Apply side: for long, upper=TP; for short, lower=TP
        ...
```

### Ez a KULCS a meta-labeling pipeline-hez!
1. Primary model → side prediction (+1 vagy -1)
2. TBM side-aware → label = hogy az adott irányú trade nyert vagy vesztett
3. Meta-model → bináris: vegyük-e a trade-t?

---

## 6. META-LABELING

```python
def get_meta_labels(primary_signal, triple_barrier_result):
    # Long signals (signal==1) correct if label==1 (TP hit)
    # Short signals (signal==-1) correct if label==-1 (SL hit for short=TP)
    meta_labels = ((signal == 1) & (labels == 1)) | ((signal == -1) & (labels == -1))
    meta_labels = meta_labels.astype(int)  # 1=correct, 0=wrong
```

### Pipeline:
```
Primary model → side (+1/-1)
    ↓
TBM side-aware → {+1, -1, 0}
    ↓
Meta-label: 1 if side matched TBM outcome, 0 otherwise
    ↓
Meta-model trains on: features → meta_label (0/1)
    ↓
At inference: primary side → meta probability → trade only if P(meta=1) > threshold
```

---

## 7. OOP REFERENCE (triple_barrier-main)

### Labeler osztály
```python
class Labeler:
    def __init__(self, open_price, high_price, low_price, close_price,
                 box_setup: Orders, dynamic_exit=None):
        # Separate barrier objects
        self._take_profit_barrier = TakeProfit(...)
        self._stop_loss_barrier = StopLoss(...)
        self._time_barrier = TimeBarrier(...)
        self._dynamic_barrier = DynamicOrder(...)
    
    def compute(self) -> OrderBoxHits:
        self._compute_take_profit_barrier()
        self._compute_stop_loss_barrier()
        self._compute_time_barrier()
        # Determine which was hit FIRST
        self._compute_first_hit()
```

### TradeSide enum
```python
class TradeSide(Enum):
    BUY = 1
    SELL = -1
```

### Pip handling (futures/forex specific!)
```python
# BoxBuilder.take_profit:
self._take_profit = open_price + trade_side.value * take_profit_width * (10 ** -pip_decimal_position)
```

### BTCUSD: `pip_decimal_position = 2` (BTCUSD tick = 0.01)

---

## 8. CUSUM FILTER (event detection = sampling, NOT labeling!)

```python
def cusum_filter(close, threshold=None):
    # CUSUM filter detects structural changes
    # Returns timestamps where CUSUM exceeds threshold
    # These are EVENT TIMES → sample only at these bars
    # NOT labels! Direction from sign of CUSUM at event
```

### BTCUSD: CUSUM → DF_Curve proxy → direction feature!
