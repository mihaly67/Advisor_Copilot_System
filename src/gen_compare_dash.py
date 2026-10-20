#!/usr/bin/env python3
"""Generate v6.1 vs v6.2 comparison dashboard HTML"""
import json
from pathlib import Path

CHART_DIR = Path('/data/LGBM_copilot/charts')
BG='#111'; TC='#f2f5fa'
horizons = ['20s','1min','2min','3min','4min','5min']
wr61 = [54.5, 58.8, 59.2, 61.3, 58.9, 61.5]
wr62 = [56.1, 60.8, 61.8, 61.5, 58.6, 60.8]
ev61 = [0.1363, 0.1705, 0.1732, 0.1904, 0.1715, 0.1923]
ev62 = [0.1490, 0.1867, 0.1947, 0.1922, 0.1684, 0.1864]
pnl61m = [1.16, 1.31, 1.34, 1.51, 1.29, 1.51]
pnl62m = [0.87, 1.00, 1.04, 1.04, 0.81, 0.95]
contra_red = [76.4, 84.6, 90.6, 90.4, 96.9, 93.1]
j=json.dumps

js = f"""<script>
var H={j(horizons)};
var BG2={{plot_bgcolor:'rgb(17,17,17)',paper_bgcolor:'rgb(17,17,17)',font:{{color:'{TC}'}}}};

Plotly.newPlot('wr',[
{{x:H,y:{j(wr61)},type:'bar',name:'v6.1 WR%',marker:{{color:'#FF6B6B'}},offsetgroup:'a'}},
{{x:H,y:{j(wr62)},type:'bar',name:'v6.2 WR%',marker:{{color:'#4CAF50'}},offsetgroup:'b'}}
],Object.assign({{barmode:'group',title:{{text:'Win Rate (%)',font:{{size:14}}}},yaxis:{{range:[52,64],dtick:2}},showlegend:true}},BG2),{{displayModeBar:false}});

Plotly.newPlot('ev',[
{{x:H,y:{j(ev61)},type:'scatter',mode:'lines+markers',name:'v6.1 EV',line:{{color:'#FF6B6B',width:3}},marker:{{size:8}}}},
{{x:H,y:{j(ev62)},type:'scatter',mode:'lines+markers',name:'v6.2 EV',line:{{color:'#4CAF50',width:3}},marker:{{size:8}}}}
],Object.assign({{title:{{text:'Expected Value / Trade (ATR)',font:{{size:14}}}},yaxis:{{range:[0.12,0.22]}}}},BG2),{{displayModeBar:false}});

Plotly.newPlot('pnl',[
{{x:H,y:{j(pnl61m)},type:'bar',name:'v6.1 PnL $M',marker:{{color:'#FF6B6B'}},offsetgroup:'a'}},
{{x:H,y:{j(pnl62m)},type:'bar',name:'v6.2 PnL $M',marker:{{color:'#4CAF50'}},offsetgroup:'b'}}
],Object.assign({{barmode:'group',title:{{text:'Total PnL ($M)',font:{{size:14}}}},yaxis:{{range:[0,1.8]}}}},BG2),{{displayModeBar:false}});

Plotly.newPlot('contra',[
{{x:H,y:{j(contra_red)},type:'bar',name:'Contra redukcio %',marker:{{color:['#FF6B6B','#FF9800','#FFC107','#8BC34A','#4CAF50','#2196F3']}}}}
],Object.assign({{title:{{text:'Contra-Trend Redukcio (%)',font:{{size:14}}}},yaxis:{{range:[0,100]}}}},BG2),{{displayModeBar:false}});
</script>"""

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>v6.1 vs v6.2 Verseny</title>
<script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script>
<style>
body {{margin:0;padding:20px;background:{BG};color:{TC};font-family:monospace}}
.grid {{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.box {{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:12px}}
h1 {{color:#00d2ff;text-align:center}}
.verdict {{background:#0a2a0a;border:2px solid #228B22;border-radius:12px;padding:20px;margin-top:16px;text-align:center}}
.verdict h2 {{color:#4CAF50;margin:0}}
table {{margin:16px auto;border-collapse:collapse;font-size:13px}}
th,td {{padding:4px 12px;border:1px solid #333}}
th {{color:#00d2ff}}
.win {{color:#4CAF50;font-weight:bold}}
.lose {{color:#FF6B6B}}
</style></head><body>
<h1>v6.1 (no filter) vs v6.2 (regime filter) — VERSENY</h1>
<div class="grid">
<div class="box" id="wr"></div>
<div class="box" id="ev"></div>
<div class="box" id="pnl"></div>
<div class="box" id="contra"></div>
</div>

<table>
<tr><th>Horizon</th><th>v6.1 WR</th><th>v6.2 WR</th><th>v6.1 EV</th><th>v6.2 EV</th><th>Contra ↓</th><th>EV Winner</th></tr>
<tr><td>20s</td><td>54.5%</td><td class="win">56.1%</td><td>0.136</td><td class="win">0.149</td><td>76.4%</td><td class="win">v6.2</td></tr>
<tr><td>1min</td><td>58.8%</td><td class="win">60.8%</td><td>0.171</td><td class="win">0.187</td><td>84.6%</td><td class="win">v6.2</td></tr>
<tr><td>2min</td><td>59.2%</td><td class="win">61.8%</td><td>0.173</td><td class="win">0.195</td><td>90.6%</td><td class="win">v6.2</td></tr>
<tr><td>3min</td><td>61.3%</td><td class="win">61.5%</td><td>0.190</td><td class="win">0.192</td><td>90.4%</td><td class="win">v6.2</td></tr>
<tr><td>4min</td><td class="win">58.9%</td><td class="lose">58.6%</td><td class="win">0.172</td><td class="lose">0.168</td><td>96.9%</td><td class="lose">v6.1</td></tr>
<tr><td>5min</td><td class="win">61.5%</td><td class="lose">60.8%</td><td class="win">0.192</td><td class="lose">0.186</td><td>93.1%</td><td class="lose">v6.1</td></tr>
</table>

<div class="verdict">
<h2>🏆 NYERTES: v6.2 (regime filter) — Scalping horizontokban</h2>
<p style="color:#aaa;font-size:13px">
<b style="color:#4CAF50">Előny:</b> +1.6–2.6% WR javulás (20s–2min), 76–97% contra-trend redukció, 0 contra TRENDING regime-ben<br>
<b style="color:#FF8C00">Hátrány:</b> 30% kevesebb szignál → 30% kevesebb total PnL; 4min/5min WR enyhe romlás (–0.3–0.7%)<br>
<b style="color:#00d2ff">Ajánlás:</b> v6.2 scalping (20s–2min) ✅ &nbsp;|&nbsp; v6.1 swing (4min–5min) &nbsp;|&nbsp; vagy hibrid: v6.2 20s–3min + v6.1 4min–5min
</p>
</div>
{js}
</body></html>"""

out = CHART_DIR / 'v6_comparison_dashboard.html'
with open(out, 'w') as f:
    f.write(html)
print(f'✅ {out.name} ({len(html)//1024}KB)')
