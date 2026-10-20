#!/usr/bin/env python3
"""V8 Dual-Binary Chart — Fuggetlen P(Long) + P(Short) modell
Vizsga chart: 5 horizon panel + OHLC + független Long/Short signal markers
"""
import sys, warnings, json
warnings.filterwarnings('ignore')
sys.path.insert(0, '/data/LGBM_copilot/src')
import numpy as np, pandas as pd
import lightgbm as lgb
from pathlib import Path
from scalper_copilot_v6 import load_ticks, make_dollar_bars, EXAM_DIR, DOLLAR_THR
from build_features_v8 import build_features_v8, FEATURES_V8_PRUNED

MDIR=Path('/data/LGBM_copilot/models/scalper')
CDIR=Path('/data/LGBM_copilot/charts'); CDIR.mkdir(exist_ok=True)
KEEP=[f for f in FEATURES_V8_PRUNED if f not in ('kill_zone','ema_d_5')]
HORIZONS=[('1min',60),('2min',120),('3min',180),('4min',240),('5min',300)]
LC='#26a69a';SC='#ef5350';NC='#FF8C00'
BG='rgb(17,17,17)';GC='#283442';TC='#f2f5fa'

def build_preds():
    print('Loading exam ticks...')
    ticks=load_ticks(str(EXAM_DIR/'BTCUSD_exam_tick.csv'),label='EXAM')
    bars=make_dollar_bars(ticks,DOLLAR_THR)
    feat,cols=build_features_v8(bars)
    avail=[c for c in KEEP if c in cols]; feat=feat[avail]; bars_al=bars.loc[feat.index]
    ohlc=ticks['price'].resample('1min').ohlc().dropna()
    print('1min: %d bars, $bars: %d' % (len(ohlc), len(bars_al)))
    df=ohlc.copy(); df['price']=df['close']
    summary={}
    for hname,hsec in HORIZONS:
        mpl=MDIR/f'v8_long_{hname}.txt'
        mps=MDIR/f'v8_short_{hname}.txt'
        if not mpl.exists() or not mps.exists():
            print('  %s: model missing'); continue
        ml=lgb.Booster(model_file=str(mpl))
        ms=lgb.Booster(model_file=str(mps))
        # Dollar bar predikcio
        pL_dollar=ml.predict(feat[avail].values)
        pS_dollar=ms.predict(feat[avail].values)
        # 1min OHLC-re map (last $bar at each 1min)
        pL=[];pS=[]
        for t in df.index:
            mask=feat.index<=t
            if mask.any():
                i=feat.index.get_loc(feat.index[mask][-1])
                pL.append(pL_dollar[i]);pS.append(pS_dollar[i])
            else: pL.append(0.0);pS.append(0.0)
        df['p_long_'+hname]=pL;df['p_short_'+hname]=pS
        pLa=np.array(pL);pSa=np.array(pS)
        # Dual signal: Long ha P(L)>0.40, Short ha P(S)>0.40 (független)
        # Ha mindketto>0.40 -> Noise (ambigu)
        sig=np.where(pLa>0.40,1,0) + np.where(pSa>0.40,-1,0)
        # 0 = Noise, 1 = Long, -1 = Short
        # Ha mindketto>0.40 (sig=0 from +1-1=0, but we want to distinguish)
        # Use cleaner logic:
        sig=np.zeros(len(pLa),dtype=int)
        for k in range(len(pLa)):
            if pLa[k]>0.40 and pSa[k]<=0.40: sig[k]=1
            elif pSa[k]>0.40 and pLa[k]<=0.40: sig[k]=-1
            # else: 0 (Noise)
        df['signal_'+hname]=sig
        nL=int((sig==1).sum());nS=int((sig==-1).sum());nN=int((sig==0).sum())
        pl=pLa.mean();ps=pSa.mean()
        bias=nL/max(1,nS)
        summary[hname]={'P(L)':float(pl),'P(S)':float(ps),
                        'nL':nL,'nS':nS,'nN':nN,'bias':float(bias)}
        print('  %s: P(L)=%.3f P(S)=%.3f | L=%d S=%d N=%d | L/S=%.2f' %
              (hname,pl,ps,nL,nS,nN,bias))
    out=MDIR/'BTCUSD_v8_dual_preds.csv';df.to_csv(str(out))
    print('Saved: %s' % out)
    return df,summary

