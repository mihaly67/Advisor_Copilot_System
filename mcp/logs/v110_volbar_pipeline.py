#!/usr/bin/env python3
"""v110_volbar_pipeline.py - Teljes pipeline nullarol, volatility bar-al

Helyes CSV-k (CFD, nem futures!):
  TANITO: .../raw/uj/Scalper_Copilot_MTF_Data_v2.csv (799MB, 06.16-09.01)
  VIZSGA: .../raw/uj/Scalper_Copilot_MTF_Data_kulon_vizsga.csv (74MB, 09.14-09.18)

Bar tipus: VOLATILITY BAR (nem dollar bar!)
  - Kumulatív |delta_price| >= ATR_target -> zarul a bar
  - Adaptiv a volatilitashoz, NEM kell volume!
  - CFD-n nincs volume -> ez az egyetlen helyes megoldas

Feature-k: 18 feat, shift(1) leakfix, ZZ+MTF direkt CSV-bol
"""
import pandas as pd, numpy as np, lightgbm as lgb, joblib, os, sys, json, time, warnings
from sklearn.metrics import confusion_matrix
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === PATHS ===
BASE='/data/dev/projects/z-ai-copilot'
RAW=os.path.join(BASE,'Master_csv','raw','új')
PROC=os.path.join(BASE,'Master_csv','processed')
MOD=os.path.join(BASE,'models','v110_volbar')
DOCS=os.path.join(BASE,'docs','v110_volbar')
for d in [MOD,DOCS,PROC]: os.makedirs(d,exist_ok=True)

RAW_TANITO=os.path.join(RAW,'Scalper_Copilot_MTF_Data_v2.csv')
RAW_VIZSGA=os.path.join(RAW,'Scalper_Copilot_MTF_Data_külön_vizsga.csv')

# === PARAMS ===
ATR_TARGET=3.0        # Volatility bar: cumulative |dprice| >= $3.0 -> bar close
LGBM_PARAMS={'n_estimators':781,'learning_rate':0.0142,'num_leaves':57,
    'max_depth':6,'min_child_samples':24,'colsample_bytree':0.566,
    'class_weight':'balanced','objective':'multiclass',
    'random_state':42,'n_jobs':-1,'verbose':-1}
THL=0.390; THS=0.400; THN=0.400; SW=2
PT=1.5; SL=1.0; MAX_BARS=5

PAL=dict(long='#228B22',short='#B22222',noise='#888888',
    bg='#111111',paper='#000000',grid='#333333',
    zero='#444444',font='white')

FEAT_ORIG=['Tick_Speed','Dist_Micro_R','Dist_Micro_S','Dist_Sec_R','Dist_Sec_S',
    'Dist_Ter_R','Dist_Ter_S','Stoch_State_M1','Upper_Wick_ATR','Lower_Wick_ATR']
FEAT_DIR=['RSI_signed','MACD_Hist_ATR','BB_ZScore','ROC_5','MFI_signed',
    'OBI_ZScore','Price_Vel_ATR','RSI_M15_signed']
FEAT_ALL=FEAT_ORIG+FEAT_DIR

