#!/usr/bin/env python3
"""
Scalper Copilot v5 — Multi-Horizon Chart + Contradictory Signal Analysis
Template: Plotly standalone dark theme, 2-panel (ár + probability)

Generates:
  1. Per-horizon charts (20s, 1min, 2min) with P(Long)/P(Short) overlay
  2. Contradictory signals chart (where horizontok disagree)
  3. Analysis summary (signal stats, contradiction rates, regime analysis)
"""
import json, sys, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts')
CHART_DIR.mkdir(parents=True, exist_ok=True)

LC = '#228B22'; SC = '#B22222'; NC = '#888888'
CC = '#FF6B35'; BC = '#00d2ff'
BG = 'rgb(17,17,17)'; GC = '#283442'; TC = '#f2f5fa'
HORIZONS = ['20s', '1min', '2min']

def load_preds(preds_path=None, instrument='BTCUSD'):
    if preds_path is None:
        files = sorted(MODEL_DIR.glob(f'{instrument}_v401_preds_*.csv'))
        if not files: print("❌ Nincs CSV!"); sys.exit(1)
        preds_path = files[-1]
    print(f"📊 Predikciók: {preds_path.name} ({preds_path.stat().st_size/1e6:.0f}MB)")
    df = pd.read_csv(preds_path, parse_dates=['timestamp'], index_col='timestamp')
    for h in HORIZONS:
        df[f'p_long_{h}'] = df[f'p_long_{h}'].fillna(0)
        df[f'p_short_{h}'] = df[f'p_short_{h}'].fillna(0)
    return df

def analyze_contradictions(df):
    print("\n" + "="*70)
    print("🔍 ELLENTÉTES PREDIKCIÓ ANALÍZIS")
    print("="*70)
    results = {}
    for h in HORIZONS:
        sig = df[f'signal_{h}']
        nL = (sig == 1).sum(); nS = (sig == -1).sum(); n0 = (sig == 0).sum()
        print(f"\n  {h}: Long={nL:,} Short={nS:,} None={n0:,} (össz={len(sig):,})")
        results[h] = {'long': int(nL), 'short': int(nS), 'none': int(n0)}
    pairs = [('20s','1min'), ('20s','2min'), ('1min','2min')]
    contradictions = {}; total_bars = len(df)
    for h1, h2 in pairs:
        s1 = df[f'signal_{h1}']; s2 = df[f'signal_{h2}']
        both = (s1 != 0) & (s2 != 0)
        opp = (s1 == -s2) & both
        same = (s1 == s2) & both
        one = ((s1 != 0) & (s2 == 0)) | ((s1 == 0) & (s2 != 0))
        no, ns, n1 = int(opp.sum()), int(same.sum()), int(one.sum())
        print(f"\n  {h1} vs {h2}:")
        print(f"    🚨 Ellentétes: {no:,} ({no/total_bars*100:.2f}%)")
        print(f"    ✅ Egyezés:    {ns:,} ({ns/total_bars*100:.2f}%)")
        print(f"    ⚡ Csak1 aktív: {n1:,} ({n1/total_bars*100:.2f}%)")
        contradictions[f'{h1}_vs_{h2}'] = {'opposite': no, 'same': ns, 'one_only': n1, 'opp_pct': no/total_bars*100}
    s20=df['signal_20s']; s1m=df['signal_1min']; s2m=df['signal_2min']
    all3 = (s20!=0)&(s1m!=0)&(s2m!=0)
    same3 = all3&(s20==s1m)&(s1m==s2m)
    contra3 = all3&((s20!=s1m)|(s1m!=s2m))
    print(f"\n  3-WAY: Mind3 aktív={all3.sum():,} Egyezik={same3.sum():,} Ellentmond={contra3.sum():,}")
    return results, contradictions

