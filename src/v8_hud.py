#!/usr/bin/env python3
"""
Scalper HUD v8 — 5-Horizon Dashboard (1-5 min)
  FELSŐ (60%): Candlestick + Long▲ Short▼ + regime színezés
  ALSÓ (40%): 5 panel — 1min..5min — P(Long)/P(Short)/küszöb
Template: scalper_hud_v6.py adaptálva v8 modellekhez
"""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import load_ticks, make_dollar_bars, label_tbm, DATA_DIR, EXAM_DIR, DOLLAR_THR, SEED
from build_features_v8 import build_features_v8, FEATURES_V8_PRUNED
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts')
CHART_DIR.mkdir(parents=True, exist_ok=True)

LC='#228B22'; SC='#B22222'; NC='#FF8C00'
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'
C_TREND='rgba(255,0,0,0.08)'; C_MR='rgba(0,255,0,0.05)'

HORIZONS = ['1min','2min','3min','4min','5min']
H_COLORS = {'1min':'#FF9800','2min':'#4CAF50','3min':'#2196F3','4min':'#9C27B0','5min':'#E91E63'}
PY = 0.40; PH = PY / len(HORIZONS)
PANEL = {}
for i, h in enumerate(HORIZONS):
    y1 = PY - i * PH; y0 = y1 - PH
    PANEL[h] = (f'x{i+3}', f'y{i+3}', round(y0, 4), round(y1, 4))

KEEP = [f for f in FEATURES_V8_PRUNED if f not in ('kill_zone','ema_d_5')]