# ============================================================
# STEP 1: Volatility Bar Builder
# ============================================================
def build_volatility_bars(df_tick, atr_target=ATR_TARGET, label=''):
    """Volatility bar: bar closes when cumulative |delta_mid| >= atr_target"""
    print(f'  Building Volatility Bars (ATR_target=${atr_target:.1f}) from {len(df_tick):,} ticks')
    ts=df_tick['Timestamp'].values
    bid=df_tick['Bid'].values; ask=df_tick['Ask'].values
    mid=(bid+ask)/2.0
    spread=ask-bid

    bars=[]; cum_move=0.0; bar=None
    for i in range(len(df_tick)):
        if bar is None:
            bar={'Start_Timestamp':ts[i],'Open':mid[i],'High':mid[i],'Low':mid[i],
                 'Close':mid[i],'Spread':spread[i],'N_ticks':1}
            cum_move=0.0
        else:
            dm=abs(mid[i]-mid[i-1])
            cum_move+=dm
            if mid[i]>bar['High']: bar['High']=mid[i]
            if mid[i]<bar['Low']: bar['Low']=mid[i]
            bar['Close']=mid[i]
            bar['Spread']=spread[i]
            bar['N_ticks']+=1
            if cum_move>=atr_target:
                bar['End_Timestamp']=ts[i]
                bars.append(bar)
                bar={'Start_Timestamp':ts[i],'Open':mid[i],'High':mid[i],'Low':mid[i],
                     'Close':mid[i],'Spread':spread[i],'N_ticks':1}
                cum_move=0.0
    if bar is not None:
        bar['End_Timestamp']=ts[-1]
        bars.append(bar)
    result=pd.DataFrame(bars)
    if len(result)>0:
        sec=(pd.to_datetime(result['End_Timestamp'])-pd.to_datetime(result['Start_Timestamp'])).dt.total_seconds()
        print(f'  {len(result):,} bars | avg {sec.mean():.1f} sec/bar | avg {result["N_ticks"].mean():.1f} ticks/bar')
    return result