def _wrap_html(js, info, horizon, day_str):
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>BTCUSD Copilot v5 — {horizon} — {day_str or 'Full'}</title>
<script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script>
<style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:{BC};text-align:center}}</style></head><body>
<div id="chart"></div><div id="info">📊 {info}</div>{js}</body></html>'''

def _sub_df(df, day_str, max_pts):
    if day_str:
        day = pd.Timestamp(day_str); nxt = day + pd.Timedelta(days=1)
        sub = df.loc[(df.index >= day) & (df.index < nxt)]
    else: sub = df
    if len(sub) > max_pts: sub = sub.iloc[::max(1, len(sub)//max_pts)]
    return sub

def gen_horizon_chart(df, horizon, day_str=None, max_pts=12000, meta_auc=None, show_contra=False):
    sub = _sub_df(df, day_str, max_pts)
    if len(sub) == 0: print(f"  ⚠️ Nincs adat {day_str}"); return None
    n = len(sub)
    ts = [t.strftime('%Y-%m-%d %H:%M:%S') for t in sub.index]
    px = sub['price'].round(2).tolist()
    noise = sub['noise_level'].round(5).tolist()
    noise_mean = float(np.nanmean(noise))
    pl = sub[f'p_long_{horizon}'].round(4).tolist()
    ps = sub[f'p_short_{horizon}'].round(4).tolist()
    lt = sub[f'long_thr_{horizon}'].round(4).tolist() if f'long_thr_{horizon}' in sub.columns else [0.5]*n
    st = sub[f'short_thr_{horizon}'].round(4).tolist() if f'short_thr_{horizon}' in sub.columns else [0.5]*n
    sig = sub[f'signal_{horizon}'].tolist()
    lt_avg = float(np.nanmean(lt)); st_avg = float(np.nanmean(st))
    lts = [ts[i] for i in range(n) if sig[i]==1]
    lpx = [round(px[i]*0.9997,2) for i in range(n) if sig[i]==1]
    sts = [ts[i] for i in range(n) if sig[i]==-1]
    spx = [round(px[i]*1.0003,2) for i in range(n) if sig[i]==-1]
    nL = len(lts); nS = len(sts)
    cts=[]; cpx=[]
    if show_contra and horizon != '2min':
        other = '1min' if horizon == '20s' else '2min'
        osig = sub[f'signal_{other}'].tolist()
        for i in range(n):
            if sig[i]!=0 and osig[i]!=0 and sig[i]==-osig[i]: cts.append(ts[i]); cpx.append(round(px[i]*1.0006,2))
    j = json.dumps
    js = '<script>\n'
    js += f'var ts={j(ts)},px={j(px)},noise={j(noise)};\n'
    js += f'var pL={j(pl)},pS={j(ps)},lThr={j(lt)},sThr={j(st)};\n'
    js += f'var lts={j(lts)},lpx={j(lpx)},sts={j(sts)},spx={j(spx)};\n'
    if cts: js += f'var cts={j(cts)},cpx={j(cpx)};\n'
    js += '(function(){\nvar data=[];\n'
    js += f'data.push({{x:ts,y:px,type:"scatter",mode:"lines",line:{{color:"{BC}",width:1}},name:"Price",xaxis:"x",yaxis:"y"}});\n'
    js += f'data.push({{x:lts,y:lpx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-up",color:"{LC}",size:9,opacity:0.85}},name:"Long ▲ ({nL})",xaxis:"x",yaxis:"y"}});\n'
    js += f'data.push({{x:sts,y:spx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-down",color:"{SC}",size:9,opacity:0.85}},name:"Short ▼ ({nS})",xaxis:"x",yaxis:"y"}});\n'
    if cts: js += f'data.push({{x:cts,y:cpx,type:"scatter",mode:"markers",marker:{{symbol:"x",color:"{CC}",size:10,opacity:0.9}},name:"⚠️ Contra ({len(cts)})",xaxis:"x",yaxis:"y"}});\n'
    js += 'var nU=[],nD=[];for(var i=0;i<px.length;i++){var nn=noise[i]*px[i];nU.push(px[i]+nn);nD.push(px[i]-nn);}\n'
    js += f'data.push({{x:ts.concat(ts.slice().reverse()),y:nU.concat(nD.slice().reverse()),type:"scatter",fill:"toself",fillcolor:"rgba(136,136,136,0.06)",line:{{color:"transparent"}},name:"Noise",xaxis:"x",yaxis:"y",showlegend:true}});\n'
    js += f'data.push({{x:ts,y:pL,type:"scatter",mode:"lines",line:{{color:"{LC}",width:2}},name:"P(Long)",xaxis:"x2",yaxis:"y2",fill:"tozeroy",fillcolor:"rgba(34,139,34,0.12)"}});\n'
    js += f'data.push({{x:ts,y:pS,type:"scatter",mode:"lines",line:{{color:"{SC}",width:2}},name:"P(Short)",xaxis:"x2",yaxis:"y2",fill:"tozeroy",fillcolor:"rgba(178,34,34,0.12)"}});\n'
    auc_str = f"L={meta_auc[0]:.3f} S={meta_auc[1]:.3f}" if meta_auc else ""
    js += 'var layout={showlegend:true,\n'
    js += f'legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",bordercolor:"#444",font:{{color:"{TC}",size:10}}}},\n'
    js += f'xaxis:{{domain:[0,1],anchor:"y",matches:"x2",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},\n'
    js += f'yaxis:{{domain:[0.32,1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},\n'
    js += f'xaxis2:{{domain:[0,1],anchor:"y2",gridcolor:"{GC}"}},\n'
    js += f'yaxis2:{{domain:[0,0.291],anchor:"x2",range:[0,1],gridcolor:"{GC}",title:{{text:"Probability",font:{{color:"{TC}"}}}}}},\n'
    js += 'shapes:['
    js += f'{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:{lt_avg:.4f},y1:{lt_avg:.4f},line:{{color:"{LC}",width:1,dash:"dash"}}}},'
    js += f'{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:{st_avg:.4f},y1:{st_avg:.4f},line:{{color:"{SC}",width:1,dash:"dash"}}}},'
    js += f'{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:{noise_mean:.4f},y1:{noise_mean:.4f},line:{{color:"{NC}",width:1,dash:"dash"}}}}],\n'
    js += 'annotations:['
    js += f'{{font:{{size:16}},showarrow:false,text:"BTCUSD Scalper Copilot v5 — {horizon}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}},'
    js += f'{{font:{{size:14}},showarrow:false,text:"{horizon} Probabilities ({auc_str})",x:0.5,xanchor:"center",xref:"paper",y:0.291,yanchor:"bottom",yref:"paper"}}],\n'
    js += f'plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},\n'
    js += 'margin:{l:55,r:80,t:25,b:40},height:900,hovermode:"x unified",dragmode:"zoom"};\n'
    js += 'Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n'
    js += '})();\n</script>'
    info = f"Noise:{noise_mean:.4f} │ {horizon}: {auc_str} │ Long▲={nL} Short▼={nS}"
    if cts: info += f" ⚠️Contra={len(cts)}"
    return _wrap_html(js, info, horizon, day_str)

def gen_multi_horizon_chart(df, day_str=None, max_pts=12000):
    sub = _sub_df(df, day_str, max_pts)
    n = len(sub)
    ts = [t.strftime('%Y-%m-%d %H:%M:%S') for t in sub.index]
    px = sub['price'].round(2).tolist()
    j = json.dumps
    js = '<script>\n'
    js += f'var ts={j(ts)},px={j(px)};\n'
    for h in HORIZONS:
        js += f'var pL_{h}={j(sub[f"p_long_{h}"].round(4).tolist())};\n'
        js += f'var pS_{h}={j(sub[f"p_short_{h}"].round(4).tolist())};\n'
    s20 = sub['signal_20s'].tolist(); s1m = sub['signal_1min'].tolist(); s2m = sub['signal_2min'].tolist()
    c20_1 = [i for i in range(n) if s20[i]!=0 and s1m[i]!=0 and s20[i]==-s1m[i]]
    c20_2 = [i for i in range(n) if s20[i]!=0 and s2m[i]!=0 and s20[i]==-s2m[i]]
    c1_2 = [i for i in range(n) if s1m[i]!=0 and s2m[i]!=0 and s1m[i]==-s2m[i]]
    all_c = sorted(set(c20_1+c20_2+c1_2))
    cts = [ts[i] for i in all_c]; cpx = [round(px[i]*1.0008,2) for i in all_c]
    js += f'var cts={j(cts)},cpx={j(cpx)};\n'
    js += '(function(){\nvar data=[];\n'
    js += f'data.push({{x:ts,y:px,type:"scatter",mode:"lines",line:{{color:"{BC}",width:1}},name:"Price",xaxis:"x",yaxis:"y"}});\n'
    js += f'data.push({{x:cts,y:cpx,type:"scatter",mode:"markers",marker:{{symbol:"x",color:"{CC}",size:11,opacity:0.9,line:{{width:2}}}},name:"⚠️ Contra ({len(cts)})",xaxis:"x",yaxis:"y"}});\n'
    cL = ['#00FF00','#66FF66','#99FF99']; cS = ['#FF0000','#FF6666','#FF9999']
    for idx,h in enumerate(HORIZONS):
        js += f'data.push({{x:ts,y:pL_{h},type:"scatter",mode:"lines",line:{{color:"{cL[idx]}",width:{2-idx*0.5}}},name:"P(L) {h}",xaxis:"x2",yaxis:"y2"}});\n'
        js += f'data.push({{x:ts,y:pS_{h},type:"scatter",mode:"lines",line:{{color:"{cS[idx]}",width:{2-idx*0.5}}},name:"P(S) {h}",xaxis:"x2",yaxis:"y2"}});\n'
    js += 'var layout={showlegend:true,\n'
    js += f'legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.9)",font:{{color:"{TC}",size:10}}}},\n'
    js += f'xaxis:{{domain:[0,1],anchor:"y",matches:"x2",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},\n'
    js += f'yaxis:{{domain:[0.32,1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},\n'
    js += f'xaxis2:{{domain:[0,1],anchor:"y2",gridcolor:"{GC}"}},\n'
    js += f'yaxis2:{{domain:[0,0.291],anchor:"x2",range:[0,1],gridcolor:"{GC}",title:{{text:"Probability (all horizons)",font:{{color:"{TC}"}}}}}},\n'
    js += 'annotations:['
    js += f'{{font:{{size:16}},showarrow:false,text:"BTCUSD v5 Multi-Horizon",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}},'
    js += f'{{font:{{size:13}},showarrow:false,text:"⚠️ {len(all_c)} contra | {len(c20_1)}(20s⇄1m) {len(c20_2)}(20s⇄2m) {len(c1_2)}(1m⇄2m)",x:0.5,xanchor:"center",xref:"paper",y:0.291,yanchor:"bottom",yref:"paper"}}],\n'
    js += f'plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},\n'
    js += 'margin:{l:55,r:80,t:25,b:40},height:900,hovermode:"x unified",dragmode:"zoom"};\n'
    js += 'Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n'
    js += '})();\n</script>'
    info = f"⚠️ Contra: {len(all_c)} | 20s⇄1m={len(c20_1)} 20s⇄2m={len(c20_2)} 1m⇄2m={len(c1_2)}"
    return _wrap_html(js, info, 'multi', day_str)

def gen_contradiction_chart(df, max_pts=50000):
    sub = df if len(df) <= max_pts else df.iloc[::max(1,len(df)//max_pts)]
    sub = sub.copy(); sub['date'] = sub.index.date
    pairs = [('20s','1min'),('20s','2min'),('1min','2min')]
    daily = {}
    for h1,h2 in pairs:
        k = f'{h1}⇄{h2}'
        m = (sub[f'signal_{h1}']!=0)&(sub[f'signal_{h2}']!=0)&(sub[f'signal_{h1}']==-sub[f'signal_{h2}'])
        daily[k] = sub[m].groupby('date').size()
    dates = sorted(set(sub['date']))
    j = json.dumps; ts = [str(d) for d in dates]
    js = '<script>\n'; js += f'var ts={j(ts)};\n'
    colors = ['#FF6B35','#FFB347','#FF4444']
    for idx,(k,ser) in enumerate(daily.items()):
        js += f'var v{idx}={j([int(ser.get(d,0)) for d in dates])};\n'
    js += '(function(){\nvar data=[];\n'
    for idx,k in enumerate(daily.keys()):
        fill = '"tonexty"' if idx>0 else '"tozeroy"'
        js += f'data.push({{x:ts,y:v{idx},type:"scatter",mode:"lines",line:{{color:"{colors[idx]}",width:2}},stackgroup:"one",name:"{k}"}});\n'
    js += 'var layout={showlegend:true,\n'
    js += f'legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",font:{{color:"{TC}"}}}},\n'
    js += f'xaxis:{{gridcolor:"{GC}"}},yaxis:{{gridcolor:"{GC}",title:{{text:"Contradictions/day",font:{{color:"{TC}"}}}}}},\n'
    js += 'annotations:['
    js += f'{{font:{{size:16}},showarrow:false,text:"Daily Contradictory Signals by Horizon Pair",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}}],\n'
    js += f'plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},\n'
    js += 'margin:{l:60,r:30,t:30,b:40},height:500,hovermode:"x unified"};\n'
    js += 'Plotly.newPlot("chart",data,layout,{responsive:true});\n'
    js += '})();\n</script>'
    total = sum(v.sum() for v in daily.values())
    return _wrap_html(js, f"Total: {total:,}", 'contra', 'daily')

def main():
    import argparse
    p = argparse.ArgumentParser(description='Scalper Copilot v5 — Multi-Horizon Chart')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--date', default=None, help='YYYY-MM-DD')
    p.add_argument('--max-points', type=int, default=12000)
    a = p.parse_args()
    AUC = {'20s':(0.6858,0.5495), '1min':(0.5812,0.5675), '2min':(0.5479,0.5165)}
    df = load_preds(instrument=a.instrument)
    if a.date is None:
        a.date = df.index[-1].strftime('%Y-%m-%d')
        print(f"  Utolsó nap: {a.date}")
    sig_results, contra_results = analyze_contradictions(df)
    datestamp = datetime.now().strftime('%Y%m%d')
    for h in HORIZONS:
        html = gen_horizon_chart(df, h, day_str=a.date, max_pts=a.max_points, meta_auc=AUC.get(h), show_contra=True)
        if html:
            out = CHART_DIR / f'BTCUSD_copilot_v5_{h}_{a.date}.html'
            with open(out,'w') as f: f.write(html)
            print(f"  ✅ {out.name} ({len(html)//1024}KB)")
    html = gen_multi_horizon_chart(df, day_str=a.date, max_pts=a.max_points)
    if html:
        out = CHART_DIR / f'BTCUSD_copilot_v5_multi_{a.date}.html'
        with open(out,'w') as f: f.write(html)
        print(f"  ✅ {out.name} ({len(html)//1024}KB)")
    html = gen_contradiction_chart(df)
    if html:
        out = CHART_DIR / f'BTCUSD_copilot_v5_contradictions_{datestamp}.html'
        with open(out,'w') as f: f.write(html)
        print(f"  ✅ {out.name} ({len(html)//1024}KB)")
    print("\n" + "="*70)
    print("📋 V5 CHART ÖSSZEFOGLALÓ")
    print("="*70)
    for h in HORIZONS:
        s = sig_results[h]
        print(f"  {h}: Long▲={s['long']:,} Short▼={s['short']:,} None={s['none']:,}")
    for k,v in contra_results.items():
        print(f"  {k}: 🚨{v['opposite']:,} ({v['opp_pct']:.2f}%) ✅{v['same']:,} ⚡{v['one_only']:,}")
    print(f"\n  Charts: {CHART_DIR}/")
    for f in sorted(CHART_DIR.glob('BTCUSD_copilot_v5_*.html')):
        print(f"    📈 {f.name}")

if __name__ == '__main__':
    main()