#!/usr/bin/env python3
"""v6 Chart — Candlestick + P(Long) P(Short) P(Noise) in subwindow — TEMPLATE"""
import json, numpy as np, pandas as pd
from pathlib import Path
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts'); CHART_DIR.mkdir(exist_ok=True)
LC='#228B22';SC='#B22222';NC='#FF8C00';BC='#00d2ff';BG='rgb(17,17,17)';GC='#283442';TC='#f2f5fa'

def gen_chart(preds_path, day_str, max_pts=15000):
    print(f"📊 {preds_path.name}")
    df = pd.read_csv(preds_path, index_col=0, parse_dates=True)
    for h in ['20s','1min','2min','3min','4min','5min']:
        df[f'p_long_{h}']=df[f'p_long_{h}'].fillna(0)
        df[f'p_short_{h}']=df[f'p_short_{h}'].fillna(0)
        if f'p_noise_{h}' in df.columns: df[f'p_noise_{h}']=df[f'p_noise_{h}'].fillna(0)
        else: df[f'p_noise_{h}']=0
    day=pd.Timestamp(day_str); nxt=day+pd.Timedelta(days=1)
    sub=df.loc[(df.index>=day)&(df.index<nxt)]
    if len(sub)>max_pts: sub=sub.iloc[::max(1,len(sub)//max_pts)]
    
    has_ohlc = 'open' in sub.columns and 'high' in sub.columns and 'low' in sub.columns
    
    for h in ['20s','1min','2min','3min','4min','5min']:
        n=len(sub); ts=[t.strftime('%Y-%m-%d %H:%M:%S') for t in sub.index]
        px=sub['price'].round(2).tolist()
        pL=sub[f'p_long_{h}'].round(4).tolist(); pS=sub[f'p_short_{h}'].round(4).tolist()
        pN=sub[f'p_noise_{h}'].round(4).tolist(); sig=sub[f'signal_{h}'].tolist()
        lts=[ts[i] for i in range(n) if sig[i]==1]; lpx=[round(px[i]*0.9997,2) for i in range(n) if sig[i]==1]
        sts=[ts[i] for i in range(n) if sig[i]==-1]; spx=[round(px[i]*1.0003,2) for i in range(n) if sig[i]==-1]
        nL=len(lts); nS=len(sts)
        j=json.dumps; js='<script>\n'
        js+=f'var ts={j(ts)},px={j(px)},pL={j(pL)},pS={j(pS)},pN={j(pN)};\n'
        js+=f'var lts={j(lts)},lpx={j(lpx)},sts={j(sts)},spx={j(spx)};\n'
        js+='(function(){\nvar data=[];\n'
        if has_ohlc:
            o_=sub['open'].round(2).tolist(); hi_=sub['high'].round(2).tolist()
            lo_=sub['low'].round(2).tolist(); cl_=sub['close'].round(2).tolist()
            js+=f'var o_={j(o_)},hi_={j(hi_)},lo_={j(lo_)},cl_={j(cl_)};\n'
            js+=f'data.push({{x:ts,open:o_,high:hi_,low:lo_,close:cl_,type:"candlestick",increasing:{{line:{{color:"#26a69a"}}}},decreasing:{{line:{{color:"#ef5350"}}}},name:"OHLC",xaxis:"x",yaxis:"y"}});\n'
        else:
            js+=f'data.push({{x:ts,y:px,type:"scatter",mode:"lines",line:{{color:"{BC}",width:1}},name:"Price",xaxis:"x",yaxis:"y"}});\n'
        js+=f'data.push({{x:lts,y:lpx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-up",color:"{LC}",size:8}},name:"Long({nL})",xaxis:"x",yaxis:"y"}});\n'
        js+=f'data.push({{x:sts,y:spx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-down",color:"{SC}",size:8}},name:"Short({nS})",xaxis:"x",yaxis:"y"}});\n'
        js+=f'data.push({{x:ts,y:pL,type:"scatter",mode:"lines",line:{{color:"{LC}",width:2}},name:"P(Long)",xaxis:"x2",yaxis:"y2"}});\n'
        js+=f'data.push({{x:ts,y:pS,type:"scatter",mode:"lines",line:{{color:"{SC}",width:2}},name:"P(Short)",xaxis:"x2",yaxis:"y2"}});\n'
        js+=f'data.push({{x:ts,y:pN,type:"scatter",mode:"lines",line:{{color:"{NC}",width:2,dash:"dot"}},name:"P(Noise)",xaxis:"x2",yaxis:"y2"}});\n'
        js+=f'var layout={{showlegend:true,legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",font:{{color:"{TC}",size:10}}}},xaxis:{{domain:[0,1],anchor:"y",matches:"x2",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},yaxis:{{domain:[0.32,1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},xaxis2:{{domain:[0,1],anchor:"y2",gridcolor:"{GC}"}},yaxis2:{{domain:[0,0.291],anchor:"x2",range:[0,1],gridcolor:"{GC}",title:{{text:"Probability",font:{{color:"{TC}"}}}}}},shapes:[{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:0.5,y1:0.5,line:{{color:"rgba(255,255,255,0.3)",width:1,dash:"dash"}}}}],annotations:[{{font:{{size:16}},showarrow:false,text:"BTCUSD v6 {h}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}}],plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},margin:{{l:55,r:80,t:25,b:40}},height:900,hovermode:"x unified",dragmode:"zoom"}};\n'
        js+='Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n})();\n</script>'
        chart_type = "Candlestick" if has_ohlc else "Line"
        html=f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>BTCUSD v6 {h}</title><script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script><style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:{BC};text-align:center}}</style></head><body><div id="chart"></div><div id="info">v6 $0.5M | {h} | {chart_type} | L={nL} S={nS}</div>{js}</body></html>'
        out=CHART_DIR/f'BTCUSD_v6_{h}_{day_str}.html'
        with open(out,'w') as f: f.write(html)
        print(f"  ✅ {out.name} ({len(html)//1024}KB) [{chart_type}]")

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--date',default=None); a=p.parse_args()
    files=sorted(MODEL_DIR.glob('BTCUSD_v6_preds_*.csv'))
    if not files: print("❌ No v6 preds"); raise SystemExit(1)
    if a.date is None:
        df=pd.read_csv(files[-1],index_col=0,parse_dates=True,nrows=10)
        a.date=df.index[-1].strftime('%Y-%m-%d')
    gen_chart(files[-1], day_str=a.date)