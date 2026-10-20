#!/usr/bin/env python3
"""
V8 Chart — 5 Horizon (1-5 min), 1 nap HTML
FIXED: 1min OHLC from exam tick (folytonos candlestick)
       + dollar bar pred overlay (▲▼ signals)
FELSŐ (68%): Candlestick (1min OHLC) + Long▲ zöld + Short▼ piros
ALSÓ (29%): P(Long) görbe + küszöb vonalak (0.55 / 0.45)
"""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import load_ticks, make_dollar_bars, label_tbm, DATA_DIR, EXAM_DIR, DOLLAR_THR, SEED
from build_features_v8 import build_features_v8, FEATURES_V8_PRUNED
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts')
CHART_DIR.mkdir(parents=True, exist_ok=True)
LC='#228B22'; SC='#B22222'; NC='#888888'
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'
HORIZONS = [('1min',60),('2min',120),('3min',180),('4min',240),('5min',300)]
KEEP = [f for f in FEATURES_V8_PRUNED if f not in ('kill_zone','ema_d_5')]


def resample_1min(ticks):
    """Tick DataFrame -> 1min OHLC (folytonos, nem szigetes!)"""
    ohlc = ticks['price'].resample('1min').ohlc()
    ohlc = ohlc.dropna()
    return ohlc


def _gen_html(hname, day_str, ts, o_, hi_, lo_, cl_,
              pL, pS, lt_avg, st_avg, lts, lpx, sts, spx, n, nL, nS, auc_val):
    """FELSŐ: candlestick+▲▼ ALSÓ: P(Long) only"""
    js = '<script>(function(){\nvar ts='+json.dumps(ts)+';\nvar data=[];\n'
    # Candlestick
    js += 'data.push({x:ts,open:'+json.dumps(o_)+',high:'+json.dumps(hi_)+',low:'+json.dumps(lo_)+',close:'+json.dumps(cl_)
    js += f',type:"candlestick",increasing:{{line:{{color:"{LC}"}}}},decreasing:{{line:{{color:"{SC}"}}}},name:"Price",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>$%{{y:,.0f}}<extra></extra>"}});\n'
    # Long ▲
    if lts:
        js += f'data.push({{x:{json.dumps(lts)},y:{json.dumps(lpx)},type:"scatter",mode:"markers",marker:{{color:"{LC}",symbol:"triangle-up",size:10}},name:"Long▲",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>$%{{y:,.0f}} ▲LONG<extra></extra>"}});\n'
    # Short ▼
    if sts:
        js += f'data.push({{x:{json.dumps(sts)},y:{json.dumps(spx)},type:"scatter",mode:"markers",marker:{{color:"{SC}",symbol:"triangle-down",size:10}},name:"Short▼",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>$%{{y:,.0f}} ▼SHORT<extra></extra>"}});\n'
    # P(Long) erdőzöld
    js += f'data.push({{x:ts,y:{json.dumps(pL)},type:"scatter",mode:"lines",line:{{color:"{LC}",width:2}},name:"P(Long)",xaxis:"x2",yaxis:"y2",hovertemplate:"%{{x}}<br>P(L)=%{{y:.3f}}<extra></extra>"}});\n'
    # P(Short) téglavörös
    js += f'data.push({{x:ts,y:{json.dumps(pS)},type:"scatter",mode:"lines",line:{{color:"{SC}",width:2}},name:"P(Short)",xaxis:"x2",yaxis:"y2",hovertemplate:"%{{x}}<br>P(S)=%{{y:.3f}}<extra></extra>"}});\n'
    # Layout
    js += 'var layout={showlegend:true,\n'
    js += f'legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",bordercolor:"#444",font:{{color:"{TC}",size:10}}}},\n'
    js += f'xaxis:{{domain:[0,1],anchor:"y",matches:"x2",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},\n'
    js += f'yaxis:{{domain:[0.32,1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},\n'
    js += f'xaxis2:{{domain:[0,1],anchor:"y2",gridcolor:"{GC}"}},\n'
    js += f'yaxis2:{{domain:[0,0.291],anchor:"x2",range:[0,1],gridcolor:"{GC}",title:{{text:"Probability",font:{{color:"{TC}"}}}}}},\n'
    # Küszöb vonalak
    js += 'shapes:['
    js += f'{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:{lt_avg:.4f},y1:{lt_avg:.4f},line:{{color:"{LC}",width:1,dash:"dash"}}}},'
    js += f'{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:0.5,y1:0.5,line:{{color:"{NC}",width:1,dash:"dot"}}}},'
    js += f'{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:{st_avg:.4f},y1:{st_avg:.4f},line:{{color:"{SC}",width:1,dash:"dash"}}}}],\n'
    js += 'annotations:['
    js += f'{{font:{{size:16}},showarrow:false,text:"BTCUSD Scalper v8 {hname} — {day_str}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}},'
    js += f'{{font:{{size:16}},showarrow:false,text:"LightGBM {hname} Probabilities (AUC={auc_val:.4f})",x:0.5,xanchor:"center",xref:"paper",y:0.291,yanchor:"bottom",yref:"paper"}},'
    js += f'{{showarrow:false,text:"Long {lt_avg:.2f}",x:1,xanchor:"right",xref:"x2 domain",y:{lt_avg:.3f},yanchor:"bottom",yref:"y2",font:{{color:"{LC}",size:10}}}},'
    js += f'{{showarrow:false,text:"Short {st_avg:.2f}",x:1,xanchor:"right",xref:"x2 domain",y:{st_avg:.3f},yanchor:"bottom",yref:"y2",font:{{color:"{SC}",size:10}}}}],\n'
    js += f'plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},'
    js += 'margin:{l:55,r:80,t:25,b:40},height:900,hovermode:"x unified",dragmode:"zoom"};\n'
    js += 'Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n})();\n</script>'
    info = f"{hname}: AUC={auc_val:.4f} | Long▲={nL} Short▼={nS} @thr {lt_avg:.2f}/{st_avg:.2f}"
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>BTCUSD v8 {hname} — {day_str}</title><script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script><style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:#00d2ff;text-align:center}}</style></head><body><div id="chart"></div><div id="info">📊 {info}</div>{js}</body></html>'