def build_hud(day_str=None, max_pts=12000, thr_long=0.55, thr_short=0.45):
    print('='*72); print('V8 HUD — 5-Horizon Dashboard'); print('='*72)
    print(f'Features: {len(KEEP)}')
    # 1. LOAD TRAIN
    print('\n1. Loading TRAIN...')
    ticks_tr = load_ticks(str(DATA_DIR / 'BTCUSD_training_tick.csv'))
    bars_tr = make_dollar_bars(ticks_tr, DOLLAR_THR)
    feat_tr, cols_tr = build_features_v8(bars_tr)
    avail = [c for c in KEEP if c in cols_tr]
    feat_tr = feat_tr[avail]; bars_tr_al = bars_tr.loc[feat_tr.index]
    print(f'   Train: {len(feat_tr):,} bars')
    # 2. LOAD EXAM
    print('\n2. Loading EXAM...')
    ticks_ex = load_ticks(str(EXAM_DIR / 'BTCUSD_exam_tick.csv'), label='EXAM')
    bars_ex = make_dollar_bars(ticks_ex, DOLLAR_THR)
    feat_ex, cols_ex = build_features_v8(bars_ex)
    feat_ex = feat_ex[[c for c in avail if c in cols_ex]]
    bars_ex_al = bars_ex.loc[feat_ex.index]
    print(f'   Exam: {len(feat_ex):,} bars')
    # 3. TRAIN / LOAD MODELS
    models = {}; HSEC = {'1min':60,'2min':120,'3min':180,'4min':240,'5min':300}
    LP = {'objective':'binary','metric':'auc','learning_rate':0.05,'num_leaves':31,
          'feature_fraction':0.7,'bagging_fraction':0.8,'bagging_freq':5,
          'seed':SEED,'verbose':-1,'min_data_in_leaf':50,'lambda_l1':1.0}
    for hname in HORIZONS:
        mp = MODEL_DIR / f'v8_long_{hname}.txt'
        if mp.exists():
            models[hname] = lgb.Booster(model_file=str(mp))
            print(f'   {hname}: loaded {mp.name}')
        else:
            hsec = HSEC[hname]; print(f'\n--- Training {hname} ---')
            y_l, _ = label_tbm(bars_tr_al, hsec, pt_m=0.5, sl_m=0.3)
            valid = (y_l != 0); X = feat_tr[valid].values; y = y_l[valid]
            n=len(X); s=int(n*0.1); X_t=X[s:]; y_t=y[s:]
            tscv=TimeSeriesSplit(n_splits=5); aucs=[]
            for fold,(tr,va) in enumerate(tscv.split(X_t)):
                dtr=lgb.Dataset(X_t[tr],label=y_t[tr],feature_name=avail)
                dva=lgb.Dataset(X_t[va],label=y_t[va],feature_name=avail,reference=dtr)
                m=lgb.train(LP,dtr,300,[dva],callbacks=[lgb.early_stopping(30,verbose=False)])
                aucs.append(roc_auc_score(y_t[va],m.predict(X_t[va])))
            print(f'   AUC: {np.mean(aucs):.4f} +/- {np.std(aucs):.4f}')
            dall=lgb.Dataset(X_t,label=y_t,feature_name=avail)
            bst=lgb.train(LP,dall,200); bst.save_model(str(mp)); models[hname]=bst
    # 4. PREDICT
    print('\n3. Predicting OOS...')
    X_ex = feat_ex[avail].values; preds = {}
    for hname in HORIZONS:
        p = models[hname].predict(X_ex)
        preds[hname] = pd.Series(p, index=feat_ex.index)
        print(f'   {hname}: mean={p.mean():.3f}')
    # 5. SELECT DAY
    if day_str is None: day_str = bars_ex_al.index[-1].strftime('%Y-%m-%d')
    day = pd.Timestamp(day_str); nxt = day + pd.Timedelta(days=1)
    day_mask = (bars_ex_al.index >= day) & (bars_ex_al.index < nxt)
    day_bars = bars_ex_al[day_mask]
    if len(day_bars) == 0: print(f'No data for {day_str}!'); return None
    n = len(day_bars)
    if n > max_pts:
        step = max(1, n // max_pts); day_bars = day_bars.iloc[::step]; n = len(day_bars)
    print(f'   Day: {day_str}, {n:,} bars')
    # 6. DATA PREP
    ts = [t.strftime('%Y-%m-%d %H:%M:%S') for t in day_bars.index]
    px = day_bars['close'].round(2).tolist()
    o_ = day_bars['open'].round(2).tolist()
    hi_ = day_bars['high'].round(2).tolist()
    lo_ = day_bars['low'].round(2).tolist()
    cl_ = day_bars['close'].round(2).tolist()
    h_data = {}
    for h in HORIZONS:
        p_day = preds[h].reindex(day_bars.index).fillna(0.5)
        pL = p_day.round(4).tolist()
        pS = (1.0 - p_day).round(4).tolist()
        sig = [1 if p > thr_long else -1 if p < thr_short else 0 for p in pL]
        nL = sum(1 for s in sig if s==1); nS = sum(1 for s in sig if s==-1)
        h_data[h] = {'pL':pL,'pS':pS,'sig':sig,'lt_avg':thr_long,'st_avg':thr_short,'nL':nL,'nS':nS}
    # 7. BUILD HTML (template: scalper_hud_v6.py)
    sig_main = h_data['2min']['sig']
    lts = [ts[i] for i in range(n) if sig_main[i]==1]
    lpx = [round(px[i]*0.9997,2) for i in range(n) if sig_main[i]==1]
    sts = [ts[i] for i in range(n) if sig_main[i]==-1]
    spx = [round(px[i]*1.0003,2) for i in range(n) if sig_main[i]==-1]
    js = '<script>(function(){\nvar ts='+json.dumps(ts)+';\n'
    js += 'var px='+json.dumps(px)+';\n'
    js += 'var o_='+json.dumps(o_)+',hi_='+json.dumps(hi_)+',lo_='+json.dumps(lo_)+',cl_='+json.dumps(cl_)+';\n'
    js += 'var data=[];\n'
    # Candlestick
    js += f'data.push({{x:ts,open:o_,high:hi_,low:lo_,close:cl_,type:"candlestick",increasing:{{line:{{color:"{LC}"}}}},decreasing:{{line:{{color:"{SC}"}}}},name:"Price",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>$%{{y:,.0f}}<extra></extra>"}});\n'
    # Long ▲ green triangles
    if lts:
        js += f'data.push({{x:{json.dumps(lts)},y:{json.dumps(lpx)},type:"scatter",mode:"markers",marker:{{color:"{LC}",symbol:"triangle-up",size:10}},name:"Long▲",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>$%{{y:,.0f}} ▲LONG<extra></extra>"}});\n'
    # Short ▼ red triangles
    if sts:
        js += f'data.push({{x:{json.dumps(sts)},y:{json.dumps(spx)},type:"scatter",mode:"markers",marker:{{color:"{SC}",symbol:"triangle-down",size:10}},name:"Short▼",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>$%{{y:,.0f}} ▼SHORT<extra></extra>"}});\n'
    # Per-horizon probability curves
    for h in HORIZONS:
        xa,ya,y0,y1 = PANEL[h]; d = h_data[h]
        js += f'data.push({{x:ts,y:{json.dumps(d["pL"])},type:"scatter",mode:"lines",line:{{color:"{LC}",width:1.5}},name:"P(L) {h}",xaxis:"{xa}",yaxis:"{ya}",hovertemplate:"%{{x}}<br>P(L)=%{{y:.3f}}<extra></extra>"}});\n'
        js += f'data.push({{x:ts,y:{json.dumps(d["pS"])},type:"scatter",mode:"lines",line:{{color:"{SC}",width:1.5}},name:"P(S) {h}",xaxis:"{xa}",yaxis:"{ya}",hovertemplate:"%{{x}}<br>P(S)=%{{y:.3f}}<extra></extra>"}});\n'
    # Shapes + Annotations + Layout
    shapes = ''
    for h in HORIZONS:
        xa,ya,y0,y1 = PANEL[h]; d = h_data[h]
        lt_a = d['lt_avg']; st_a = d['st_avg']
        shapes += f'{{type:"line",xref:"{xa} domain",yref:"{ya}",x0:0,x1:1,y0:{lt_a:.4f},y1:{lt_a:.4f},line:{{color:"{LC}",width:1,dash:"dash"}}}},'
        shapes += f'{{type:"line",xref:"{xa} domain",yref:"{ya}",x0:0,x1:1,y0:{st_a:.4f},y1:{st_a:.4f},line:{{color:"{SC}",width:1,dash:"dash"}}}},'
    if shapes.endswith(','): shapes = shapes[:-1]
    anns = f'{{font:{{size:15}},showarrow:false,text:"BTCUSD Scalper v8 — {day_str}",x:0.5,xanchor:"center",xref:"paper",y:1.0,yanchor:"bottom",yref:"paper"}},'
    for h in HORIZONS:
        _,ya,y0,y1 = PANEL[h]; d = h_data[h]
        nL=d['nL']; nS=d['nS']; lt_a=d['lt_avg']; st_a=d['st_avg']
        anns += f'{{font:{{size:10,color:"{H_COLORS[h]}"}},showarrow:false,text:"{h}: L▲={nL:,} S▼={nS:,} | thr {lt_a:.2f}/{st_a:.2f}",x:0.02,xanchor:"left",xref:"paper",y:{(y0+y1)/2:.4f},yanchor:"middle",yref:"paper"}},'
    if anns.endswith(','): anns = anns[:-1]
    js += f'var layout={{showlegend:true,legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.85)",font:{{color:"{TC}",size:9}}}},'
    js += f'xaxis:{{domain:[0,1],anchor:"y",matches:"x3",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}"}},'
    js += f'yaxis:{{domain:[{PY},1.0],anchor:"x",gridcolor:"{GC}",title:{{text:"Price",font:{{color:"{TC}"}}}}}},'
    for i,h in enumerate(HORIZONS):
        xa,ya,y0,y1 = PANEL[h]
        showtl = 'true' if i==len(HORIZONS)-1 else 'false'
        match = 'matches:"x3",' if i<len(HORIZONS)-1 else ''
        js += f'{xa}:{{domain:[0,1],anchor:"{ya}",{match}showticklabels:{showtl},gridcolor:"{GC}"}},'
        js += f'{ya}:{{domain:[{y0},{y1}],anchor:"{xa}",range:[0,1],gridcolor:"{GC}"}},'
    js += f'shapes:[{shapes}],annotations:[{anns}],'
    js += f'plot_bgcolor:"{BG}",paper_bgcolor:"{BG}",font:{{color:"{TC}"}},'
    js += f'margin:{{l:55,r:80,t:25,b:30}},height:1050,hovermode:"x unified",dragmode:"zoom"}};'
    js += 'Plotly.newPlot("chart",data,layout,{responsive:true,displayModeBar:true,displaylogo:false});\n})();\n</script>'
    # Info bar
    parts = []
    for h in HORIZONS:
        d = h_data[h]; parts.append(f'{h}: L▲={d["nL"]:,} S▼={d["nS"]:,} @thr {d["lt_avg"]:.2f}/{d["st_avg"]:.2f}')
    info = ' │ '.join(parts)
    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<title>BTCUSD Scalper HUD v8 — {day_str}</title>
<script src="https://cdn.plot.ly/plotly-3.7.0.min.js"></script>
<style>body{{margin:0;padding:0;background:{BG};color:{TC};font-family:monospace}}#chart{{width:100%;height:calc(100vh - 36px)}}#info{{padding:6px 16px;background:#111;border-top:1px solid #333;font-size:11px;color:#00d2ff;text-align:center}}</style></head><body>
<div id="chart"></div><div id="info">📊 {info}</div>{js}</body></html>'''
    out = CHART_DIR / f'BTCUSD_hud_v8_{day_str}.html'
    with open(out,'w') as f: f.write(html)
    print(f'\n✅ {out.name} ({len(html)//1024}KB)')
    return out

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Scalper HUD v8 — 5-Horizon Dashboard')
    p.add_argument('--date', default=None, help='YYYY-MM-DD')
    p.add_argument('--max-points', type=int, default=12000)
    a = p.parse_args()
    build_hud(day_str=a.date, max_pts=a.max_points)