def render_chart(df,summary):
    print('Rendering chart...')
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    nH=len(HORIZONS)
    fig=make_subplots(rows=nH+1,cols=1,shared_xaxes=True,
        row_heights=[0.25]+[0.15]*nH,
        vertical_spacing=0.02,
        subplot_titles=['OHLC + 1min Dual Signal']+[f'{h} — P(Long) [indep] / P(Short) [indep]' for h,_ in HORIZONS])
    # Row 1: OHLC + 1min signal
    h0='1min'
    fig.add_trace(go.Candlestick(x=df.index,open=df['open'],high=df['high'],
        low=df['low'],close=df['close'],name='OHLC',increasing_line_color=LC,
        decreasing_line_color=SC,line=dict(width=1)),row=1,col=1)
    sig=df['signal_'+h0].values
    long_idx=np.where(sig==1)[0]
    short_idx=np.where(sig==-1)[0]
    if len(long_idx):
        fig.add_trace(go.Scatter(x=df.index[long_idx],y=df['low'].iloc[long_idx].values*0.999,
            mode='markers',marker=dict(symbol='triangle-up',size=10,color=LC),
            name='Long',showlegend=False),row=1,col=1)
    if len(short_idx):
        fig.add_trace(go.Scatter(x=df.index[short_idx],y=df['high'].iloc[short_idx].values*1.001,
            mode='markers',marker=dict(symbol='triangle-down',size=10,color=SC),
            name='Short',showlegend=False),row=1,col=1)
    # Row 2..nH+1: probabilities per horizon (independent)
    for r,(hname,_) in enumerate(HORIZONS,start=2):
        fig.add_trace(go.Scatter(x=df.index,y=df['p_long_'+hname],
            name='P(Long) indep',line=dict(color=LC,width=1.5),showlegend=(r==2)),row=r,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df['p_short_'+hname],
            name='P(Short) indep',line=dict(color=SC,width=1.5),showlegend=(r==2)),row=r,col=1)
        fig.add_hline(y=0.40,line_dash='dash',line_color=GC,row=r,col=1)
        fig.add_hrect(y0=0.35,y1=0.45,line_width=0,fillcolor=GC,opacity=0.15,row=r,col=1)
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=BG,plot_bgcolor=BG,
        font=dict(color=TC,size=11),
        height=200+250*(nH+1),width=1600,
        title_text='V8 Dual-Binary (Jules V5 Strict Wick) — BTCUSD Exam | Independent P(Long) + P(Short)',
        xaxis_rangeslider_visible=False,
        showlegend=True)
    fig.update_xaxes(showgrid=True,gridcolor=GC)
    fig.update_yaxes(showgrid=True,gridcolor=GC)
    out=CDIR/'BTCUSD_v8_dual_exam.html'
    fig.write_html(str(out),include_plotlyjs='cdn')
    print('Chart saved: %s' % out)
    return out

def main():
    df,summary=build_preds()
    out=render_chart(df,summary)
    print('\n'+'='*60)
    print('  VIZSGA OSSZEGFOGALO — Dual-Binary Long-Bias Check')
    print('='*60)
    print('  %-8s%-10s%-10s%-8s%-8s%-8s%-10s' % ('Horizon','P(Long)','P(Short)','nLong','nShort','nNoise','L/S bias'))
    for h,s in summary.items():
        print('  %-8s%-10.3f%-10.3f%-8d%-8d%-8d%-10.2f' %
              (h,s['P(L)'],s['P(S)'],s['nL'],s['nS'],s['nN'],s['bias']))
    print('\nChart: %s' % out)

if __name__=='__main__': main()
