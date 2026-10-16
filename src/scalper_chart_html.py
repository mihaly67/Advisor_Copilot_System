"""
Scalper Interactive HTML Chart — Plotly.js standalone
1 day visualization: P(Long) + P(Short) with zoom/pan
Forest green for Long, Brick red for Short
"""
import json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts')
CHART_DIR.mkdir(parents=True, exist_ok=True)

LONG_COLOR = '#228B22'   # Forest green
SHORT_COLOR = '#B22222'  # Brick red (Firebrick)
BG_DARK = '#111111'
BG_PAPER = '#0a0a0a'
GRID_COLOR = '#333333'
TEXT_COLOR = '#cccccc'
PRICE_COLOR = '#00d2ff'


def find_latest_scalper(instrument='BTCUSD'):
    # Try v3f (final) first, then v3h, then scalper
    for prefix in ['v3f', 'v3h', 'scalper']:
        metas = sorted(MODEL_DIR.glob(f'{instrument}_{prefix}_meta_*.json'))
        if metas:
            with open(metas[-1]) as f:
                meta = json.load(f)
            preds = sorted(MODEL_DIR.glob(f'{instrument}_{prefix}_preds_*.csv'))
            prices = sorted(MODEL_DIR.glob(f'{instrument}_{prefix}_price_*.csv'))
            r = {'meta': meta, 'prefix': prefix}
            if preds: r['preds'] = preds[-1]
            if prices: r['price'] = prices[-1]
            return r
    return None


def filter_one_day(df, date_str=None):
    if date_str:
        day = pd.Timestamp(date_str)
    else:
        day = df.index[0].normalize()
    next_day = day + pd.Timedelta(days=1)
    mask = (df.index >= day) & (df.index < next_day)
    return df.loc[mask], day.strftime('%Y-%m-%d')


def _build_ohlc(instrument, day_str):
    """Load tick data for 1 day, resample to 1-min OHLC for candlestick."""
    try:
        data_dir = Path('/data/dev/LGB_copilot_system/RAW_CSV')
        if instrument == 'BTCUSD':
            path = data_dir / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
        else:
            return None
        print(f"  Loading ticks for OHLC: {path.name}...")
        df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp',
                         usecols=['Timestamp', 'Bid', 'Ask'])
        df.columns = [c.lower() for c in df.columns]
        day = pd.Timestamp(day_str)
        next_day = day + pd.Timedelta(days=1)
        df = df.loc[(df.index >= day) & (df.index < next_day)]
        if len(df) == 0:
            return None
        mid = ((df['bid'] + df['ask']) / 2).to_frame('mid')
        ohlc = mid['mid'].resample('1min').ohlc().dropna()
        print(f"  OHLC: {len(ohlc)} 1-min candles")
        return ohlc
    except Exception as e:
        print(f"  OHLC failed: {e}")
        return None


def _build_data_arrays(preds_1d, price_1d, lt, st, ohlc_1d=None):
    """Extract JS-ready arrays. ohlc_1d: DataFrame with ohlc columns aligned to preds."""
    n = len(preds_1d)
    timestamps = [t.strftime('%Y-%m-%d %H:%M:%S') for t in preds_1d.index]
    p_long = preds_1d['p_long'].round(4).tolist()
    p_short = preds_1d['p_short'].round(4).tolist()
    prices = price_1d.iloc[:, 0].round(2).tolist() if price_1d.shape[1] > 0 else price_1d.round(2).tolist()
    long_mask = preds_1d['p_long'] > lt
    short_mask = preds_1d['p_short'] > st
    long_times = [timestamps[i] for i in range(n) if long_mask.iloc[i]]
    long_prices = [round(prices[i] * 0.9997, 2) for i in range(n) if long_mask.iloc[i]]
    short_times = [timestamps[i] for i in range(n) if short_mask.iloc[i]]
    short_prices = [round(prices[i] * 1.0003, 2) for i in range(n) if short_mask.iloc[i]]
    net = (preds_1d['p_long'] - preds_1d['p_short']).round(4).tolist()
    d = dict(ts=timestamps, px=prices, pL=p_long, pS=p_short, net=net,
             lts=long_times, lpx=long_prices, sts=short_times, spx=short_prices,
             n_long=len(long_times), n_short=len(short_times))
    # OHLC for candlestick (from 1-min resample of tick data)
    if ohlc_1d is not None and len(ohlc_1d) > 0:
        d['ohlc_ts'] = [t.strftime('%Y-%m-%d %H:%M:%S') for t in ohlc_1d.index]
        d['ohlc_o'] = ohlc_1d['open'].round(2).tolist()
        d['ohlc_h'] = ohlc_1d['high'].round(2).tolist()
        d['ohlc_l'] = ohlc_1d['low'].round(2).tolist()
        d['ohlc_c'] = ohlc_1d['close'].round(2).tolist()
    return d


