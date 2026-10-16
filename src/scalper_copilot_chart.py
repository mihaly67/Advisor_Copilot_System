#!/usr/bin/env python3
"""
Scalper Copilot v4.0 — 2min Chart 1 nap (Plotly standalone)
Template: live_forward_test_results_20260813_SL1.html

FELSŐ (68%): Candlestick + Long▲ Short▼ + zaj sáv
ALSÓ (29%): P(Long) erdőzöld + P(Short) téglavörös + küszöb + zaj
"""
import json, numpy as np, pandas as pd
from pathlib import Path

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts')
DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
CHART_DIR.mkdir(parents=True, exist_ok=True)

LC = '#228B22'  # ForestGreen (Long)
SC = '#B22222'  # BrickRed (Short)
NC = '#888888'  # Noise gray
BG = 'rgb(17,17,17)'; GC = '#283442'; TC = '#f2f5fa'


def find_v4(instrument='BTCUSD'):
    metas = sorted(MODEL_DIR.glob(f'{instrument}_v4_meta_*.json'))
    if not metas: return None
    with open(metas[-1]) as f: meta = json.load(f)
    preds = sorted(MODEL_DIR.glob(f'{instrument}_v4_preds_*.csv'))
    r = {'meta': meta}
    if preds: r['preds'] = preds[-1]
    return r


def load_ohlc(day_str):
    path = DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
    print(f"  OHLC: {path.name}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp',
                     usecols=['Timestamp', 'Bid', 'Ask'])
    df.columns = [c.lower() for c in df.columns]
    day = pd.Timestamp(day_str); nxt = day + pd.Timedelta(days=1)
    df = df.loc[(df.index >= day) & (df.index < nxt)]
    if len(df) == 0: return None
    mid = ((df['bid'] + df['ask']) / 2).to_frame('mid')
    ohlc = mid['mid'].resample('1min').ohlc().dropna()
    print(f"    {len(ohlc)} candles")
    return ohlc


