#!/usr/bin/env python3
"""Multi-horizon summary chart — 6 horizons + regime overlay"""
import json, numpy as np, pandas as pd
from pathlib import Path
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts'); CHART_DIR.mkdir(exist_ok=True)
LC='#228B22';SC='#B22222';NC='#FF8C00';BG='rgb(17,17,17)';GC='#283442';TC='#f2f5fa'

def gen_multi(preds_path, day_str, max_pts=12000):
    df = pd.read_csv(preds_path, index_col=0, parse_dates=True)
    day=pd.Timestamp(day_str); nxt=day+pd.Timedelta(days=1)
    sub=df.loc[(df.index>=day)&(df.index<nxt)]
    if len(sub)>max_pts: sub=sub.iloc[::max(1,len(sub)//max_pts)]
    
    H=['20s','1min','2min','3min','4min','5min']
    ts=[t.strftime('%Y-%m-%d %H:%M:%S') for t in sub.index]
    px=sub['price'].round(2).tolist()
    has_ohlc='open' in sub.columns
    if has_ohlc:
        o_=sub['open'].round(2).tolist(); hi_=sub['high'].round(2).tolist()
        lo_=sub['low'].round(2).tolist(); cl_=sub['close'].round(2).tolist()
    
    j=json.dumps; js='<script>\n'
    js+=f'var ts={j(ts)},px={j(px)};\n'
    if has_ohlc:
        js+=f'var o_={j(o_)},hi_={j(hi_)},lo_={j(lo_)},cl_={j(cl_)};\n'
    
    # Regime colors for background shapes
    if 'regime' in sub.columns:
        regime=sub['regime'].tolist()
        # Build regime segments
        segs=[]; cur_r=regime[0]; cur_s=0
        for i in range(1,len(regime)):
            if regime[i]!=cur_r:
                segs.append((cur_s,i,cur_r)); cur_s=i; cur_r=regime[i]
        segs.append((cur_s,len(regime),cur_r))
        regime_colors={'trending':'rgba(255,0,0,0.08)','mean_rev':'rgba(0,255,0,0.05)','neutral':'rgba(128,128,128,0.03)'}
    
    # P(Noise) aggregated across horizons
    pN_cols=[f'p_noise_{h}' for h in H if f'p_noise_{h}' in sub.columns]
    if pN_cols:
        pN_avg=sub[pN_cols].mean(axis=1).round(4).tolist()
    else:
        pN_avg=[0]*len(sub)
    js+=f'var pN_avg={j(pN_avg)};\n'
    
    js+='(function(){\nvar data=[];\n'
    # Main price chart
    if has_ohlc:
        js+=f'data.push({{x:ts,open:o_,high:hi_,low:lo_,close:cl_,type:"candlestick",increasing:{{line:{{color:"#26a69a"}}}},decreasing:{{line:{{color:"#ef5350"}}}},name:"OHLC",xaxis:"x",yaxis:"y"}});\n'
    else:
        js+=f'data.push({{x:ts,y:px,type:"scatter",mode:"lines",line:{{color:"#00d2ff",width:1}},name:"Price",xaxis:"x",yaxis:"y"}});\n'
    
    # Signal markers (from 20s horizon)
    sig20=sub['signal_20s'].tolist()
    lts=[ts[i] for i in range(len(sig20)) if sig20[i]==1]
    lpx=[round(px[i]*0.9997,2) for i in range(len(sig20)) if sig20[i]==1]
    sts=[ts[i] for i in range(len(sig20)) if sig20[i]==-1]
    spx=[round(px[i]*1.0003,2) for i in range(len(sig20)) if sig20[i]==-1]
    js+=f'data.push({{x:{j(lts)},y:{j(lpx)},type:"scatter",mode:"markers",marker:{{symbol:"triangle-up",color:"{LC}",size:7}},name:"Long({len(lts)})",xaxis:"x",yaxis:"y"}});\n'
    js+=f'data.push({{x:{j(sts)},y:{j(spx)},type:"scatter",mode:"markers",marker:{{symbol:"triangle-down",color:"{SC}",size:7}},name:"Short({len(sts)})",xaxis:"x",yaxis:"y"}});\n'
    
    # Subchart: P(Noise) avg + per-horizon P(Long)-P(Short)
    js+=f'data.push({{x:ts,y:pN_avg,type:"scatter",mode:"lines",line:{{color:"{NC}",width:2,dash:"dot"}},name:"P(Noise) avg",xaxis:"x2",yaxis:"y2"}});\n'
    colors=['#4CAF50','#2196F3','#9C27B0','#FF9800','#795548','#607D8B']
    for i,h in enumerate(H):
        pL=sub[f'p_long_{h}'].fillna(0).round(4).tolist()
        pS=sub[f'p_short_{h}'].fillna(0).round(4).tolist()
        diff=[round(pL[j]-pS[j],4) for j in range(len(pL))]
        js+=f'data.push({{x:ts,y:{j(diff)},type:"scatter",mode:"lines",line:{{color:"{colors[i]}",width:1}},name:"P(L)-P(S) {h}",xaxis:"x2",yaxis:"y2"}});\n'
    
    # Layout
    shapes=''
    if 'regime' in sub.columns:
        for s,e,r in segs:
            if r=='trending':
                shapes+=f'{{type:"rect",xref:"x",yref:"y domain",x0:ts[{s}],x1:ts[{min(e-1,len(ts)-1)}],y0:0,y1:1,fillcolor:"rgba(255,0,0,0.08)",line:{{width:0}}}},'
    shapes+=f'{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:0,y1:0,line:{{color:"rgba(255,255,255,0.3)",width:1,dash:"dash"}}}}'
    
    js+=f'var layout={{showlegend:true,legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",font:{{color:"{TC}",size:9}}}},xaxis:{{domain:[0,1],anchor:"y",matches:"x2",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},yaxis:{{domain:[0.35,1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},xaxis2:{{domain:[0,1],anchor:"y2",gridcolor:"{GC}"}},yaxis2:{{domain:[0,0.32],anchor:"x2",gridcolor:"{GC}",title:{{text:"P(L)-P(S) / P(N)",font:{{color:"{TC}"}}}}}},shapes:[{shapes}],annotations:[{{font:{{size:16}},showarrow:false,text:"BTCUSD v6.2 Regime-Filter — {day_str}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}}],plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},margin:{{l:55,r:80,t:25,b:40}},height:900,hovermode:"x unified",dragmode:"zoom"}};\n'
    js+='Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n})();\n</script>'
    
    nL=len(lts); nS=len(sts)
    n_trend=(sub['regime']=='trending').sum() if 'regime' in sub.columns else 0
    n_mr=(sub['regime']=='mean_rev').sum() if 'regime' in sub.columns else 0
    info=f'v6.2 $0.5M | Candlestick | L={nL} S={nS} | Trending={n_trend} MR={n_mr}'
    html=f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>BTCUSD v6.2 Multi {day_str}</title><script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script><style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:#00d2ff;text-align:center}}</style></head><body><div id="chart"></div><div id="info">{info}</div>{js}</body></html>'
    out=CHART_DIR/f'BTCUSD_v6_multi_{day_str}.html'
    with open(out,'w') as f: f.write(html)
    print(f"  ✅ {out.name} ({len(html)//1024}KB)")

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--date',default=None); a=p.parse_args()
    files=sorted(MODEL_DIR.glob('BTCUSD_v6_preds_*.csv'))
    if not files: print("❌ No v6 preds"); raise SystemExit(1)
    if a.date is None:
        df=pd.read_csv(files[-1],index_col=0,parse_dates=True,nrows=10)
        a.date=df.index[-1].strftime('%Y-%m-%d')
    gen_multi(files[-1], day_str=a.date)
