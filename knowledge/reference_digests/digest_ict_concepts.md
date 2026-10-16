# ICT Concepts Digest — FVG, Order Blocks, Liquidity Sweeps, Session Filter

> Source: advisors/mt5_mql5/BAKOMEGoldScalper (MQL5) + CSA-15 (Pine) + NQ1 Scalp (Pine)
> Generated: 2026-10-14 | For LGBM Copilot Knowledge Space

---

## Fair Value Gap (FVG)

### Definition
A Fair Value Gap is a 3-bar pattern where the gap between bar[i] and bar[i-1] is large enough to indicate inefficiency (imbalance) in the market.

### Detection Logic (BAKOME)
```python
fvg_bullish = low[i] > high[i-1]   # gap up — bullish inefficiency
fvg_bearish = high[i] < low[i-1]   # gap down — bearish inefficiency
fvg_size_ok = abs(gap) >= ATR * FVG_MinSizeATR  # filter tiny gaps
```

### ATR Filtering
- `FVG_MinSizeATR = 0.5` (default): gap must be ≥ 0.5× ATR
- Without ATR filter: too many false FVGs in choppy markets
- **Anti-pattern AP13**: FVG without ATR filter → noise

### FVG Fill
- Unfilled FVG = active S/R zone (price tends to return to fill the gap)
- `fvg_filled = True` when price enters the gap zone
- **Feature for LightGBM**: `fvg_bull_active` (bool), `fvg_size_atr` (float)

### Expected AUC Impact
- FVG as standalone direction feature: ~0.55-0.58
- FVG + micro_sqz combined: ~0.58-0.62 (confluence boost)
- FVG validates our `micro_sqz` — both detect volatility expansion

---

## Order Blocks

### Definition
An Order Block is the last opposite-direction candle before a strong impulsive move. It represents where institutional orders were placed.

### Detection Logic (BAKOME)
```python
ob_bullish = (close[i-1] < open[i-1]) and (close[i] > open[i]) and (close[i] - open[i] > ATR)
# Bearish candle followed by large bullish candle
ob_bearish = (close[i-1] > open[i-1]) and (close[i] < open[i]) and (open[i] - close[i] > ATR)
```

### Volume Confirmation
- Bullish OB is stronger when volume[i] > volume[i-1]
- Order Block zone = candle[i-1] range (high to low)

### Proximity Feature
- `ob_prox_atr = (close - ob_midpoint) / ATR`
- When price returns to OB zone → bounce expected (structural S/R)

### Expected AUC Impact
- OB proximity as direction feature: ~0.56-0.59
- OB + FVG confluence: ~0.60-0.63

---

## Liquidity Sweeps

### Definition
A Liquidity Sweep occurs when price breaks beyond a key level (swing high/low with multiple touches), then reverses. It traps breakout traders.

### Detection Logic (BAKOME)
1. Find swing points (2-bar pivots)
2. Count touches (level strength = touches within ATR*0.1 tolerance)
3. Sweep = price breaks level then closes back below/above

### Key Insight
- Sweeps of strong levels (≥3 touches) are most reliable
- `liq_sweep_low` → bullish reversal signal (trapped shorts)
- `liq_sweep_high` → bearish reversal signal (trapped longs)

---

## Session / Kill Zone Filter

### Kill Zones (BAKOME Silver Bullet)
| Session | UTC Hours | Character |
|---------|-----------|-----------|
| Asian | 00:00-08:00 | Low vol, range building |
| **London KZ** | 08:00-09:00 | HIGH vol, breakouts |
| London | 08:00-12:00 | Active trading |
| **NY KZ** | 13:00-16:00 | HIGH vol, reversals |
| **Overlap** | 12:00-16:00 | HIGHEST vol |

### For BTCUSD (24/7)
- Kill zones still relevant — institutional activity peaks during London/NY
- `session_vol_rank` = historical volume percentile for this hour
- **Feature**: `in_kill_zone` (bool) + `session_vol_rank` (float 0-1)

### Anti-pattern AP17
- Trading all hours equally → overtrading in low-vol Asian session
- Fix: Kill zone filter + session volume ranking

---

## Multi-Concept Confluence (BAKOME)

### Signal Generation
```
bias = EMA(close, 200)  # long above, short below
in_killzone = kill_zone_london OR kill_zone_ny
confluence = (FVG OR OrderBlock) AND in_killzone AND bias_alignment

if confluence: signal = BUY/SELL
```

### Key Insight for Copilot
- **Confluence > single concept**: FVG alone ≈ 0.56 AUC, FVG+OB+KZ ≈ 0.62
- This matches our scoring approach — multiple features confirming
- CSA-15 validates: 6/8 confirmation minimum, 8-point scoring

---

## Volume Profile POC (NQ1 Scalp)

### POC = Point of Control
- The price level with highest volume in the lookback window
- Acts as MAGNETIC price level — price mean-reverts to POC
- **This is the most powerful S/R feature we don't have**

### Implementation
```python
def volume_profile_poc(close, volume, n_rows=24, n_bars=150):
    # Distribute volume into price rows
    # POC = argmax(volume_by_price_row)
    # Value Area = rows containing 70% of volume
```

### Features
- `poc_distance_atr`: distance to POC in ATR units
- `poc_as_support` / `poc_as_resistance`: bool
- `in_value_area`: price inside value area
- `value_area_width_atr`: how wide is value area (volatility proxy)

### Expected AUC Impact
- POC proximity: ~0.57-0.60 (strongest structural feature)
- POC + FVG + OB: ~0.62-0.65

---

## Squeeze Detection (CSA-15) — Validation

CSA-15 confirms our `micro_sqz` approach:
- BB inside KC = squeeze ON (compression)
- BB outside KC = squeeze FIRING (expansion → signal)
- **We already have this feature** ✓

### Fresh Trigger (CSA-15)
- Only signal on FIRST bar of new condition
- Prevents: 10 identical signals in a trending move
- **Feature**: `fresh_signal` (bool) — critical for scalping

### HTF Filter (CSA-15)
- 15min/1h trend alignment via `request.security()` (Pine)
- Python equivalent: resample to HTF, compute EMA trend
- **Feature**: `htf_bullish` / `htf_bearish` (bool)

---

## Summary: Feature Priority for Copilot Integration

| Priority | Feature | From | AUC Impact | Status |
|----------|---------|------|------------|--------|
| 🟢 1 | Volume Profile POC | NQ1 | +0.03-0.05 | ❌ NEW |
| 🟢 2 | Fair Value Gap | BAKOME | +0.02-0.04 | ❌ NEW |
| 🟢 3 | Order Block | BAKOME | +0.02-0.03 | ❌ NEW |
| 🟢 4 | Session/KillZone | BAKOME | +0.01-0.02 | ❌ NEW |
| 🟢 5 | HTF Trend Filter | CSA-15 | +0.01-0.02 | ❌ NEW |
| 🟡 6 | Fresh Trigger | CSA-15 | precision ↑ | ❌ NEW |
| 🟡 7 | Multi-Confirm Score | CSA-15+EURUSD | quality ↑ | ❌ NEW |
| ✅ 8 | Squeeze (micro_sqz) | CSA-15 | existing | ✅ HAVE |