def build_scalper_html(instrument='BTCUSD', date_str=None, max_points=8000):
    s = find_latest_scalper(instrument)
    if not s:
        print(f"No scalper model for {instrument}"); return None
    meta = s['meta']
    la, sa = meta.get('long_auc', 0), meta.get('short_auc', 0)
    lt, st = meta.get('long_thr', 0.5), meta.get('short_thr', 0.5)
    print("Loading predictions...")
    preds = pd.read_csv(s['preds'], index_col=0, parse_dates=True)
    price = pd.read_csv(s['price'], index_col=0, parse_dates=True)
    preds_1d, day_str = filter_one_day(preds, date_str)
    if len(preds_1d) == 0:
        print(f"No data for {date_str or 'first day'}"); return None
    price_1d = price.reindex(preds_1d.index).ffill().bfill()
    n = len(preds_1d)
    if n > max_points:
        step = max(1, n // max_points)
        idx = preds_1d.index[::step]
        preds_1d, price_1d = preds_1d.loc[idx], price_1d.loc[idx]
        n = len(preds_1d)
    print(f"  Day: {day_str}, Points: {n}, Long AUC={la:.4f}, Short AUC={sa:.4f}")
    # Display thresholds: use model thr but floor at 0.30 for visual clarity
    disp_lt = max(min(lt, 0.50), 0.30)
    disp_st = max(min(st, 0.50), 0.30)
    # Build 1-min OHLC from tick data for candlestick chart
    ohlc_1d = _build_ohlc(instrument, day_str)
    d = _build_data_arrays(preds_1d, price_1d, disp_lt, disp_st, ohlc_1d)
    print(f"  Long signals: {d['n_long']}, Short signals: {d['n_short']}")
    title = f'{instrument} Scalper | {day_str} | Long AUC={la:.3f} | Short AUC={sa:.3f}'
    html = _render_html(title, day_str, meta, d, disp_lt, disp_st, n, instrument)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = CHART_DIR / f'{instrument}_scalper_{day_str}_{ts}.html'
    out.write_text(html, encoding='utf-8')
    kb = out.stat().st_size / 1024
    print(f"\n✅ HTML chart saved: {out}")
    print(f"   Size: {kb:.0f} KB | Day: {day_str} | Points: {n}")
    print(f"   Long signals: {d['n_long']} | Short signals: {d['n_short']}")
    return out


def _render_html(title, day_str, meta, d, lt, st, n, instrument):
    """Render the full Plotly.js HTML page."""
    LC, SC, PC = LONG_COLOR, SHORT_COLOR, PRICE_COLOR
    BG, BP, GC, TC = BG_DARK, BG_PAPER, GRID_COLOR, TEXT_COLOR
    nl, ns = d['n_long'], d['n_short']
    sub = meta.get('subsample', 5)
    j = json.dumps
    ts_j, px_j, pL_j, pS_j = j(d['ts']), j(d['px']), j(d['pL']), j(d['pS'])
    lts_j, lpx_j, sts_j, spx_j = j(d['lts']), j(d['lpx']), j(d['sts']), j(d['spx'])
    # OHLC for candlestick
    has_ohlc = 'ohlc_ts' in d
    ohlc_ts_j = j(d.get('ohlc_ts', []))
    ohlc_o_j = j(d.get('ohlc_o', []))
    ohlc_h_j = j(d.get('ohlc_h', []))
    ohlc_l_j = j(d.get('ohlc_l', []))
    ohlc_c_j = j(d.get('ohlc_c', []))
    return _build_html_str(title, n, nl, ns, sub, lt, st,
                           ts_j, px_j, pL_j, pS_j, lts_j, lpx_j, sts_j, spx_j,
                           LC, SC, PC, BG, BP, GC, TC,
                           has_ohlc, ohlc_ts_j, ohlc_o_j, ohlc_h_j, ohlc_l_j, ohlc_c_j)


def _build_html_str(title, n, nl, ns, sub, lt, st,
                    ts_j, px_j, pL_j, pS_j, lts_j, lpx_j, sts_j, spx_j,
                    LC, SC, PC, BG, BP, GC, TC,
                    has_ohlc, ohlc_ts_j, ohlc_o_j, ohlc_h_j, ohlc_l_j, ohlc_c_j):
    h = '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><title>' + title + '</title>\n<style>\n'
    h += f'body{{margin:0;padding:0;background:{BP};color:{TC};font-family:"Courier New",monospace}}\n'
    h += f'.hdr{{padding:10px 20px;background:#1a1a2e;border-bottom:2px solid #00d2ff;display:flex;justify-content:space-between;align-items:center}}\n'
    h += f'.hdr h1{{margin:0;font-size:15px;color:#00d2ff}}\n'
    h += f'.hdr .st{{font-size:12px}}.st .lg{{color:{LC};font-weight:bold}}.st .sh{{color:{SC};font-weight:bold}}\n'
    h += f'#chart{{width:100%;height:calc(100vh - 48px)}}\n'
    h += f'.lbar{{position:fixed;bottom:8px;left:50%;transform:translateX(-50%);background:rgba(20,20,40,0.9);border:1px solid #333;border-radius:6px;padding:5px 14px;font-size:11px;display:flex;gap:16px;z-index:100}}\n'
    h += f'.lbar span{{display:flex;align-items:center;gap:4px}}.lbar .dt{{width:10px;height:10px;border-radius:50%}}\n'
    h += '</style></head><body>\n'
    h += f'<div class="hdr"><h1>📊 {title}</h1><div class="st"><span class="lg">▲ Long: {nl}</span> | <span class="sh">▼ Short: {ns}</span> | Total: {n} | ~{sub} ticks/sample</div></div>\n'
    h += '<div id="chart"></div>\n'
    h += f'<div class="lbar"><span><div class="dt" style="background:{LC}"></div> Long (P&gt;{lt:.2f})</span><span><div class="dt" style="background:{SC}"></div> Short (P&gt;{st:.2f})</span><span><div class="dt" style="background:{PC}"></div> Price</span><span>🖱 Zoom | Drag | DblClick=reset</span></div>\n'
    h += '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>\n'
    h += _build_js(ts_j, px_j, pL_j, pS_j, lts_j, lpx_j, sts_j, spx_j, lt, st, LC, SC, PC, BG, BP, GC, TC,
                   has_ohlc, ohlc_ts_j, ohlc_o_j, ohlc_h_j, ohlc_l_j, ohlc_c_j)
    h += '</body></html>'
    return h


def _build_js(ts_j, px_j, pL_j, pS_j, lts_j, lpx_j, sts_j, spx_j, lt, st, LC, SC, PC, BG, BP, GC, TC,
              has_ohlc, ohlc_ts_j, ohlc_o_j, ohlc_h_j, ohlc_l_j, ohlc_c_j):
    j = '<script>\n(function(){\n'
    j += f'var ts={ts_j},px={px_j},pL={pL_j},pS={pS_j},lts={lts_j},lpx={lpx_j},sts={sts_j},spx={spx_j},lt={lt},st={st};\n'
    # OHLC candlestick or line
    if has_ohlc:
        j += f'var oTs={ohlc_ts_j},oO={ohlc_o_j},oH={ohlc_h_j},oL={ohlc_l_j},oC={ohlc_c_j};\n'
    j += 'var traces=[\n'
    if has_ohlc:
        j += '{x:oTs,open:oO,high:oH,low:oL,close:oC,type:"candlestick",name:"OHLC",xaxis:"x",yaxis:"y",'
        j += 'increasing:{line:{color:"#26a69a"}},decreasing:{line:{color:"#ef5350"}},'
        j += 'hovertemplate:"%{x}<br>O=%{open:.2f} H=%{high:.2f} L=%{low:.2f} C=%{close:.2f}<extra></extra>"},\n'
    else:
        j += f'{{x:ts,y:px,type:"scatter",mode:"lines",line:{{color:"{PC}",width:1.2}},name:"Mid Price",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>Price: %{{y:.2f}}<extra></extra>"}},\n'
    j += f'{{x:lts,y:lpx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-up",color:"{LC}",size:7,opacity:0.7}},name:"Long ▲ ("+lts.length+")",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>Long Signal<extra></extra>"}},\n'
    j += f'{{x:sts,y:spx,type:"scatter",mode:"markers",marker:{{symbol:"triangle-down",color:"{SC}",size:7,opacity:0.7}},name:"Short ▼ ("+sts.length+")",xaxis:"x",yaxis:"y",hovertemplate:"%{{x}}<br>Short Signal<extra></extra>"}},\n'
    j += f'{{x:ts,y:pL,type:"scatter",mode:"lines",line:{{color:"{LC}",width:1.5}},name:"P(Long)",xaxis:"x2",yaxis:"y2",fill:"tozeroy",fillcolor:"rgba(34,139,34,0.08)",hovertemplate:"%{{x}}<br>P(L)=%{{y:.4f}}<extra></extra>"}},\n'
    j += f'{{x:ts,y:pS,type:"scatter",mode:"lines",line:{{color:"{SC}",width:1.5}},name:"P(Short)",xaxis:"x2",yaxis:"y2",fill:"tozeroy",fillcolor:"rgba(178,34,34,0.08)",hovertemplate:"%{{x}}<br>P(S)=%{{y:.4f}}<extra></extra>"}}\n'
    j += '];\n'
    j += 'var layout={showlegend:true,\n'
    j += f'legend:{{x:0.01,y:0.99,bgcolor:"rgba(20,20,40,0.8)",bordercolor:"#333",borderwidth:1,font:{{color:"{TC}",size:11}}}},\n'
    j += f'xaxis:{{domain:[0,1],anchor:"y",matches:"x2",showticklabels:false,rangeslider:{{visible:false}},gridcolor:"{GC}",linecolor:"#555",tickfont:{{color:"{TC}"}}}},\n'
    j += f'yaxis:{{domain:[0.30,1.0],anchor:"x",gridcolor:"{GC}",linecolor:"#555",tickfont:{{color:"{TC}"}},title:{{text:"Price",font:{{color:"{TC}",size:12}}}}}},\n'
    j += f'xaxis2:{{domain:[0,1],anchor:"y2",gridcolor:"{GC}",linecolor:"#555",tickfont:{{color:"{TC}"}},title:{{text:"Time",font:{{color:"{TC}",size:12}}}}}},\n'
    j += f'yaxis2:{{domain:[0.0,0.27],anchor:"x2",range:[0,1],gridcolor:"{GC}",linecolor:"#555",tickfont:{{color:"{TC}"}},title:{{text:"Probability",font:{{color:"{TC}",size:12}}}}}},\n'
    j += f'shapes:[{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:lt,y1:lt,line:{{color:"{LC}",width:1,dash:"dash"}}}},{{type:"line",xref:"x2 domain",yref:"y2",x0:0,x1:1,y0:st,y1:st,line:{{color:"{SC}",width:1,dash:"dash"}}}}],\n'
    j += f'annotations:[{{x:1,y:lt,xref:"x2 domain",yref:"y2",xanchor:"right",yanchor:"bottom",text:"Long TH: "+lt.toFixed(2),showarrow:false,font:{{color:"{LC}",size:10}}}},{{x:1,y:st,xref:"x2 domain",yref:"y2",xanchor:"right",yanchor:"top",text:"Short TH: "+st.toFixed(2),showarrow:false,font:{{color:"{SC}",size:10}}}},{{x:0.5,y:1.0,xref:"paper",yref:"paper",xanchor:"center",yanchor:"bottom",text:"Price & Scalper Signals",showarrow:false,font:{{color:"#00d2ff",size:14}}}},{{x:0.5,y:0.27,xref:"paper",yref:"paper",xanchor:"center",yanchor:"bottom",text:"P(Long) / P(Short) Continuous",showarrow:false,font:{{color:"#00d2ff",size:14}}}}],\n'
    j += f'plot_bgcolor:"{BG}",paper_bgcolor:"{BP}",font:{{color:"{TC}"}},margin:{{l:60,r:30,t:20,b:40}},height:Math.max(600,window.innerHeight-48),width:window.innerWidth,dragmode:"zoom",hovermode:"x unified"}};\n'
    j += 'Plotly.newPlot("chart",traces,layout,{responsive:true,displayModeBar:true,modeBarButtonsToRemove:["select2d","lasso2d","autoScale2d"],displaylogo:false});\n'
    j += '})();\n</script>'
    return j


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Scalper interactive HTML chart (1 day)')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--date', default=None, help='Date YYYY-MM-DD (default: first day)')
    p.add_argument('--max-points', type=int, default=8000, help='Max points for browser perf')
    a = p.parse_args()
    build_scalper_html(a.instrument, a.date, a.max_points)
