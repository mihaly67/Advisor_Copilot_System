#!/usr/bin/env python3
"""Validate chart_analyzer endpoint."""
import json, urllib.request

base = "http://127.0.0.1:8420"

# Health
r = urllib.request.urlopen(base + "/health")
print("Health:", json.loads(r.read()))

# Regex test
data = json.dumps({"path": "/data/dev/LGB_copilot_system/viz/viz_pred_2026-08-28.html", "method": "regex"}).encode()
req = urllib.request.Request(base + "/chart-analyze", data=data, headers={"Content-Type": "application/json"})
r = urllib.request.urlopen(req)
d = json.loads(r.read())
rx = d["regex_analysis"]
print(f"\n=== REGEX ===")
print(f"Title: {rx['layout']['title']}")
print(f"Traces: {[t['type'] for t in rx['traces']]}")
print(f"Thresholds: {len(rx['layout']['shapes'])} shapes")
if rx.get("candlestick"):
    cs = rx["candlestick"]
    print(f"Candlestick: {cs['time_range']['start']} → {cs['time_range']['end']} ({cs['time_range']['num_bars']} bars)")

# Playwright test
data2 = json.dumps({"path": "/data/dev/LGB_copilot_system/viz/viz_pred_2026-08-28.html", "method": "playwright", "wait_ms": 3000}).encode()
req2 = urllib.request.Request(base + "/chart-analyze", data=data2, headers={"Content-Type": "application/json"})
r2 = urllib.request.urlopen(req2)
d2 = json.loads(r2.read())
pw = d2.get("playwright_analysis", {})
print(f"\n=== PLAYWRIGHT ===")
for plot_id, plot_data in pw.get("plots", {}).items():
    if plot_id == "_meta": continue
    traces = plot_data.get("traces", [])
    print(f"Plot {plot_id[:8]}...: {len(traces)} traces")
    for t in traces:
        if t["type"] == "candlestick":
            print(f"  🕯️ {t['name']}: {t['num_bars']} bars, ${t['price_min']:,.0f}-${t['price_max']:,.0f}")
        elif t["type"] == "scatter":
            print(f"  📈 {t['name']}: y_count={t['y_count']}, y_mean={t.get('y_mean','?')}")

print("\n✅ ALL TESTS PASSED")