def build_chart(instrument='BTCUSD', date_str=None, max_pts=8000):
    """1 nap chart — template struktúrával."""
    v4 = find_v4(instrument)
    if not v4: print("Nincs v4 modell!"); return None
    meta = v4['meta']

    preds_all = pd.read_csv(v4['preds'], index_col=0, parse_dates=True)
    if date_str is None: date_str = preds_all.index[0].strftime('%Y-%m-%d')
    day = pd.Timestamp(date_str); nxt = day + pd.Timedelta(days=1)
    preds = preds_all.loc[(preds_all.index >= day) & (preds_all.index < nxt)]
    if len(preds) == 0: print(f"Nincs adat {date_str}!"); return None
    if len(preds) > max_pts: preds = preds.iloc[::len(preds)//max_pts]

    ohlc = load_ohlc(date_str)
    n = len(preds)
    ts = [t.strftime('%Y-%m-%d %H:%M:%S') for t in preds.index]
    px = preds['price'].round(2).tolist()
    noise = preds['noise_level'].round(5).tolist()
    noise_mean = float(np.mean(noise))

    # 2min adatok
    pl = preds['p_long_2min'].round(4).tolist()
    ps = preds['p_short_2min'].round(4).tolist()
    lt = preds['long_thr_2min'].round(4).tolist() if 'long_thr_2min' in preds.columns else [0.5]*n
    st = preds['short_thr_2min'].round(4).tolist() if 'short_thr_2min' in preds.columns else [0.5]*n
    sig = preds['signal_2min'].tolist() if 'signal_2min' in preds.columns else [0]*n
    lt_avg = float(np.mean(lt)); st_avg = float(np.mean(st))

    # Jelzés markerek
    lts = [ts[i] for i in range(n) if sig[i]==1]
    lpx = [round(px[i]*0.9997,2) for i in range(n) if sig[i]==1]
    sts = [ts[i] for i in range(n) if sig[i]==-1]
    spx = [round(px[i]*1.0003,2) for i in range(n) if sig[i]==-1]
    nL = len(lts); nS = len(sts)

    h = meta['horizons'].get('2min', {})

    # HTML generálás
    html = _gen_html(instrument, date_str, ts, px, noise, pl, ps, lt, st,
                     lts, lpx, sts, spx, nL, nS, lt_avg, st_avg, noise_mean,
                     ohlc, h, meta)
    out = CHART_DIR / f'{instrument}_copilot_v4_{date_str}.html'
    with open(out, 'w') as f: f.write(html)
    print(f"✅ {out} ({len(html)//1024}KB)")
    return out


def _gen_html(instrument, day, ts, px, noise, pl, ps, lt, st,
              lts, lpx, sts, spx, nL, nS, lt_avg, st_avg, noise_mean,
              ohlc, h, meta):
    j = json.dumps
    js = '<script>\n'
    js += f'var ts={j(ts)},px={j(px)},noise={j(noise)};\n'
    js += f'var pL={j(pl)},pS={j(ps)},lThr={j(lt)},sThr={j(st)};\n'
    js += f'var lts={j(lts)},lpx={j(lpx)},sts={j(sts)},spx={j(spx)};\n'
    if ohlc is not None and len(ohlc) > 0:
        oT = [t.strftime('%Y-%m-%d %H:%M:%S') for t in ohlc.index]
        js += f'var oT={j(oT)},oO={j(ohlc["open"].round(2).tolist())};\n'
        js += f'var oH={j(ohlc["high"].round(2).tolist())},oL={j(ohlc["low"].round(2).tolist())},oC={j(ohlc["close"].round(2).tolist())};\n'

    js += '(function(){\nvar data=[];\n'
    # Candlestick
    if ohlc is not None and len(ohlc) > 0:
        js += f'data.push({{x:oT,open:oO,high:oH,low:oL,close:oC,type:"candlestick",increasing:{{line:{{color:"{LC}"}}}},decreasing:{{line:{{color:"{SC}"}}}},name:"OHLC",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>O:%{{open:.2f}} H:%{{high:.2f}} L:%{{low:.2f}} C:%{{close:.2f}}<extra></extra>"}});\n'
    else:
        js += f'data.push({{x:ts,y:px,type:"scatter",mode:"lines",line:{{color:"#00d2ff",width:1}},name:"Price",xaxis:"x",yaxis:"y"}});\n'
    # Markerek
    js += f'data.push({{x:lts,y:lpx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-up",color:"{LC}",size:8,opacity:0.8}},name:"Long ▲ ({nL})",xaxis:"x",yaxis:"y"}});\n'
    js += f'data.push({{x:sts,y:spx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-down",color:"{SC}",size:8,opacity:0.8}},name:"Short ▼ ({nS})",xaxis:"x",yaxis:"y"}});\n'
    # Zaj sáv
    js += 'var nU=[],nD=[];for(var i=0;i<px.length;i++){var nn=noise[i]*px[i];nU.push(px[i]+nn);nD.push(px[i]-nn);}\n'
    js += f'data.push({{x:ts.concat(ts.slice().reverse()),y:nU.concat(nD.slice().reverse()),type:"scatter",fill:"toself",fillcolor:"rgba(136,136,136,0.08)",line:{{color:"transparent"}},name:"Noise ±ATR",xaxis:"x",yaxis:"y",showlegend:true}});\n'
    # P(Long) erdőzöld
    js += f'data.push({{x:ts,y:pL,type:"scatter",mode:"lines",line:{{color:"{LC}",width:2}},name:"P(Long)",xaxis:"x2",yaxis:"y2",fill:"tozeroy",fillcolor:"rgba(34,139,34,0.08)",hovertemplate:"%{{x}}<br>P(L)=%{{y:.3f}}<extra></extra>"}});\n'
    # P(Short) téglavörös
    js += f'data.push({{x:ts,y:pS,type:"scatter",mode:"lines",line:{{color:"{SC}",width:2}},name:"P(Short)",xaxis:"x2",yaxis:"y2",hovertemplate:"%{{x}}<br>P(S)=%{{y:.3f}}<extra></extra>"}});\n'
    return _wrap(js, instrument, day, lt_avg, st_avg, noise_mean, h, nL, nS)


def _wrap(js, instrument, day, lt_avg, st_avg, noise_mean, h, nL, nS):
    la = h.get('long_auc',0); sa = h.get('short_auc',0)
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
    js += f'{{font:{{size:16}},showarrow:false,text:"{instrument} Scalper Copilot v4.0 — {day}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}},'
    js += f'{{font:{{size:16}},showarrow:false,text:"LightGBM 2min Probabilities",x:0.5,xanchor:"center",xref:"paper",y:0.291,yanchor:"bottom",yref:"paper"}},'
    js += f'{{showarrow:false,text:"Long Threshold ({lt_avg:.2f})",x:1,xanchor:"right",xref:"x2 domain",y:{lt_avg:.3f},yanchor:"bottom",yref:"y2",font:{{color:"{LC}",size:10}}}},'
    js += f'{{showarrow:false,text:"Short Threshold ({st_avg:.2f})",x:1,xanchor:"right",xref:"x2 domain",y:{st_avg:.3f},yanchor:"bottom",yref:"y2",font:{{color:"{SC}",size:10}}}},'
    js += f'{{showarrow:false,text:"Noise ({noise_mean:.4f})",x:1,xanchor:"right",xref:"x2 domain",y:{noise_mean:.3f},yanchor:"bottom",yref:"y2",font:{{color:"{NC}",size:10}}}}],\n'
    js += f'plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},'
    js += 'margin:{l:55,r:80,t:25,b:40},height:900,hovermode:"x unified",dragmode:"zoom"};\n'
    js += 'Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n'
    js += '})();\n</script>'
    info = f"Noise:{noise_mean:.4f} │ 2min: L={la:.3f}@{lt_avg:.2f} S={sa:.3f}@{st_avg:.2f} │ Long▲={nL} Short▼={nS}"
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{instrument} Copilot v4.0 — {day}</title>
<script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script>
<style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:#00d2ff;text-align:center}}</style></head><body>
<div id="chart"></div><div id="info">📊 {info}</div>{js}</body></html>'''


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Scalper Copilot v4.0 — 2min Chart (1 nap)')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--date', default=None, help='YYYY-MM-DD')
    p.add_argument('--max-points', type=int, default=8000)
    a = p.parse_args()
    build_chart(a.instrument, a.date, a.max_points)
