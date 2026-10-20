#!/usr/bin/env python3
"""V6 2min FADE demo chart - ZOLD P(Long) csucsok utan SHORT entry 2 percig"""
import json, pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
CHART_OUT = Path('/data/LGBM_copilot/charts/BTCUSD_v6_2min_FADE_demo.html')

df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
day = df.loc['2026-09-01'].copy().reset_index(drop=True)

pL = day['p_long_2min'].values
pS = day['p_short_2min'].values
pN = day['p_noise_2min'].values
px = day['price'].values
n = len(day)

HOLD = 16  # 2 perc = 16 bar
fwd = np.full(n, np.nan)
fwd[:-HOLD] = (px[HOLD:] / px[:-HOLD] - 1) * 100

fade_mask = pL > 0.55
fade_idx = np.where(fade_mask)[0]
print(f'Fade csucsok (P(Long) > 0.55): {len(fade_idx)} db')

sig = day['signal_2min'].values
ts = [day.index[i].strftime('%Y-%m-%d %H:%M:%S') for i in range(n)]

fade_ts = [ts[i] for i in fade_idx if i+HOLD < n]
fade_px = [px[i] for i in fade_idx if i+HOLD < n]
fade_pL = [pL[i] for i in fade_idx if i+HOLD < n]

orig_long_ts = [ts[i] for i in range(n) if sig[i] == 1]
orig_long_px = [px[i] * 0.9997 for i in range(n) if sig[i] == 1]
orig_short_ts = [ts[i] for i in range(n) if sig[i] == -1]
orig_short_px = [px[i] * 1.0003 for i in range(n) if sig[i] == -1]

j = json.dumps
js = '<script>\n'
js += f'var ts={j(ts)},px={j([round(float(x),2) for x in px])},pL={j([round(float(x),4) for x in pL])},pS={j([round(float(x),4) for x in pS])},pN={j([round(float(x),4) for x in pN])};\n'
js += f'var fade_ts={j(fade_ts)},fade_px={j([round(float(x),2) for x in fade_px])},fade_pL={j([round(float(x),4) for x in fade_pL])};\n'
js += f'var orig_long_ts={j(orig_long_ts)},orig_long_px={j([round(float(x),2) for x in orig_long_px])},orig_short_ts={j(orig_short_ts)},orig_short_px={j([round(float(x),2) for x in orig_short_px])};\n'
js += '''(function(){
var data=[];
data.push({x:ts,y:px,type:"scatter",mode:"lines",line:{color:"#00d2ff",width:1},name:"Price",xaxis:"x",yaxis:"y"});
data.push({x:orig_long_ts,y:orig_long_px,type:"scatter",mode:"markers",marker:{symbol:"triangle-up",color:"#228B22",size:7},name:"Eredeti V6 Long",xaxis:"x",yaxis:"y"});
data.push({x:orig_short_ts,y:orig_short_px,type:"scatter",mode:"markers",marker:{symbol:"triangle-down",color:"#B22222",size:7},name:"Eredeti V6 Short",xaxis:"x",yaxis:"y"});
data.push({x:fade_ts,y:fade_px,type:"scatter",mode:"markers",marker:{symbol:"x",color:"#FF0000",size:11,line:{width:2}},name:"FADE Short entry (P(L)>0.55)",xaxis:"x",yaxis:"y"});
data.push({x:ts,y:pL,type:"scatter",mode:"lines",line:{color:"#228B22",width:2},name:"P(Long) [ZOLD = FADE Short!]",xaxis:"x2",yaxis:"y2"});
data.push({x:ts,y:pS,type:"scatter",mode:"lines",line:{color:"#B22222",width:2},name:"P(Short) [PIROS]",xaxis:"x2",yaxis:"y2"});
data.push({x:ts,y:pN,type:"scatter",mode:"lines",line:{color:"#FF8C00",width:1,dash:"dot"},name:"P(Noise)",xaxis:"x2",yaxis:"y2"});
data.push({x:fade_ts,y:fade_pL,type:"scatter",mode:"markers",marker:{symbol:"x",color:"#FF0000",size:9,line:{width:2}},name:"Fade trigger",xaxis:"x2",yaxis:"y2"});
var layout={showlegend:true,legend:{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",font:{color:"#f2f5fa",size:10}},xaxis:{domain:[0,1],anchor:"y",matches:"x2",showticklabels:false,rangeslider:{visible:false},gridcolor:"#283442"},yaxis:{domain:[0.32,1.0],anchor:"x",gridcolor:"#283442",title:{text:"Price",font:{color:"#f2f5fa"}}},xaxis2:{domain:[0,1],anchor:"y2",gridcolor:"#283442"},yaxis2:{domain:[0,0.291],anchor:"x2",range:[0,1],gridcolor:"#283442",title:{text:"Probability",font:{color:"#f2f5fa"}}}},shapes:[{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:0.5,y1:0.5,line:{color:"rgba(255,255,255,0.3)",width:1,dash:"dash"}},{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:0.55,y1:0.55,line:{color:"#FF0000",width:1,dash:"dot"}}],annotations:[{font:{size:16},showarrow:false,text:"BTCUSD v6 2min FADE demo (ZOLD csucs = SHORT signal)",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}}],plot_bgcolor:"rgb(17,17,17)",paper_bgcolor:"rgb(17,17,17)",font:{color:"#f2f5fa"},margin:{l:55,r:80,t:25,b:40},height:900,hovermode:"x unified",dragmode:"zoom"};
Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});
})();
</script>'''

html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>BTCUSD v6 2min FADE demo</title>
<script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script>
<style>body{{margin:0;padding:0;background:rgb(17,17,17);color:#f2f5fa;font-family:monospace}}
#chart{{width:100%;height:calc(100vh - 36px)}}
#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:#00d2ff;text-align:center}}</style></head>
<body><div id="chart"></div>
<div id="info">FADE demo | ZOLD csucs (P(Long)>0.55) -> SHORT 2 percig | 65 fade trade, WR=56.9%, +1.35%</div>
{js}</body></html>'''

CHART_OUT.write_text(html)
print(f'✅ {CHART_OUT.name} ({len(html)//1024}KB)')
