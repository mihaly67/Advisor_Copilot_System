#!/usr/bin/env python3
"""Regime-aware 3-row chart: Price + Hurst/Regime + P(L)-P(S)/P(N)"""
import json, numpy as np, pandas as pd
from pathlib import Path
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts'); CHART_DIR.mkdir(exist_ok=True)
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'

def gen_regime(preds_path, day_str, max_pts=12000):
    df = pd.read_csv(preds_path, index_col=0, parse_dates=True)
    day=pd.Timestamp(day_str); nxt=day+pd.Timedelta(days=1)
    sub=df.loc[(df.index>=day)&(df.index<nxt)]
    if len(sub)>max_pts: sub=sub.iloc[::max(1,len(sub)//max_pts)]
    
    H=['20s','1min','2min','3min','4min','5min']
    ts=[t.strftime('%Y-%m-%d %H:%M:%S') for t in sub.index]
    px=sub['price'].round(2).tolist()
    has_ohlc='open' in sub.columns
    j=json.dumps; js='<script>\n'
    js+=f'var ts={j(ts)},px={j(px)};\n'
    if has_ohlc:
        o_=sub['open'].round(2).tolist(); hi_=sub['high'].round(2).tolist()
        lo_=sub['low'].round(2).tolist(); cl_=sub['close'].round(2).tolist()
        js+=f'var o_={j(o_)},hi_={j(hi_)},lo_={j(lo_)},cl_={j(cl_)};\n'
    
    hurst=sub['hurst'].round(3).tolist() if 'hurst' in sub.columns else [0.5]*len(sub)
    regime_num=[{'trending':1,'mean_rev':-1,'neutral':0}.get(r,0) for r in sub['regime'].tolist()] if 'regime' in sub.columns else [0]*len(sub)
    js+=f'var hurst={j(hurst)},regime_num={j(regime_num)};\n'
    
    pN_cols=[f'p_noise_{h}' for h in H if f'p_noise_{h}' in sub.columns]
    pN_avg=sub[pN_cols].mean(axis=1).round(4).tolist() if pN_cols else [0]*len(sub)
    js+=f'var pN_avg={j(pN_avg)};\n'
    
    sig20=sub['signal_20s'].tolist()
    pL20=sub['p_long_20s'].round(4).tolist()
    pS20=sub['p_short_20s'].round(4).tolist()
    js+=f'var sig20={j(sig20)},pL20={j(pL20)},pS20={j(pS20)};\n'
    
    js+='(function(){\nvar data=[];\n'
    if has_ohlc:
        js+=f'data.push({{x:ts,open:o_,high:hi_,low:lo_,close:cl_,type:"candlestick",increasing:{{line:{{color:"#26a69a"}}}},decreasing:{{line:{{color:"#ef5350"}}}},name:"OHLC",xaxis:"x",yaxis:"y"}});\n'
    
    lts=[ts[i] for i in range(len(sig20)) if sig20[i]==1]
    lpx=[round(px[i]*0.9997,2) for i in range(len(sig20)) if sig20[i]==1]
    sts=[ts[i] for i in range(len(sig20)) if sig20[i]==-1]
    spx=[round(px[i]*1.0003,2) for i in range(len(sig20)) if sig20[i]==-1]
    js+=f'data.push({{x:{j(lts)},y:{j(lpx)},type:"scatter",mode:"markers",marker:{{symbol:"triangle-up",color:"#228B22",size:8}},name:"Long({len(lts)})",xaxis:"x",yaxis:"y"}});\n'
    js+=f'data.push({{x:{j(sts)},y:{j(spx)},type:"scatter",mode:"markers",marker:{{symbol:"triangle-down",color:"#B22222",size:8}},name:"Short({len(sts)})",xaxis:"x",yaxis:"y"}});\n'
    
    js+=f'data.push({{x:ts,y:hurst,type:"scatter",mode:"lines",line:{{color:"#FFD700",width:2}},name:"Hurst",xaxis:"x2",yaxis:"y2"}});\n'
    js+=f'data.push({{x:ts,y:regime_num,type:"scatter",mode:"lines",line:{{color:"#FF4444",width:1,dash:"dot"}},name:"Regime(+1=T,-1=MR)",xaxis:"x2",yaxis:"y2"}});\n'
    
    diff20=[round(pL20[i]-pS20[i],4) for i in range(len(pL20))]
    js+=f'data.push({{x:ts,y:pN_avg,type:"scatter",mode:"lines",line:{{color:"#FF8C00",width:2,dash:"dot"}},name:"P(Noise)",xaxis:"x3",yaxis:"y3"}});\n'
    js+=f'data.push({{x:ts,y:{j(diff20)},type:"scatter",mode:"lines",line:{{color:"#00d2ff",width:1}},name:"P(L)-P(S) 20s",xaxis:"x3",yaxis:"y3"}});\n'
    
    js+=f'var layout={{showlegend:true,legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",font:{{color:"{TC}",size:9}}}},xaxis:{{domain:[0,1],anchor:"y",matches:"x3",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},yaxis:{{domain:[0.45,1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},xaxis2:{{domain:[0,1],anchor:"y2",matches:"x3",showticklabels:false,gridcolor:"{GC}"}},yaxis2:{{domain:[0.25,0.42],anchor:"x2",range:[-1.5,1.5],gridcolor:"{GC}",title:{{text:"Hurst/Regime",font:{{color:"{TC}"}}}}}},xaxis3:{{domain:[0,1],anchor:"y3",gridcolor:"{GC}"}},yaxis3:{{domain:[0,0.22],anchor:"x3",gridcolor:"{GC}",title:{{text:"P(L)-P(S) / P(N)",font:{{color:"{TC}"}}}}}},shapes:[{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:0.5,y1:0.5,line:{{color:"rgba(255,255,0,0.4)",width:1,dash:"dash"}}}},{{type:"line",xref:"x3 domain",yref:"y3",x0:0,x1:1,y0:0,y1:0,line:{{color:"rgba(255,255,255,0.3)",width:1,dash:"dash"}}}}],annotations:[{{font:{{size:16}},showarrow:false,text:"v6.2 Regime-Filter — {day_str}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}}],plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},margin:{{l:55,r:80,t:25,b:40}},height:1000,hovermode:"x unified",dragmode:"zoom"}};\n'
    js+='Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n})();\n</script>'
    
    n_trend=(sub['regime']=='trending').sum() if 'regime' in sub.columns else 0
    n_mr=(sub['regime']=='mean_rev').sum() if 'regime' in sub.columns else 0
    info=f'v6.2 | {day_str} | Hurst+Regime | Trending={n_trend} MR={n_mr} | L={len(lts)} S={len(sts)}'
    html=f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>v6.2 Regime {day_str}</title><script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script><style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:#00d2ff;text-align:center}}</style></head><body><div id="chart"></div><div id="info">{info}</div>{js}</body></html>'
    out=CHART_DIR/f'BTCUSD_v6_regime_{day_str}.html'
    with open(out,'w') as f: f.write(html)
    print(f"  ✅ {out.name} ({len(html)//1024}KB)")

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--date',required=True); a=p.parse_args()
    files=sorted(MODEL_DIR.glob('BTCUSD_v6_preds_*.csv'))
    gen_regime(files[-1], day_str=a.date)
