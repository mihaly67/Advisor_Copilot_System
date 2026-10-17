#!/usr/bin/env python3
"""Generator script for v110_vizsga_eval.py"""
import os

TARGET = '/data/dev/projects/z-ai-copilot/src/v110_vizsga_eval.py'

code = r'''#!/usr/bin/env python3
"""v110_vizsga_eval.py - Leakfix + Vizsga CSV mint VEGSO donteshozo

FAZIS 1: Modell training CSV oszlopokbol (MAR shiftelve = leakfix)
FAZIS 2: Vizsga CSV pipeline (teljes független teszt, shift(1)!)
FAZIS 3: Osszehasonlitas + jelentes
"""
import pandas as pd, numpy as np, lightgbm as lgb, joblib, os, sys, json, time, warnings
from sklearn.metrics import confusion_matrix
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE='/data/dev/projects/z-ai-copilot'
RAW=os.path.join(BASE,'Master_csv','raw')
PROC=os.path.join(BASE,'Master_csv','processed')
MOD=os.path.join(BASE,'models','v110_vizsga')
DOCS=os.path.join(BASE,'docs','v110_vizsga')
for d in [MOD,DOCS]: os.makedirs(d,exist_ok=True)

LGBM_PARAMS={'n_estimators':781,'learning_rate':0.0142,'num_leaves':57,
    'max_depth':6,'min_child_samples':24,'colsample_bytree':0.566,
    'class_weight':'balanced','objective':'multiclass',
    'random_state':42,'n_jobs':-1,'verbose':-1}
THL=0.390; THS=0.400; THN=0.400; SW=2
DOLLAR_THRESHOLD=1746000.0
PAL=dict(long='#228B22',short='#B22222',noise='#888888',
    long_lt='#32CD32',short_lt='#FF4444',
    bg='#111111',paper='#000000',grid='#333333',
    zero='#444444',legend_bg='#222222',font='white')
FEAT_ORIG=['Tick_Speed','Dist_Micro_R','Dist_Micro_S','Dist_Sec_R','Dist_Sec_S',
    'Dist_Ter_R','Dist_Ter_S','Stoch_State_M1','Upper_Wick_ATR','Lower_Wick_ATR']
FEAT_DIR=['RSI_signed','MACD_Hist_ATR','BB_ZScore','ROC_5','MFI_signed',
    'OBI_ZScore','Price_Vel_ATR','RSI_M15_signed']
FEAT_ALL=FEAT_ORIG+FEAT_DIR

def compute_dir_features(df):
    f={}
    hl=df['High']-df['Low']; hc=np.abs(df['High']-df['Close'].shift(1))
    lc=np.abs(df['Low']-df['Close'].shift(1))
    tr=np.max(pd.concat([hl,hc,lc],axis=1),axis=1)
    atr14=tr.rolling(14).mean().shift(1)+1e-8
    f['RSI_signed']=(df['Micro_RSI_14']-50.0)/50.0
    f['MACD_Hist_ATR']=df['Micro_MACD_Hist']/atr14
    f['BB_ZScore']=df['Micro_BB_ZScore']
    f['ROC_5']=df['Micro_ROC_5']
    f['MFI_signed']=(df['Micro_MFI_5']-50.0)/50.0
    f['OBI_ZScore']=df['OBI_ZScore']
    f['Price_Vel_ATR']=df['Price_Velocity']/atr14
    f['RSI_M15_signed']=(df['RSI_M15']-50.0)/50.0
    return pd.DataFrame(f)

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

def eval_sig(sig, y_true, pt=1.5, sl=1.0):
    profit=0.0; wins=0; losses=0
    for i in range(len(sig)):
        if sig[i]==1: continue
        ok=(sig[i]==2 and y_true[i]==2)or(sig[i]==0 and y_true[i]==0)
        if ok: profit+=pt; wins+=1
        else: profit-=sl; losses+=1
    t=wins+losses; wr=wins/t*100 if t>0 else 0
    return {'wr':round(wr,1),'profit':round(profit,1),'wins':wins,'losses':losses,'trades':t}

def eval_detailed(sig, y_true, ps, pn, pl, pt=1.5, sl=1.0):
    r=eval_sig(sig,y_true,pt,sl)
    has=sig!=1
    cm=confusion_matrix(y_true[has],sig[has],labels=[0,1,2]) if has.sum()>0 else np.zeros((3,3),dtype=int)
    opp=int(cm[0,2]+cm[2,0])
    swap_mask=((sig==2)&(y_true==0))|((sig==0)&(y_true==2))
    correct_mask=((sig==2)&(y_true==2))|((sig==0)&(y_true==0))
    n_swap=int(swap_mask.sum()); n_correct=int(correct_mask.sum())
    swap_pct=n_swap/(n_correct+n_swap)*100 if (n_correct+n_swap)>0 else 0
    dpl=pl-ps
    r['opposite']=opp; r['swap_pct']=round(swap_pct,1)
    r['swap_gap']=round(float(dpl[swap_mask].mean()),4) if swap_mask.sum()>0 else 0
    r['correct_gap']=round(float(dpl[correct_mask].mean()),4) if correct_mask.sum()>0 else 0
    r['confusion']=cm.tolist()
    r['mean_conviction']=round(float(dpl[sig!=1].mean()),4) if (sig!=1).sum()>0 else 0
    return r

def build_dollar_bars(df_tick, threshold=DOLLAR_THRESHOLD):
    print(f"  Building Dollar Bars (${threshold:,.0f}) from {len(df_tick):,} rows")
    bars=[]; current_dv=0.0; bar=None
    ts=df_tick['Timestamp'].values; bid=df_tick['Bid'].values; ask=df_tick['Ask'].values
    bv=df_tick['Bid_Volume'].values; av=df_tick['Ask_Volume'].values
    for i in range(len(df_tick)):
        mid=(bid[i]+ask[i])/2.0; total_vol=bv[i]+av[i]; d_val=mid*total_vol
        if d_val<=0: continue
        if current_dv==0.0:
            bar={'Start_Timestamp':ts[i],'Open':mid,'High':mid,'Low':mid,
                 'Bid_Volume':0,'Ask_Volume':0,'Total_Volume':0,'Total_Dollar_Value':0.0}
        current_dv+=d_val; bar['Bid_Volume']+=bv[i]; bar['Ask_Volume']+=av[i]
        bar['Total_Volume']+=total_vol; bar['Total_Dollar_Value']+=d_val
        if mid>bar['High']: bar['High']=mid
        if mid<bar['Low']: bar['Low']=mid
        if current_dv>=threshold:
            bar['End_Timestamp']=ts[i]; bar['Close']=mid
            bars.append(bar); current_dv=0.0; bar=None
    if bar is not None and bar['Total_Volume']>0:
        bar['End_Timestamp']=ts[-1]; bar['Close']=mid; bars.append(bar)
    result=pd.DataFrame(bars)
    if len(result)>0:
        sec=(pd.to_datetime(result['End_Timestamp'])-pd.to_datetime(result['Start_Timestamp'])).dt.total_seconds()
        print(f"  {len(result):,} Dollar Bars (avg {sec.mean():.1f} sec/bar)")
    return result

def compute_vizsga_features(dollar_bars, df_zz):
    """Feature engineering - MINDEN shift(1)-el! (LEAKFIX)"""
    print("  Feature Engineering: VIZSGA pipeline (shift(1) leakfix)")
    df=dollar_bars.copy()
    df['Start_Timestamp']=pd.to_datetime(df['Start_Timestamp'])
    df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
    total_vol=df['Total_Volume']+1e-9
    df['OBI_Raw']=(df['Ask_Volume']-df['Bid_Volume'])/total_vol
    df['OBI_ZScore']=((df['OBI_Raw']-df['OBI_Raw'].rolling(100).mean())/(df['OBI_Raw'].rolling(100).std()+1e-9)).shift(1)
    df['Bar_Time_Seconds']=(df['End_Timestamp']-df['Start_Timestamp']).dt.total_seconds().replace(0,1)
    df['Price_Velocity']=(df['Close'].diff(1)/df['Bar_Time_Seconds']).replace([np.inf,-np.inf],0).fillna(0).shift(1)
    df['Tick_Speed']=(1.0/df['Bar_Time_Seconds']).shift(1)
    hl=df['High']-df['Low']; hc=np.abs(df['High']-df['Close'].shift(1))
    lc=np.abs(df['Low']-df['Close'].shift(1))
    tr=np.max(pd.concat([hl,hc,lc],axis=1),axis=1)
    df['ATR_Proxy']=tr.rolling(15).mean().shift(1)
    has_ta=True
    try:
        import ta
        df['Micro_RSI_14']=ta.momentum.RSIIndicator(df['Close'],window=14).rsi().shift(1)
        macd=ta.trend.MACD(df['Close'],window_slow=26,window_fast=12,window_sign=9)
        df['Micro_MACD_Hist']=macd.macd_diff().shift(1)
        bb=ta.volatility.BollingerBands(df['Close'],window=20,window_dev=2)
        df['Micro_BB_ZScore']=((df['Close']-bb.bollinger_mavg())/(df['Close'].rolling(20).std()+1e-9)).shift(1)
        df['Micro_ROC_5']=ta.momentum.ROCIndicator(df['Close'],window=5).roc().shift(1)
        df['Micro_MFI_5']=ta.volume.MFIIndicator(high=df['High'],low=df['Low'],close=df['Close'],volume=df['Total_Volume'],window=5).money_flow_index().shift(1)
    except ImportError:
        print("  Warning: ta lib not available"); has_ta=False
    df_zz=df_zz.copy(); df_zz['Time']=pd.to_datetime(df_zz['Time']); df_zz=df_zz.sort_values('Time')
    df=df.sort_values('End_Timestamp')
    df=pd.merge_asof(df,df_zz[['Time','Micro_R','Micro_S','Sec_R','Sec_S','Ter_R','Ter_S']],
                      left_on='End_Timestamp',right_on='Time',direction='backward')
    if 'Time' in df.columns: df.drop(columns=['Time'],inplace=True)
    atr14=tr.rolling(14).mean().shift(1)+1e-8
    cl=df['Close']
    df['Dist_Micro_R']=(df['Micro_R']-cl)/atr14; df['Dist_Micro_S']=(cl-df['Micro_S'])/atr14
    df['Dist_Sec_R']=(df['Sec_R']-cl)/atr14; df['Dist_Sec_S']=(cl-df['Sec_S'])/atr14
    df['Dist_Ter_R']=(df['Ter_R']-cl)/atr14; df['Dist_Ter_S']=(cl-df['Ter_S'])/atr14
    for f in ['Dist_Micro_R','Dist_Micro_S','Dist_Sec_R','Dist_Sec_S','Dist_Ter_R','Dist_Ter_S']:
        df[f]=df[f].shift(1)
    df['Upper_Wick_ATR']=((df['High']-np.maximum(df['Open'],df['Close']))/atr14).shift(1)
    df['Lower_Wick_ATR']=((np.minimum(df['Open'],df['Close'])-df['Low'])/atr14).shift(1)
    if has_ta:
        import ta
        stoch=ta.momentum.StochasticOscillator(high=df['High'],low=df['Low'],close=df['Close'],window=2,smooth_window=3)
        df['Stoch_State_M1']=((stoch.stoch()-50.0)/50.0).shift(1)
        df['RSI_M15']=ta.momentum.RSIIndicator(df['Close'],window=42).rsi().shift(1)
    else:
        df['Stoch_State_M1']=0.0; df['RSI_M15']=50.0
    atr14d=tr.rolling(14).mean().shift(1)+1e-8
    df['RSI_signed']=(df['Micro_RSI_14']-50.0)/50.0
    df['MACD_Hist_ATR']=df['Micro_MACD_Hist']/atr14d
    df['BB_ZScore']=df['Micro_BB_ZScore']; df['ROC_5']=df['Micro_ROC_5']
    df['MFI_signed']=(df['Micro_MFI_5']-50.0)/50.0; df['OBI_ZScore']=df['OBI_ZScore']
    df['Price_Vel_ATR']=df['Price_Velocity']/atr14d
    df['RSI_M15_signed']=(df['RSI_M15']-50.0)/50.0
    df.replace([np.inf,-np.inf],np.nan,inplace=True)
    df.dropna(subset=FEAT_ALL,inplace=True); df.reset_index(drop=True,inplace=True)
    print(f"  {len(df):,} bars, {len(FEAT_ALL)} features")
    return df

def apply_triple_barrier(df, pt=1.5, sl=1.0, max_bars=5):
    print(f"  Triple Barrier: PT={pt}$, SL={sl}$, max_bars={max_bars}")
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
    print(f"  Long={vc.get(1,0):.1f}% Noise={vc.get(0,0):.1f}% Short={vc.get(-1,0):.1f}%")
    return df

def grid_fix(html):
    for o,n in [('"gridcolor":"white"','"gridcolor":"#333333"'),
               ('"linecolor":"white"','"linecolor":"#444444"'),
               ('"zerolinecolor":"white"','"zerolinecolor":"#444444"')]:
        html=html.replace(o,n)
    return html

def build_viz(name, df_viz, sig, ps, pn, pl, y_viz, out_dir):
    ts=df_viz['End_Timestamp'] if 'End_Timestamp' in df_viz.columns else df_viz['Start_Timestamp']
    op=df_viz['Open'].values; hi=df_viz['High'].values
    lo=df_viz['Low'].values; cl=df_viz['Close'].values
    n_l=int((sig==2).sum()); n_s=int((sig==0).sum())
    has=sig!=1; acc=(sig[has]==y_viz[has]).mean()*100 if has.sum()>0 else 0.0
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.03,row_heights=[0.7,0.3])
    fig.add_trace(go.Candlestick(x=ts,open=op,high=hi,low=lo,close=cl,
        increasing=dict(line=dict(color=PAL['long']),fillcolor=PAL['long']),
        decreasing=dict(line=dict(color=PAL['short']),fillcolor=PAL['short']),name='OHLC'),row=1,col=1)
    ml=sig==2
    if ml.any(): fig.add_trace(go.Scatter(x=ts[ml],y=cl[ml],mode='markers',
        marker=dict(color=PAL['long'],size=12,symbol='triangle-up'),name=f'Long ({n_l})'),row=1,col=1)
    ms=sig==0
    if ms.any(): fig.add_trace(go.Scatter(x=ts[ms],y=cl[ms],mode='markers',
        marker=dict(color=PAL['short'],size=12,symbol='triangle-down'),name=f'Short ({n_s})'),row=1,col=1)
    fig.add_trace(go.Scatter(x=ts,y=pl,mode='lines',line=dict(color=PAL['long'],width=1.5),name='P(Long)'),row=2,col=1)
    fig.add_trace(go.Scatter(x=ts,y=ps,mode='lines',line=dict(color=PAL['short'],width=1.5),name='P(Short)'),row=2,col=1)
    fig.add_trace(go.Scatter(x=ts,y=pn,mode='lines',line=dict(color=PAL['noise'],width=1.5),name='P(Noise)'),row=2,col=1)
    gc=dict(gridcolor=PAL['grid'],linecolor=PAL['zero'],zerolinecolor=PAL['zero'])
    title=f'Z.ai v1.10 [{name}] | L:{n_l} S:{n_s} N={int((sig==1).sum())} | WR:{acc:.1f}%'
    fig.update_layout(height=1100,width=1400,title_text=title,plot_bgcolor=PAL['bg'],paper_bgcolor=PAL['paper'],
        font=dict(color=PAL['font']),xaxis_rangeslider_visible=False,xaxis=gc,xaxis2=gc,yaxis=gc,yaxis2=gc,
        margin=dict(l=60,r=30,t=70,b=40),template=dict(layout=dict(xaxis=gc,yaxis=gc)))
    out=os.path.join(out_dir,f'viz_{name}.html')
    fig.write_html(out,include_plotlyjs='cdn')
    with open(out,'r') as fh: html=grid_fix(fh.read())
    with open(out,'w') as fh: fh.write(html)
    print(f'  Viz: {out} ({os.path.getsize(out)/1024:.0f} KB)')

def main():
    t0=time.time()
    print('='*70)
    print('  V110 VIZSGA EVAL - Leakfix + Vizsga CSV mint VEGSO donteshozo')
    print('='*70)

    # FAZIS 1
    print('\n  FAZIS 1: Modell training (CSV direkt = leakfix)')
    print('  ' + '='*60)
    print('\n[1.1] Adat betoltes...')
    df_main=pd.read_csv(os.path.join(PROC,'jules_v110_labeled.csv'))
    df_main['End_Timestamp']=pd.to_datetime(df_main['End_Timestamp'])
    df_main['Start_Timestamp']=pd.to_datetime(df_main['Start_Timestamp'])
    df_main.sort_values('End_Timestamp',inplace=True); df_main.reset_index(drop=True,inplace=True)
    print(f'  {len(df_main):,} bars, {df_main["Start_Timestamp"].min()} -> {df_main["Start_Timestamp"].max()}')

    print('\n[1.2] Features (CSV direkt + direction)...')
    feat_orig_df=df_main[FEAT_ORIG].copy()
    feat_dir_df=compute_dir_features(df_main)
    feat_all=pd.concat([feat_orig_df,feat_dir_df],axis=1)
    feat_all=feat_all.replace([np.inf,-np.inf],np.nan).fillna(0)

    print('\n[1.3] Lookahead sanity check...')
    price_diff=df_main['Close'].diff(1).shift(-1).fillna(0)
    for f in FEAT_ALL[:5]:
        corr=np.corrcoef(feat_all[f].fillna(0).values,price_diff.values)[0,1]
        tag='WARNING HIGH!' if abs(corr)>0.15 else 'OK'
        print(f'  corr({f}, future_price_change) = {corr:.4f} [{tag}]')

    print('\n[1.4] Train/OOS split + training...')
    si=int(len(df_main)*0.8)
    y_all=(df_main['Target_Label']+1).astype(int).values
    y_tr=y_all[:si]; y_oo=y_all[si:]
    X_tr=feat_all.iloc[:si].values; X_oo=feat_all.iloc[si:].values
    print(f'  Train: {si:,} | OOS: {len(df_main)-si:,}')

    clf=lgb.LGBMClassifier(**LGBM_PARAMS)
    clf.fit(X_tr,y_tr,eval_set=[(X_oo,y_oo)])
    fi=clf.feature_importances_
    top10=[(FEAT_ALL[i],round(fi[i]/fi.sum()*100,2)) for i in np.argsort(fi)[::-1][:10]]
    print('  Feature importance top 10:')
    for i,(n,v) in enumerate(top10):
        tag=' <-- NEW' if n in FEAT_DIR else ''
        print(f'    {i+1:2d}. {n:<20s} {v:.2f}%{tag}')

    print('\n[1.5] OOS ertekeles...')
    probs_oos=clf.predict_proba(X_oo); cl=clf.classes_
    sig_t,ps,pn,pl=apply_threshold(probs_oos,cl)
    sig_f=apply_stability(sig_t)
    r_oos=eval_detailed(sig_f,y_oo,ps,pn,pl)
    print(f'  OOS: WR={r_oos["wr"]}% P=${r_oos["profit"]} T={r_oos["trades"]}')
    print(f'    Opp swaps: {r_oos["opposite"]} ({r_oos["swap_pct"]}%)')
    print(f'    P(L)-P(S): swap={r_oos["swap_gap"]:.4f} correct={r_oos["correct_gap"]:.4f}')

    joblib.dump(clf,os.path.join(MOD,'lgbm_18feat_leakfix.pkl'))
    print(f'  Model: {MOD}/lgbm_18feat_leakfix.pkl')

    t_max=df_main['End_Timestamp'].iloc[-1]; t_min=t_max-pd.Timedelta(days=3)
    viz_mask=(df_main['End_Timestamp'].iloc[si:]>=t_min).values
    if viz_mask.sum()>0:
        Xv=X_oo[viz_mask]; dfv=df_main.iloc[si:][viz_mask].copy().reset_index(drop=True)
        pv=clf.predict_proba(Xv)
        st,psv,pnv,plv=apply_threshold(pv,cl); sf=apply_stability(st); yv=y_oo[viz_mask]
        build_viz('OOS_leakfix',dfv,sf,psv,pnv,plv,yv,DOCS)

    # FAZIS 2
    print('\n  FAZIS 2: VIZSGA CSV - Teljes független pipeline')
    print('  ' + '='*60)

    print('\n[2.1] Vizsga CSV betoltese...')
    vizsga_csv=os.path.join(RAW,'Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv')
    if not os.path.exists(vizsga_csv):
        vizsga_csv='/data/dev/projects/scalper-copilot/Master_csv/raw/Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv'
    df_viz_tick=pd.read_csv(vizsga_csv)
    df_viz_tick['Timestamp']=pd.to_datetime(df_viz_tick['Timestamp'],format='%Y.%m.%d %H:%M:%S.%f')
    print(f'  {len(df_viz_tick):,} rows, {df_viz_tick["Timestamp"].min()} -> {df_viz_tick["Timestamp"].max()}')

    print('\n[2.2] ZZ adat...')
    zz_csv=os.path.join(RAW,'Master_ZigZag_GCEQ26_M1.csv')
    if not os.path.exists(zz_csv):
        zz_csv='/data/dev/projects/scalper-copilot/Master_csv/raw/Master_ZigZag_GCEQ26_M1.csv'
    df_zz=pd.read_csv(zz_csv)
    df_zz['Time']=pd.to_datetime(df_zz['Time'],format='%Y.%m.%d %H:%M:%S')
    viz_start=df_viz_tick['Timestamp'].min()-pd.Timedelta(hours=1)
    viz_end=df_viz_tick['Timestamp'].max()+pd.Timedelta(hours=1)
    df_zz_viz=df_zz[(df_zz['Time']>=viz_start)&(df_zz['Time']<=viz_end)].copy().reset_index(drop=True)
    print(f'  ZZ vizsga: {len(df_zz_viz):,} bars')

    print('\n[2.3] Dollar Bars...')
    db_viz=build_dollar_bars(df_viz_tick)
    if len(db_viz)==0:
        print('  HIBA: Nem sikerult dollar bar-t generalni!'); sys.exit(1)

    print('\n[2.4] Feature engineering (shift(1) leakfix)...')
    df_viz_feat=compute_vizsga_features(db_viz, df_zz_viz)

    print('\n[2.5] Triple Barrier Labeling...')
    df_viz_lab=apply_triple_barrier(df_viz_feat)
    df_viz_lab=df_viz_lab.iloc[:-5].reset_index(drop=True)
    print(f'  {len(df_viz_lab):,} labeled bars')

    print('\n[2.6] Predikcio a vizsgan...')
    X_viz=df_viz_lab[FEAT_ALL].replace([np.inf,-np.inf],np.nan).fillna(0).values
    y_viz=(df_viz_lab['Target_Label']+1).astype(int).values
    probs_viz=clf.predict_proba(X_viz); cl_viz=clf.classes_
    sig_t_v,ps_v,pn_v,pl_v=apply_threshold(probs_viz,cl_viz)
    sig_f_v=apply_stability(sig_t_v)
    r_viz=eval_detailed(sig_f_v,y_viz,ps_v,pn_v,pl_v)

    print(f'\n  ================================================')
    print(f'  VIZSGA CSV EREDMENY (VEGSO donteshozo)')
    print(f'  ================================================')
    print(f'  WR={r_viz["wr"]}%  P=${r_viz["profit"]}  T={r_viz["trades"]}')
    print(f'  Opp swaps: {r_viz["opposite"]} ({r_viz["swap_pct"]}%)')
    print(f'  P(L)-P(S): swap={r_viz["swap_gap"]:.4f} correct={r_viz["correct_gap"]:.4f}')
    cm=np.array(r_viz['confusion'])
    print(f'\n  Konfuzio:')
    print(f'              Act Short  Act Noise  Act Long')
    print(f'  Pred Short {cm[0,0]:>10d}{cm[0,1]:>10d}{cm[0,2]:>10d}')
    print(f'  Pred Noise {cm[1,0]:>10d}{cm[1,1]:>10d}{cm[1,2]:>10d}')
    print(f'  Pred Long  {cm[2,0]:>10d}{cm[2,1]:>10d}{cm[2,2]:>10d}')

    build_viz('VIZSGA_independent',df_viz_lab,sig_f_v,ps_v,pn_v,pl_v,y_viz,DOCS)

    # FAZIS 3
    print('\n  FAZIS 3: Osszehasonlitas')
    print('  ' + '='*60)
    wr_gap=r_oos['wr']-r_viz['wr']; p_gap=r_oos['profit']-r_viz['profit']
    print(f'\n  OOS WR:    {r_oos["wr"]:>6.1f}%  P=${r_oos["profit"]:>8.0f}  T={r_oos["trades"]:>6d}')
    print(f'  Vizsga WR: {r_viz["wr"]:>6.1f}%  P=${r_viz["profit"]:>8.0f}  T={r_viz["trades"]:>6d}')
    print(f'  Gap:       {wr_gap:>+5.1f}%  dP=${p_gap:>+8.0f}')
    if wr_gap>5: print('  NAGY GAP (>5%) -> overfitting!')
    elif wr_gap>2: print('  Eszreveheto gap (2-5%) -> enyhe overfitting')
    else: print('  Kis gap (<2%) -> modell stabil')

    conviction_gap=r_oos['mean_conviction']-r_viz['mean_conviction']
    print(f'  Dir_Conviction: OOS={r_oos["mean_conviction"]:.4f} Vizsga={r_viz["mean_conviction"]:.4f} Gap={conviction_gap:+.4f}')

    results={'timestamp':time.strftime('%Y-%m-%d %H:%M:%S'),'oos':r_oos,'vizsga':r_viz,
             'gap_wr':round(wr_gap,1),'gap_profit':round(p_gap,1),
             'feature_importance':top10,'leakfix':True,'shift1':True,
             'features':FEAT_ALL,'threshold':{'THL':THL,'THS':THS,'THN':THN,'SW':SW}}
    with open(os.path.join(DOCS,'vizsga_results.json'),'w') as f:
        json.dump(results,f,indent=2,default=str)
    print(f'  Results: {DOCS}/vizsga_results.json')

    fig=make_subplots(rows=1,cols=3,subplot_titles=('Win Rate %','Profit ($)','Opposite Swaps'))
    names=['OOS (leakfix)','Vizsga']
    wrs=[r_oos['wr'],r_viz['wr']]; profits=[r_oos['profit'],r_viz['profit']]
    swaps=[r_oos['opposite'],r_viz['opposite']]
    fig.add_trace(go.Bar(x=names,y=wrs,marker_color=[PAL['long'] if w==max(wrs) else PAL['short'] for w in wrs],
        text=[f'{w:.1f}%' for w in wrs],textposition='outside'),row=1,col=1)
    fig.add_trace(go.Bar(x=names,y=profits,marker_color=[PAL['long'] if p==max(profits) else PAL['short'] for p in profits],
        text=[f'${p:.0f}' for p in profits],textposition='outside'),row=1,col=2)
    fig.add_trace(go.Bar(x=names,y=swaps,marker_color=[PAL['long'] if s==min(swaps) else PAL['short'] for s in swaps],
        text=[str(s) for s in swaps],textposition='outside'),row=1,col=3)
    gc=dict(gridcolor=PAL['grid'],linecolor=PAL['zero'],zerolinecolor=PAL['zero'])
    fig.update_layout(height=500,width=1200,title_text=f'V1.10 Leakfix - OOS vs Vizsga | WR gap: {wr_gap:+.1f}%',
        plot_bgcolor=PAL['bg'],paper_bgcolor=PAL['paper'],font=dict(color=PAL['font']),
        showlegend=False,template=dict(layout=dict(xaxis=gc,yaxis=gc)))
    out_cmp=os.path.join(DOCS,'viz_comparison.html')
    fig.write_html(out_cmp,include_plotlyjs='cdn')
    with open(out_cmp,'r') as fh: html=grid_fix(fh.read())
    with open(out_cmp,'w') as fh: fh.write(html)
    print(f'  Comparison: {out_cmp}')

    print(f'\n{"="*70}')
    print(f'  V110 VIZSGA EVAL KESZ - {time.time()-t0:.0f}s')
    print(f'  Model: {MOD}/lgbm_18feat_leakfix.pkl')
    print(f'  Output: {DOCS}/')
    print(f'{"="*70}')

if __name__=='__main__': main()
'''

with open(TARGET, 'w') as f:
    f.write(code)
print(f'Written {len(code)} bytes to {TARGET}')