# ============================================================
# STEP 2: Feature Engineering (shift(1) leakfix!)
# ============================================================
def compute_features(bars, df_tick_cols=None):
    """Compute 18 features from volatility bars + tick CSV oszlopok.
    
    A tick CSV oszlopai (ZZ+MTF) MAR bent vannak - merge_asof-al hozzárendeljük.
    MINDEN feature shift(1)-el! (leakfix)
    """
    df=bars.copy()
    df['Start_Timestamp']=pd.to_datetime(df['Start_Timestamp'])
    df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
    df=df.sort_values('End_Timestamp').reset_index(drop=True)

    # Merge ZZ+MTF oszlopok a tick CSV-bol (merge_asof backward)
    if df_tick_cols is not None:
        df_tick=df_tick_cols.copy()
        df_tick['Timestamp']=pd.to_datetime(df_tick['Timestamp'],format='%Y.%m.%d %H:%M:%S.%f')
        df_tick=df_tick.sort_values('Timestamp')
        merge_cols=[c for c in ['Micro_R','Micro_S','Sec_R','Sec_S','Ter_R','Ter_S',
            'ATR_M15','RSI_M15','1m_Close','5m_Close','15m_Close','30m_Close'] if c in df_tick.columns]
        df=pd.merge_asof(df,df_tick[['Timestamp']+merge_cols],
            left_on='End_Timestamp',right_on='Timestamp',direction='backward')
        if 'Timestamp' in df.columns: df.drop(columns=['Timestamp'],inplace=True)

    # ATR14
    hl=df['High']-df['Low']
    hc=np.abs(df['High']-df['Close'].shift(1))
    lc=np.abs(df['Low']-df['Close'].shift(1))
    tr=np.max(pd.concat([hl,hc,lc],axis=1),axis=1)
    atr14=tr.rolling(14).mean()+1e-8

    # Tick_Speed (shifted)
    df['Bar_Time_Seconds']=(df['End_Timestamp']-df['Start_Timestamp']).dt.total_seconds().replace(0,1)
    df['Tick_Speed']=(1.0/df['Bar_Time_Seconds']).shift(1)

    # Dist_* (ZZ distances, ATR normalized) - shift(1)!
    cl=df['Close']
    if 'Micro_R' in df.columns:
        df['Dist_Micro_R']=((df['Micro_R']-cl)/atr14).shift(1)
        df['Dist_Micro_S']=((cl-df['Micro_S'])/atr14).shift(1)
        df['Dist_Sec_R']=((df['Sec_R']-cl)/atr14).shift(1)
        df['Dist_Sec_S']=((cl-df['Sec_S'])/atr14).shift(1)
        df['Dist_Ter_R']=((df['Ter_R']-cl)/atr14).shift(1)
        df['Dist_Ter_S']=((cl-df['Ter_S'])/atr14).shift(1)
    else:
        for c in ['Dist_Micro_R','Dist_Micro_S','Dist_Sec_R','Dist_Sec_S','Dist_Ter_R','Dist_Ter_S']:
            df[c]=0.0

    # Stoch (shifted)
    try:
        import ta
        stoch=ta.momentum.StochasticOscillator(high=df['High'],low=df['Low'],close=df['Close'],window=2,smooth_window=3)
        df['Stoch_State_M1']=((stoch.stoch()-50.0)/50.0).shift(1)
    except: df['Stoch_State_M1']=0.0

    # Wick geometry (shifted)
    df['Upper_Wick_ATR']=((df['High']-np.maximum(df['Open'],df['Close']))/atr14).shift(1)
    df['Lower_Wick_ATR']=((np.minimum(df['Open'],df['Close'])-df['Low'])/atr14).shift(1)

    # Micro oscillators (shifted)
    try:
        import ta
        df['Micro_RSI_14']=ta.momentum.RSIIndicator(df['Close'],window=14).rsi().shift(1)
        macd=ta.trend.MACD(df['Close'],window_slow=26,window_fast=12,window_sign=9)
        df['Micro_MACD_Hist']=macd.macd_diff().shift(1)
        bb=ta.volatility.BollingerBands(df['Close'],window=20,window_dev=2)
        df['Micro_BB_ZScore']=((df['Close']-bb.bollinger_mavg())/(df['Close'].rolling(20).std()+1e-9)).shift(1)
        df['Micro_ROC_5']=ta.momentum.ROCIndicator(df['Close'],window=5).roc().shift(1)
        vol_for_mfi=df['N_ticks'] if 'N_ticks' in df.columns else df['High']-df['Low']+1
        df['Micro_MFI_5']=ta.volume.MFIIndicator(high=df['High'],low=df['Low'],close=df['Close'],volume=vol_for_mfi,window=5).money_flow_index().shift(1)
        has_ta=True
    except: has_ta=False

    # OBI (shifted)
    if 'Spread' in df.columns:
        df['OBI_Raw']=0.0  # CFD nincs volume
        df['OBI_ZScore']=0.0
    else:
        df['OBI_ZScore']=0.0

    # Price Velocity (shifted)
    df['Price_Velocity']=(df['Close'].diff(1)/df['Bar_Time_Seconds']).replace([np.inf,-np.inf],0).fillna(0).shift(1)

    # ATR14 shifted for direction features
    atr14s=tr.rolling(14).mean().shift(1)+1e-8

    # 8 Direction features
    if has_ta:
        df['RSI_signed']=(df['Micro_RSI_14']-50.0)/50.0
        df['MACD_Hist_ATR']=df['Micro_MACD_Hist']/atr14s
        df['BB_ZScore']=df['Micro_BB_ZScore']
        df['ROC_5']=df['Micro_ROC_5']
        df['MFI_signed']=(df['Micro_MFI_5']-50.0)/50.0
    else:
        for c in ['RSI_signed','MACD_Hist_ATR','BB_ZScore','ROC_5','MFI_signed']:
            df[c]=0.0
    df['OBI_ZScore_feat']=df['OBI_ZScore']
    df['Price_Vel_ATR']=df['Price_Velocity']/atr14s
    # RSI_M15 direkt CSV-bol (mar shifted ha merge_asof backward)
    if 'RSI_M15' in df.columns:
        df['RSI_M15_signed']=(df['RSI_M15']-50.0)/50.0
    else:
        df['RSI_M15_signed']=0.0

    # Rename OBI feature
    if 'OBI_ZScore_feat' in df.columns:
        df['OBI_ZScore_dir']=df['OBI_ZScore_feat']

    # Select final features
    feat_map={'OBI_ZScore_dir':'OBI_ZScore'}  # alias
    for old,new in feat_map.items():
        if old in df.columns and new not in df.columns:
            df[new]=df[old]

    # Clean
    df.replace([np.inf,-np.inf],np.nan,inplace=True)
    avail=[f for f in FEAT_ALL if f in df.columns]
    df.dropna(subset=avail,inplace=True)
    df.reset_index(drop=True,inplace=True)
    print(f'  {len(df):,} bars, {len(avail)} features available')
    return df, avail