def build_charts(day_str=None, max_pts=8000, thr_long=0.55, thr_short=0.45):
    print('='*72); print('V8 CHART — 5 Horizon, Template: scalper_copilot_chart.py'); print('='*72)
    # 1. LOAD TRAIN
    print('\n1. Loading TRAIN...')
    ticks_tr = load_ticks(str(DATA_DIR / 'BTCUSD_training_tick.csv'))
    bars_tr = make_dollar_bars(ticks_tr, DOLLAR_THR)
    feat_tr, cols_tr = build_features_v8(bars_tr)
    avail = [c for c in KEEP if c in cols_tr]
    feat_tr = feat_tr[avail]; bars_tr_al = bars_tr.loc[feat_tr.index]
    print(f'   Train: {len(feat_tr):,} bars, {len(avail)} features')
    # 2. LOAD EXAM (tick -> 1min OHLC + dollar bar features)
    print('\n2. Loading EXAM...')
    ticks_ex = load_ticks(str(EXAM_DIR / 'BTCUSD_exam_tick.csv'), label='EXAM')
    bars_ex = make_dollar_bars(ticks_ex, DOLLAR_THR)
    feat_ex, cols_ex = build_features_v8(bars_ex)
    feat_ex = feat_ex[[c for c in avail if c in cols_ex]]
    bars_ex_al = bars_ex.loc[feat_ex.index]
    # 1min OHLC for candlestick (folytonos!)
    ohlc_1min = resample_1min(ticks_ex)
    print(f'   Exam: {len(feat_ex):,} dollar bars, {len(ohlc_1min):,} 1min bars')
    # 3. LOAD MODELS
    print('\n3. Loading models...')
    models = {}; aucs = {}
    for hname, hsec in HORIZONS:
        mp = MODEL_DIR / f'v8_long_{hname}.txt'
        if mp.exists():
            models[hname] = lgb.Booster(model_file=str(mp))
            # Quick CV AUC
            y_l, _ = label_tbm(bars_tr_al, hsec, pt_m=0.5, sl_m=0.3)
            valid = (y_l != 0); X = feat_tr[valid].values; y = y_l[valid]
            s = int(len(X)*0.1); X_t = X[s:]; y_t = y[s:]
            aucs[hname] = roc_auc_score(y_t, models[hname].predict(X_t))
            print(f'   {hname}: loaded, AUC={aucs[hname]:.4f}')
        else:
            print(f'   {hname}: model not found!'); return None
    # 4. PREDICT
    print('\n4. Predicting OOS...')
    X_ex = feat_ex[avail].values; preds = {}
    for hname, _ in HORIZONS:
        p = models[hname].predict(X_ex)
        preds[hname] = pd.Series(p, index=feat_ex.index)
        print(f'   {hname}: mean={p.mean():.3f}')
    # 5. SELECT DAY (use 1min OHLC for candlestick)
    if day_str is None: day_str = ohlc_1min.index[-1].strftime('%Y-%m-%d')
    day = pd.Timestamp(day_str); nxt = day + pd.Timedelta(days=1)
    day_mask = (ohlc_1min.index >= day) & (ohlc_1min.index < nxt)
    day_ohlc = ohlc_1min[day_mask]
    if len(day_ohlc) == 0: print(f'No data for {day_str}!'); return None
    n = len(day_ohlc)
    print(f'   Day: {day_str}, {n:,} 1min bars')
    # 6. GENERATE 5 HTML (candlestick from 1min OHLC, predictions from dollar bars)
    print('\n5. Generating charts...')
    ts = [t.strftime('%Y-%m-%d %H:%M:%S') for t in day_ohlc.index]
    o_ = day_ohlc['open'].round(2).tolist()
    hi_ = day_ohlc['high'].round(2).tolist()
    lo_ = day_ohlc['low'].round(2).tolist()
    cl_ = day_ohlc['close'].round(2).tolist()
    for hname, _ in HORIZONS:
        # Interpolate dollar bar predictions to 1min grid
        p_dollar = preds[hname]
        # For each 1min bar, find the closest dollar bar prediction
        p_1min = []
        for t in day_ohlc.index:
            # Find closest dollar bar before or at this time
            mask = p_dollar.index <= t
            if mask.any():
                p_1min.append(p_dollar.loc[p_dollar.index[mask][-1]])
            else:
                p_1min.append(0.5)
        pL = [round(p, 4) for p in p_1min]
        pS = [round(1.0 - p, 4) for p in p_1min]
        sig = [1 if p > thr_long else -1 if p < thr_short else 0 for p in pL]
        lts = [ts[i] for i in range(n) if sig[i]==1]
        lpx = [round(day_ohlc['close'].iloc[i]*0.9997,2) for i in range(n) if sig[i]==1]
        sts = [ts[i] for i in range(n) if sig[i]==-1]
        spx = [round(day_ohlc['close'].iloc[i]*1.0003,2) for i in range(n) if sig[i]==-1]
        nL = len(lts); nS = len(sts)
        html = _gen_html(hname, day_str, ts, o_, hi_, lo_, cl_, pL, pS,
                         thr_long, thr_short, lts, lpx, sts, spx, n, nL, nS, aucs[hname])
        out = CHART_DIR / f'BTCUSD_v8_{hname}_{day_str}.html'
        with open(out, 'w') as f: f.write(html)
        print(f'   ✅ {out.name} ({len(html)//1024}KB)')
    print('\n✅ Done!')

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='V8 Chart — 5 Horizon')
    p.add_argument('--date', default=None, help='YYYY-MM-DD')
    p.add_argument('--max-points', type=int, default=8000)
    a = p.parse_args()
    build_charts(day_str=a.date, max_pts=a.max_points)
