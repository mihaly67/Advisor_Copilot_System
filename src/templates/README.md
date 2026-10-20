# Scalper Copilot Chart Templates

## scalper_candlestick_chart_template.py

**Standard template** for all future Scalper Copilot chart generation.

### Features
- **Candlestick** OHLC bars (green #26a69a up, red #ef5350 down) — fallback to line if no OHLC
- **P(Long)** green line in probability subchart
- **P(Short)** red line in probability subchart
- **P(Noise)** orange dotted line in probability subchart
- **Long signals** green ▲ markers below price
- **Short signals** red ▼ markers above price
- **6 horizons**: 20s, 1min, 2min, 3min, 4min, 5min
- Dark theme (rgb(17,17,17) background)

### Usage
```bash
python3 scalper_candlestick_chart_template.py --date 2026-08-31
```

### Requirements in preds CSV
- `price` — close price (required)
- `open, high, low, close` — OHLC for candlestick (optional, falls back to line)
- `p_long_{h}, p_short_{h}, p_noise_{h}, signal_{h}` — per horizon (required)

### Design Rules
1. Candlestick is the DEFAULT — always prefer over line chart
2. Probability subchart always shows P(Long), P(Short), P(Noise)
3. Signal markers (▲▼) always visible on price chart
4. Dark theme consistent across all charts
5. Responsive layout, height=900px