# ============================================================
# STEP 3: Triple Barrier Label
# ============================================================
def apply_triple_barrier(df, pt=PT, sl=SL, max_bars=MAX_BARS):
    print(f'  Triple Barrier: PT=${pt}$, SL=${sl}$, max_bars={max_bars}')
    n=len(df); labels=np.zeros(n,dtype=int)
    hp=df['High'].values; lp=df['Low'].values
    for i in range(n-1):
        entry=df['Open'].iloc[i+1]
        ul=entry+pt; ll=entry-sl; ls=entry-pt; us=entry+sl; hit=0
        for j in range(i+1,min(i+1+max_bars,n)):
            ch=hp[j]; cl=lp[j]
            lpt=ch>=ul; lsl=cl<=ll; spt=cl<=ls; ssl=ch>=us
            if lpt and lsl: lpt=False
            if spt and ssl: spt=False
            if hit==0:
                if lpt and not spt: hit=1; break
                elif spt and not lpt: hit=-1; break
                elif lsl and ssl: break
        labels[i]=hit
    df['Target_Label']=labels
    vc=pd.Series(labels).value_counts(normalize=True)*100
    print(f'  Long={vc.get(1,0):.1f}% Noise={vc.get(0,0):.1f}% Short={vc.get(-1,0):.1f}%')
    return df

# ============================================================
# STEP 4: Threshold + Stability
# ============================================================
def apply_threshold(probs, classes):
    i_s=list(classes).index(0); i_n=list(classes).index(1); i_l=list(classes).index(2)
    ps=probs[:,i_s]; pn=probs[:,i_n]; pl=probs[:,i_l]
    sig=np.full(len(probs),1,dtype=int)
    sig[(pl>THL)&(pl>ps)&(pn<THN)]=2; sig[(ps>THS)&(ps>pl)&(pn<THN)]=0
    return sig,ps,pn,pl

def apply_stability(sig, w=SW):
    s=np.full(len(sig),1,dtype=int)
    for i in range(w-1,len(sig)):
        ww=sig[i-w+1:i+1]
        if len(set(ww))==1 and ww[0]!=1: s[i]=ww[0]
    return s

def eval_detailed(sig, y_true, ps, pn, pl, pt=PT, sl=SL):
    profit=0.0; wins=0; losses=0
    for i in range(len(sig)):
        if sig[i]==1: continue
        ok=(sig[i]==2 and y_true[i]==2)or(sig[i]==0 and y_true[i]==0)
        if ok: profit+=pt; wins+=1
        else: profit-=sl; losses+=1
    t=wins+losses; wr=wins/t*100 if t>0 else 0
    r={'wr':round(wr,1),'profit':round(profit,1),'wins':wins,'losses':losses,'trades':t}
    has=sig!=1
    cm=confusion_matrix(y_true[has],sig[has],labels=[0,1,2]) if has.sum()>0 else np.zeros((3,3),dtype=int)
    r['opposite']=int(cm[0,2]+cm[2,0])
    swap_mask=((sig==2)&(y_true==0))|((sig==0)&(y_true==2))
    correct_mask=((sig==2)&(y_true==2))|((sig==0)&(y_true==0))
    n_swap=int(swap_mask.sum()); n_correct=int(correct_mask.sum())
    r['swap_pct']=round(n_swap/(n_correct+n_swap)*100,1) if (n_correct+n_swap)>0 else 0
    dpl=pl-ps
    r['mean_conviction']=round(float(dpl[sig!=1].mean()),4) if (sig!=1).sum()>0 else 0
    r['confusion']=cm.tolist()
    return r

