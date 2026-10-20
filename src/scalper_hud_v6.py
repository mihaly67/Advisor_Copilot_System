#!/usr/bin/env python3
"""
Scalper HUD v6 — 3-Horizon Dashboard
  FELSŐ (65%): Candlestick + Long▲ Short▼ + regime színezés
  ALSÓ (35%): 3 panel — 2min, 3min, 5min — P(Long)/P(Short)/küszöb/zaj
"""
import json, numpy as np, pandas as pd
from pathlib import Path

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts')
CHART_DIR.mkdir(parents=True, exist_ok=True)

LC='#26a69a'; SC='#ef5350'; NC='#FF8C00'
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'
C_TREND='rgba(255,0,0,0.08)'; C_MR='rgba(0,255,0,0.05)'

HORIZONS = ['2min', '3min', '5min']
H_COLORS = {'2min':'#4CAF50','3min':'#2196F3','5min':'#9C27B0'}
# Panel y-domains: 2min=[0.22,0.33], 3min=[0.11,0.22], 5min=[0.00,0.11]
PANEL = {'2min':('x3','y3',0.22,0.33),'3min':('x4','y4',0.11,0.22),'5min':('x5','y5',0.00,0.11)}

def build_hud(preds_path=None, day_str=None, max_pts=12000):
    if preds_path is None:
        files = sorted(MODEL_DIR.glob('BTCUSD_v6_preds_*.csv'))
        if not files: print("❌ No v6 preds!"); return None
        preds_path = files[-1]
    print(f"  Loading: {preds_path.name}...")
    df = pd.read_csv(preds_path, index_col=0, parse_dates=True)
    if day_str is None: day_str = df.index[-1].strftime('%Y-%m-%d')
    day = pd.Timestamp(day_str); nxt = day + pd.Timedelta(days=1)
    sub = df.loc[(df.index >= day) & (df.index < nxt)]
    if len(sub) == 0: print(f"❌ No data for {day_str}!"); return None
    if len(sub) > max_pts: sub = sub.iloc[::max(1, len(sub)//max_pts)]
    n = len(sub); print(f"  {day_str}: {n:,} pts")

    # Data prep
    ts = [t.strftime('%Y-%m-%d %H:%M:%S') for t in sub.index]
    px = sub['price'].round(2).tolist()
    has_ohlc = all(c in sub.columns for c in ['open','high','low','close'])
    o_=sub['open'].round(2).tolist() if has_ohlc else None
    hi_=sub['high'].round(2).tolist() if has_ohlc else None
    lo_=sub['low'].round(2).tolist() if has_ohlc else None
    cl_=sub['close'].round(2).tolist() if has_ohlc else None
    noise = sub['noise_level'].round(5).tolist() if 'noise_level' in sub.columns else [0]*n

    # Regime segments
    regime_segs = []
    if 'regime' in sub.columns:
        regime = sub['regime'].tolist(); cur_r=regime[0]; cur_s=0
        for i in range(1,len(regime)):
            if regime[i]!=cur_r: regime_segs.append((cur_s,i,cur_r)); cur_s=i; cur_r=regime[i]
        regime_segs.append((cur_s,len(regime),cur_r))

    # Per-horizon data
    h_data = {}
    for h in HORIZONS:
        pL=sub[f'p_long_{h}'].fillna(0).round(4).tolist() if f'p_long_{h}' in sub.columns else [0]*n
        pS=sub[f'p_short_{h}'].fillna(0).round(4).tolist() if f'p_short_{h}' in sub.columns else [0]*n
        pN=sub[f'p_noise_{h}'].fillna(0).round(4).tolist() if f'p_noise_{h}' in sub.columns else [0]*n
        sig=sub[f'signal_{h}'].tolist() if f'signal_{h}' in sub.columns else [0]*n
        lt=sub[f'long_thr_{h}'].round(4).tolist() if f'long_thr_{h}' in sub.columns else [.5]*n
        st=sub[f'short_thr_{h}'].round(4).tolist() if f'short_thr_{h}' in sub.columns else [.5]*n
        h_data[h]={'pL':pL,'pS':pS,'pN':pN,'sig':sig,'lt':lt,'st':st,
                    'lt_avg':float(np.mean(lt)),'st_avg':float(np.mean(st)),
                    'nL':sum(1 for s in sig if s==1),'nS':sum(1 for s in sig if s==-1)}

    sig_main = h_data['2min']['sig']
    lts=[ts[i] for i in range(n) if sig_main[i]==1]
    lpx=[round(px[i]*0.9997,2) for i in range(n) if sig_main[i]==1]
    sts=[ts[i] for i in range(n) if sig_main[i]==-1]
    spx=[round(px[i]*1.0003,2) for i in range(n) if sig_main[i]==-1]

    return _gen_html(ts,px,o_,hi_,lo_,cl_,noise,regime_segs,h_data,lts,lpx,sts,spx,n,day_str)

def _gen_html(ts,px,o_,hi_,lo_,cl_,noise,regime_segs,h_data,lts,lpx,sts,spx,n,day_str):
    j=json.dumps; js='<script>\n'
    js+=f'var ts={j(ts)},px={j(px)},noise={j(noise)};\n'
    if o_: js+=f'var o_={j(o_)},hi_={j(hi_)},lo_={j(lo_)},cl_={j(cl_)};\n'
    for h in HORIZONS:
        d=h_data[h]
        js+=f'var pL_{h}={j(d["pL"])},pS_{h}={j(d["pS"])},pN_{h}={j(d["pN"])};\n'
        js+=f'var lt_{h}={j(d["lt"])},st_{h}={j(d["st"])};\n'

    js+='(function(){\nvar data=[];\n'
    # Candlestick
    if o_:
        js+=f'data.push({{x:ts,open:o_,high:hi_,low:lo_,close:cl_,type:"candlestick",increasing:{{line:{{color:"{LC}"}}}},decreasing:{{line:{{color:"{SC}"}}}},name:"OHLC",xaxis:"x",yaxis:"y"}});\n'
    else:
        js+=f'data.push({{x:ts,y:px,type:"scatter",mode:"lines",line:{{color:"#00d2ff",width:1}},name:"Price",xaxis:"x",yaxis:"y"}});\n'
    # Signal markers
    js+=f'data.push({{x:{j(lts)},y:{j(lpx)},type:"scatter",mode:"markers",marker:{{symbol:"triangle-up",color:"{LC}",size:8}},name:"Long({len(lts)})",xaxis:"x",yaxis:"y"}});\n'
    js+=f'data.push({{x:{j(sts)},y:{j(spx)},type:"scatter",mode:"markers",marker:{{symbol:"triangle-down",color:"{SC}",size:8}},name:"Short({len(sts)})",xaxis:"x",yaxis:"y"}});\n'

    # 3 horizon sub-panels
    for h in HORIZONS:
        xa,ya,y0,y1=PANEL[h]
        js+=f'data.push({{x:ts,y:pL_{h},type:"scatter",mode:"lines",line:{{color:"{LC}",width:1.5}},name:"P(L) {h}",xaxis:"{xa}",yaxis:"{ya}"}});\n'
        js+=f'data.push({{x:ts,y:pS_{h},type:"scatter",mode:"lines",line:{{color:"{SC}",width:1.5}},name:"P(S) {h}",xaxis:"{xa}",yaxis:"{ya}"}});\n'
        js+=f'data.push({{x:ts,y:pN_{h},type:"scatter",mode:"lines",line:{{color:"{NC}",width:1,dash:"dot"}},name:"P(N) {h}",xaxis:"{xa}",yaxis:"{ya}"}});\n'

    # Shapes: regime bg + threshold lines
    shapes=''
    for s,e,r in regime_segs:
        if r=='trending': shapes+=f'{{type:"rect",xref:"x",yref:"y domain",x0:ts[{s}],x1:ts[{min(e-1,len(ts)-1)}],y0:0,y1:1,fillcolor:"{C_TREND}",line:{{width:0}}}},'
    for h in HORIZONS:
        xa,ya,y0,y1=PANEL[h]; d=h_data[h]
        shapes+=f'{{type:"line",xref:"{xa} domain",yref:"{ya}",x0:0,x1:1,y0:{d["lt_avg"]:.4f},y1:{d["lt_avg"]:.4f},line:{{color:"{LC}",width:1,dash:"dash"}}}},'
        shapes+=f'{{type:"line",xref:"{xa} domain",yref:"{ya}",x0:0,x1:1,y0:{d["st_avg"]:.4f},y1:{d["st_avg"]:.4f},line:{{color:"{SC}",width:1,dash:"dash"}}}},'
    if shapes.endswith(','): shapes=shapes[:-1]

    # Annotations
    anns=f'{{font:{{size:15}},showarrow:false,text:"BTCUSD Scalper v6 — {day_str}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}},'
    for h in HORIZONS:
        _,ya,y0,y1=PANEL[h]; d=h_data[h]
        anns+=f'{{font:{{size:11,color:"{H_COLORS[h]}"}},showarrow:false,text:"{h}: L▲={d["nL"]:,} S▼={d["nS"]:,} | thr_L={d["lt_avg"]:.3f} thr_S={d["st_avg"]:.3f}",x:0.5,xanchor:"center",xref:"paper",y:{y1},yanchor:"bottom",yref:"paper"}},'
    if anns.endswith(','): anns=anns[:-1]

    # Layout
    js+=f'var layout={{showlegend:true,legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",font:{{color:"{TC}",size:9}}}},'
    js+=f'xaxis:{{domain:[0,1],anchor:"y",matches:"x3",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},'
    js+=f'yaxis:{{domain:[0.35,1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},'
    for h in HORIZONS:
        xa,ya,y0,y1=PANEL[h]
        showtl='false' if h!='5min' else 'true'
        match='matches:"x3",' if h!='5min' else ''
        js+=f'{xa}:{{domain:[0,1],anchor:"{ya}",{match}showticklabels:{showtl},gridcolor:"{GC}"}},'
        js+=f'{ya}:{{domain:[{y0},{y1}],anchor:"{xa}",range:[0,1],gridcolor:"{GC}"}},'
    js+=f'shapes:[{shapes}],annotations:[{anns}],'
    js+=f'plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},'
    js+=f'margin:{{l:55,r:80,t:25,b:30}},height:950,hovermode:"x unified",dragmode:"zoom"}};'
    js+='Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n})();\n</script>'

    # Info bar
    noise_mean=float(np.mean(noise))
    parts=[f'Noise:{noise_mean:.4f}']
    for h in HORIZONS:
        d=h_data[h]; parts.append(f'{h}: L▲={d["nL"]:,} S▼={d["nS"]:,} @thr {d["lt_avg"]:.3f}/{d["st_avg"]:.3f}')
    info=' │ '.join(parts)

    html=f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>BTCUSD Scalper HUD v6 — {day_str}</title>
<script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script>
<style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:#00d2ff;text-align:center}}</style></head><body>
<div id="chart"></div><div id="info">📊 {info}</div>{js}</body></html>'''

    out=CHART_DIR/f'BTCUSD_hud_v6_{day_str}.html'
    with open(out,'w') as f: f.write(html)
    print(f"  ✅ {out.name} ({len(html)//1024}KB)")
    return out

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Scalper HUD v6 — 3-Horizon Dashboard')
    p.add_argument('--date', default=None, help='YYYY-MM-DD')
    p.add_argument('--max-points', type=int, default=12000)
    p.add_argument('--preds', default=None, help='Path to preds CSV')
    a = p.parse_args()
    build_hud(preds_path=a.preds, day_str=a.date, max_pts=a.max_points)