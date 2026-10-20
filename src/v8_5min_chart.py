#!/usr/bin/env python3
"""V8 5min Vizsga Chart — OHLC + signal markers (felul) + P(Long)/P(Short) (alul)
Csak 5min horizon, dual-binary független modell
"""
import sys, warnings
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
HNAME='5min'; HSEC=300
TH=0.40
LC='#26a69a';SC='#ef5350'
BG='rgb(17,17,17)';GC='#283442';TC='#f2f5fa'

def build_preds():
    print('Loading exam ticks...')
    ticks=load_ticks(str(EXAM_DIR/'BTCUSD_exam_tick.csv'),label='EXAM')
    bars=make_dollar_bars(ticks,DOLLAR_THR)
    feat,cols=build_features_v8(bars)
    avail=[c for c in KEEP if c in cols]; feat=feat[avail]; bars_al=bars.loc[feat.index]
    ohlc=ticks['price'].resample('1min').ohlc().dropna()
    print('1min OHLC: %d bars, $bars: %d' % (len(ohlc), len(bars_al)))
    df=ohlc.copy(); df['price']=df['close']
    ml=lgb.Booster(model_file=str(MDIR/f'v8_long_{HNAME}.txt'))
    ms=lgb.Booster(model_file=str(MDIR/f'v8_short_{HNAME}.txt'))
    pL_dollar=ml.predict(feat[avail].values)
    pS_dollar=ms.predict(feat[avail].values)
    pL=[];pS=[]
    for t in df.index:
        mask=feat.index<=t
        if mask.any():
            i=feat.index.get_loc(feat.index[mask][-1])
            pL.append(pL_dollar[i]);pS.append(pS_dollar[i])
        else: pL.append(0.0);pS.append(0.0)
    df['p_long']=pL;df['p_short']=pS
    pLa=np.array(pL);pSa=np.array(pS)
    sig=np.zeros(len(pLa),dtype=int)
    for k in range(len(pLa)):
        if pLa[k]>TH and pSa[k]<=TH: sig[k]=1
        elif pSa[k]>TH and pLa[k]<=TH: sig[k]=-1
    df['signal']=sig
    nL=int((sig==1).sum());nS=int((sig==-1).sum());nN=int((sig==0).sum())
    print('  5min th=%.2f: P(L)avg=%.3f P(S)avg=%.3f | Long=%d Short=%d Noise=%d | L/S=%.2f' %
          (TH,pLa.mean(),pSa.mean(),nL,nS,nN,nL/max(1,nS)))
    return df,{'pL':pLa,'pS':pSa,'nL':nL,'nS':nS,'nN':nN}

def render_chart(df,info):
    print('Rendering chart...')
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,
        row_heights=[0.55,0.45],vertical_spacing=0.04,
        subplot_titles=['5min OHLC + Signal Markers (th=0.40)','5min P(Long) / P(Short) [független]'])
    # Row 1: OHLC + signal
    fig.add_trace(go.Candlestick(x=df.index,open=df['open'],high=df['high'],
        low=df['low'],close=df['close'],name='OHLC',increasing_line_color=LC,
        decreasing_line_color=SC,line=dict(width=1)),row=1,col=1)
    sig=df['signal'].values
    long_idx=np.where(sig==1)[0]
    short_idx=np.where(sig==-1)[0]
    if len(long_idx):
        fig.add_trace(go.Scatter(x=df.index[long_idx],y=df['low'].iloc[long_idx].values*0.997,
            mode='markers',marker=dict(symbol='triangle-up',size=12,color=LC,line=dict(width=1,color='white')),
            name='Long signal',showlegend=True),row=1,col=1)
    if len(short_idx):
        fig.add_trace(go.Scatter(x=df.index[short_idx],y=df['high'].iloc[short_idx].values*1.003,
            mode='markers',marker=dict(symbol='triangle-down',size=12,color=SC,line=dict(width=1,color='white')),
            name='Short signal',showlegend=True),row=1,col=1)
    # Row 2: probabilities
    fig.add_trace(go.Scatter(x=df.index,y=df['p_long'],
        name='P(Long) [független]',line=dict(color=LC,width=2),showlegend=True),row=2,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df['p_short'],
        name='P(Short) [független]',line=dict(color=SC,width=2),showlegend=True),row=2,col=1)
    fig.add_hline(y=TH,line_dash='dash',line_color='orange',row=2,col=1,
                  annotation_text='th=%.2f' % TH,annotation_position='top left')
    fig.add_hrect(y0=TH-0.02,y1=TH+0.02,line_width=0,fillcolor='orange',opacity=0.1,row=2,col=1)
    # Summary annotation
    summary_txt=('Long: %d  Short: %d  Noise: %d  |  L/S=%.2f  |  avg P(L)=%.3f  avg P(S)=%.3f' %
                 (info['nL'],info['nS'],info['nN'],info['nL']/max(1,info['nS']),
                  info['pL'].mean(),info['pS'].mean()))
    fig.add_annotation(text=summary_txt,xref='paper',yref='paper',
        x=0.01,y=0.99,showarrow=False,font=dict(color=TC,size=12),
        bgcolor='rgba(40,52,66,0.8)',bordercolor=GC,borderwidth=1)
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=BG,plot_bgcolor=BG,
        font=dict(color=TC,size=11),
        height=1000,width=1600,
        title_text='V8 5min Dual-Binary Vizsga — BTCUSD Exam | PT=0.5xATR SL=0.3xATR Jules V5 Strict Wick',
        xaxis2_rangeslider_visible=False,
        xaxis1_rangeslider_visible=False,
        showlegend=True,legend=dict(orientation='h',y=1.02,x=0.3))
    fig.update_xaxes(showgrid=True,gridcolor=GC)
    fig.update_yaxes(showgrid=True,gridcolor=GC)
    out=CDIR/'BTCUSD_v8_5min_vizsga.html'
    fig.write_html(str(out),include_plotlyjs='cdn')
    print('Chart saved: %s' % out)
    return out

def main():
    df,info=build_preds()
    out=render_chart(df,info)
    print('\nChart: %s' % out)
    print('Summary: L=%d S=%d N=%d | L/S=%.2f | avg P(L)=%.3f avg P(S)=%.3f' %
          (info['nL'],info['nS'],info['nN'],info['nL']/max(1,info['nS']),
           info['pL'].mean(),info['pS'].mean()))

if __name__=='__main__': main()