# ============================================================
# STEP 5: Visualization
# ============================================================
def grid_fix(html):
    for o,n in [('"gridcolor":"white"','"gridcolor":"#333333"'),
               ('"linecolor":"white"','"linecolor":"#444444"'),
               ('"zerolinecolor":"white"','"zerolinecolor":"#444444"')]:
        html=html.replace(o,n)
    return html

def build_viz(name, df_viz, sig, ps, pn, pl, y_viz, out_dir):
    ts=df_viz['End_Timestamp']
    op=df_viz['Open'].values; hi=df_viz['High'].values
    lo=df_viz['Low'].values; cl=df_viz['Close'].values
    n_l=int((sig==2).sum()); n_s=int((sig==0).sum()); n_n=int((sig==1).sum())
    has=sig!=1; acc=(sig[has]==y_viz[has]).mean()*100 if has.sum()>0 else 0.0
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.03,row_heights=[0.7,0.3])
    fig.add_trace(go.Candlestick(x=ts,open=op,high=hi,low=lo,close=cl,
        increasing=dict(line=dict(color=PAL['long']),fillcolor=PAL['long']),
        decreasing=dict(line=dict(color=PAL['short']),fillcolor=PAL['short']),name='OHLC'),row=1,col=1)
    ml=sig==2
    if ml.any(): fig.add_trace(go.Scatter(x=ts[ml],y=cl[ml],mode='markers',
        marker=dict(color=PAL['long'],size=10,symbol='triangle-up'),name=f'Long ({n_l})'),row=1,col=1)
    ms=sig==0
    if ms.any(): fig.add_trace(go.Scatter(x=ts[ms],y=cl[ms],mode='markers',
        marker=dict(color=PAL['short'],size=10,symbol='triangle-down'),name=f'Short ({n_s})'),row=1,col=1)
    fig.add_trace(go.Scatter(x=ts,y=pl,mode='lines',line=dict(color=PAL['long'],width=1),name='P(L)'),row=2,col=1)
   (fig.add_trace(go.Scatter(x=ts,y=ps,mode='lines',line=dict(color=PAL['short'],width=1),name='P(S)'),row=2,col=1)
    fig.add_trace(go.Scatter(x=ts,y=pn,mode='lines',line=dict(color=PAL['noise'],width=1),name='P(N)'),row=2,col=1)
    gc=dict(gridcolor=PAL['grid'],linecolor=PAL['zero'],zerolinecolor=PAL['zero'])
    title=f'Z.ai v1.10 VolBar [{name}] | L:{n_l} S:{n_s} N:{n_n} | WR:{acc:.1f}%'
    fig.update_layout(height=1100,width=1400,title_text=title,plot_bgcolor=PAL['bg'],paper_bgcolor=PAL['paper'],
        font=dict(color=PAL['font']),xaxis_rangeslider_visible=False,xaxis=gc,xaxis2=gc,yaxis=gc,yaxis2=gc,
        margin=dict(l=60,r=30,t=70,b=40),template=dict(layout=dict(xaxis=gc,yaxis=gc)))
    out=os.path.join(out_dir,f'viz_{name}.html')
    fig.write_html(out,include_plotlyjs='cdn')
    with open(out,'r') as fh: html=grid_fix(fh.read())
    with open(out,'w') as fh: fh.write(html)
    print(f'  Viz: {out} ({os.path.getsize(out)/1024:.0f} KB)')

def build_comparison_bar(r_oos, r_viz, out_dir):
    names=['OOS','Vizsga']
    wrs=[r_oos['wr'],r_viz['wr']]; profits=[r_oos['profit'],r_viz['profit']]
    swaps=[r_oos['opposite'],r_viz['opposite']]
    fig=make_subplots(rows=1,cols=3,subplot_titles=('Win Rate %','Profit ($)','Opp Swaps'))
    fig.add_trace(go.Bar(x=names,y=wrs,marker_color=[PAL['long'] if w==max(wrs) else PAL['short'] for w in wrs],
        text=[f'{w:.1f}%' for w in wrs],textposition='outside'),row=1,col=1)
    fig.add_trace(go.Bar(x=names,y=profits,marker_color=[PAL['long'] if p==max(profits) else PAL['short'] for p in profits],
        text=[f'${p:.0f}' for p in profits],Ftextposition='outside'),row=1,col=2)
    fig.add_trace(go.Bar(x=names,y=swaps,marker_color=[PAL['long'] if s==min(swaps) else PAL['short'] for s in swaps],
        text=[str(s) for s in swaps],textposition='outside'),row=1,col=3)
    gc=dict(gridcolor=PAL['grid'],linecolor=PAL['zero'],zerolinecolor=PAL['zero'])
    gap=r_oos['wr']-r_viz['wr']
    fig.update_layout(height=500,width=1200,title_text=f'VolBar ATR=${ATR_TARGET:.1f} | OOS vs Vizsga | WR gap: {gap:+.1f}%',
        plot_bgcolor=PAL['bg'],paper_bgcolor=PAL['paper'],font=dict(color=PAL['font']),
        showlegend=False,template=dict(layout=dict(xaxis=gc,yaxis=gc)))
    out=os.path.join(out_dir,'viz_comparison.html')
    fig.write_html(out,include_plotlyjs='cdn')
    with open(out,'r') as fh: html=grid_fix(fh.read())
    with open(out,'w') as fh: fh.write(html)
    print(f'  Comparison: {out}')

# ============================================================
# MAIN
# ============================================================
def main():
    t0=time.time()
    print('='*70)
    print('  V110 VOLBAR PIPELINE - Teljes pipeline nullarol')
    print(f'  ATR_target = ${ATR_TARGET:.1f} (volatility bar)')
    print('='*70)

    # ==========================================
    # PHASE 1: TANITO pipeline
    # ==========================================
    print('\n' + '='*70)
    print('  PHASE 1: TANITO (CFD v2, 06.16-09.01)')
    print('='*70)

    print('\n[1.1] Tick adat betoltes...')
    df_tick_train=pd.read_csv(RAW_TANITO)
    df_tick_train['Timestamp']=pd.to_datetime(df_tick_train['Timestamp'],format='%Y.%m.%d %H:%M:%S.%f')
    print(f'  {len(df_tick_train):,} ticks, {df_tick_train["Timestamp"].min()} -> {df_tick_train["Timestamp"].max()}')

    print('\n[1.2] Volatility Bars...')
    bars_train=build_volatility_bars(df_tick_train, ATR_TARGET, 'tanito')

    print('\n[1.3] Feature engineering (shift(1) leakfix)...')
    df_train, avail_feats=compute_features(bars_train, df_tick_train)

    print('\n[1.4] Triple Barrier Labeling...')
    df_train=apply_triple_barrier(df_train)
    df_train=df_train.iloc[:-MAX_BARS].reset_index(drop=True)
    print(f'  {len(df_train):,} labeled bars')

    # Save processed
    df_train.to_csv(os.path.join(PROC,'v110_volbar_labeled.csv'),index=False)
    print(f'  Saved: {PROC}/v110_volbar_labeled.csv')

    print('\n[1.5] Train/OOS split + training...')
    si=int(len(df_train)*0.8)
    y_all=(df_train['Target_Label']+1).astype(int).values
    y_tr=y_all[:si]; y_oo=y_all[si:]
    X_tr=df_train.iloc[:si][avail_feats].values
    X_oo=df_train.iloc[si:][avail_feats].values
    print(f'  Train: {si:,} | OOS: {len(df_train)-si:,}')
    print(f'  Train labels: L={int((y_tr==2).sum())} N={int((y_tr==1).sum())} S={int((y_tr==0).sum())}')

    clf=lgb.LGBMClassifier(**LGBM_PARAMS)
    clf.fit(X_tr,y_tr,eval_set=[(X_oo,y_oo)])
    fi=clf.feature_importances_
    top10=[(avail_feats[i],round(fi[i]/fi.sum()*100,2)) for i in np.argsort(fi)[::-1][:10]]
    print('  Feature importance:')
    for i,(n,v) in enumerate(top10):
        tag=' <-- NEW' if n in FEAT_DIR else ''
        print(f'    {i+1:2d}. {n:<20s} {v:.2f}%{tag}')

    print('\n[1.6] OOS ertekeles...')
    probs_oos=clf.predict_proba(X_oo); cl=clf.classes_
    sig_t,ps,pn,pl=apply_threshold(probs_oos,cl)
    sig_f=apply_stability(sig_t)
    r_oos=eval_detailed(sig_f,y_oo,ps,pn,pl)
    print(f'  OOS: WR={r_oos["wr"]}% P=${r_oos["profit"]} T={r_oos["trades"]}')
    print(f'    Opp: {r_oos["opposite"]} ({r_oos["swap_pct"]}%)  Conviction: {r_oos["mean_conviction"]:.4f}')

    joblib.dump(clf,os.path.join(MOD,'lgbm_18feat_volbar.pkl'))
    print(f'  Model: {MOD}/lgbm_18feat_volbar.pkl')

    # OOS viz (last 3 days)
    t_max=df_train['End_Timestamp'].iloc[-1]; t_min=t_max-pd.Timedelta(days=3)
    viz_mask=(df_train['End_Timestamp'].iloc[si:]>=t_min).values
    if viz_mask.sum()>0:
        Xv=X_oo[viz_mask]; dfv=df_train.iloc[si:][viz_mask].copy().reset_index(drop=True)
        pv=clf.predict_proba(Xv)
        st,psv,pnv,plv=apply_threshold(pv,cl); sf=apply_stability(st); yv=y_oo[viz_mask]
        build_viz('OOS_volbar',dfv,sf,psv,pnv,plv,yv,DOCS)

    # ==========================================
    # PHASE 2: VIZSGA pipeline
    # ==========================================
    print('\n' + '='*70)
    print('  PHASE 2: VIZSGA (CFD kulon_vizsga, 09.14-09.18)')
    print('='*70)

    print('\n[2.1] Vizsga tick adat betoltes...')
    df_tick_viz=pd.read_csv(RAW_VIZSGA)
    df_tick_viz['Timestamp']=pd.to_datetime(df_tick_viz['Timestamp'],format='%Y.%m.%d %H:%M:%S.%f')
    print(f'  {len(df_tick_viz):,} ticks, {df_tick_viz["Timestamp"].min()} -> {df_tick_viz["Timestamp"].max()}')

    print('\n[2.2] Volatility Bars...')
    bars_viz=build_volatility_bars(df_tick_viz, ATR_TARGET, 'vizsga')

    print('\n[2.3] Feature engineering...')
    df_viz, avail_viz=compute_features(bars_viz, df_tick_viz)

    print('\n[2.4] Triple Barrier Labeling...')
    df_viz=apply_triple_barrier(df_viz)
    df_viz=df_viz.iloc[:-MAX_BARS].reset_index(drop=True)
    print(f'  {len(df_viz):,} labeled bars')

    print('\n[2.5] Predikcio a vizsgan...')
    avail_both=[f for f in avail_feats if f in df_viz.columns]
    X_viz=df_viz[avail_both].replace([np.inf,-np.inf],np.nan).fillna(0).values
    y_viz=(df_viz['Target_Label']+1).astype(int).values
    probs_viz=clf.predict_proba(X_viz)
    sig_t,ps,pn,pl=apply_threshold(probs_viz,clf.classes_)
    sig_f=apply_stability(sig_t)
    r_viz=eval_detailed(sig_f,y_viz,ps,pn,pl)

    print(f'\n  ================================================')
    print(f'  VIZSGA EREDMENY (ATR_target=${ATR_TARGET:.1f})')
    print(f'  ================================================')
    print(f'  WR={r_viz["wr"]}%  P=${r_viz["profit"]}  T={r_viz["trades"]}')
    print(f'  Opp: {r_viz["opposite"]} ({r_viz["swap_pct"]}%)  Conviction: {r_viz["mean_conviction"]:.4f}')

    cm=np.array(r_viz['confusion'])
    print(f'\n  Konfuzio:')
    print(f'              Act Short  Act Noise  Act Long')
    print(f'  Pred Short {cm[0,0]:>10d}{cm[0,1]:>10d}{cm[0,2]:>10d}')
    print(f'  Pred Noise {cm[1,0]:>10d}{cm[1,1]:>10d}{cm[1,2]:>10d}')
    print(f'  Pred Long  {cm[2,0]:>10d}{cm[2,1]:>10d}{cm[2,2]:>10d}')

    build_viz('VIZSGA_volbar',df_viz,sig_f,ps,pn,pl,y_viz,DOCS)

    # ==========================================
    # PHASE 3: Osszehasonlitas + Statisztikak
    # ==========================================
    print('\n' + '='*70)
    print('  PHASE 3: Osszehasonlitas + Statisztikak')
    print('='*70)

    wr_gap=r_oos['wr']-r_viz['wr']; p_gap=r_oos['profit']-r_viz['profit']
    print(f'\n  +------------------+----------+-----------+')
    print(f'  | Metrika          | OOS      | Vizsga    |')
    print(f'  +------------------+----------+-----------+')
    print(f'  | WR               | {r_oos["wr"]:>6.1f}%  | {r_viz["wr"]:>6.1f}%   |')
    print(f'  | Profit           | ${r_oos["profit"]:>6.0f}  | ${r_viz["profit"]:>6.0f}   |')
    print(f'  | Trades           | {r_oos["trades"]:>6d}  | {r_viz["trades"]:>6d}   |')
    print(f'  | Opp swaps        | {r_oos["opposite"]:>6d}  | {r_viz["opposite"]:>6d}   |')
    print(f'  | Swap%            | {r_oos["swap_pct"]:>5.1f}%  | {r_viz["swap_pct"]:>5.1f}%   |')
    print(f'  | Conviction       | {r_oos["mean_conviction"]:>6.4f}  | {r_viz["mean_conviction"]:>6.4f}   |')
    print(f'  +------------------+----------+-----------+')
    print(f'  | WR gap           | {wr_gap:>+5.1f}%             |')
    print(f'  | Profit gap       | ${p_gap:>+6.0f}             |')
    print(f'  +------------------+----------+-----------+')

    if wr_gap>5: diag='OVERFITTING (>5% gap)'
    elif wr_gap>2: diag='enyhe overfitting (2-5%)'
    elif wr_gap>-2: diag='STABIL (<2% gap)'
    else: diag='Vizsgan JOBB!'
    print(f'\n  Diagnoszis: {diag}')

    build_comparison_bar(r_oos, r_viz, DOCS)

    # Save results
    results={'timestamp':time.strftime('%Y-%m-%d %H:%M:%S'),
             'atr_target':ATR_TARGET,'bar_type':'volatility',
             'oos':r_oos,'vizsga':r_viz,
             'gap_wr':round(wr_gap,1),'gap_profit':round(p_gap,1),
             'diagnosis':diag,'feature_importance':top10,
             'features':avail_feats,'threshold':{'THL':THL,'THS':THS,'THN':THN,'SW':SW},
             'label':{'PT':PT,'SL':SL,'MAX_BARS':MAX_BARS}}
    with open(os.path.join(DOCS),'volbar_results.json'),'w') as f:
        json.dump(results,f,indent=2,default=str)
    print(f'\n  Results: {DOCS}/volbar_results.json')

    print(f'\n{"="*70}')
    print(f'  V110 VOLBAR PIPELINE KESZ - {time.time()-t0:.0f}s')
    print(f'  Model: {MOD}/lgbm_18feat_volbar.pkl')
    print(f'  Output: {DOCS}/')
    print(f'{"="*70}')

if __name__=='__main__': main()
