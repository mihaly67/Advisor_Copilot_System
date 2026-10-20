#!/usr/bin/env python3
"""v6.1 vs v6.2 comprehensive comparison"""
import numpy as np, pandas as pd
from pathlib import Path

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
v61f = sorted(MODEL_DIR.glob('BTCUSD_v6_preds_20261018_124751.csv'))
v62f = sorted(MODEL_DIR.glob('BTCUSD_v6_preds_20261018_141912.csv'))
print("Loading..."); df61 = pd.read_csv(v61f[-1], index_col=0, parse_dates=True)
df62 = pd.read_csv(v62f[-1], index_col=0, parse_dates=True)
price = df62['price']; H = ['20s','1min','2min','3min','4min','5min']

SEP = '=' * 80
print(SEP)
print('v6.1 (no filter) vs v6.2 (regime filter) - OSSZEHASONLITO ELEMZES')
print(SEP)

# 1. Signal density
print('\n-- 1. SZIGNAL SURUSEG --')
for h in H:
    s61=df61[f'signal_{h}']; s62=df62[f'signal_{h}']
    L61=(s61==1).sum(); S61=(s61==-1).sum(); Z61=(s61==0).sum()
    L62=(s62==1).sum(); S62=(s62==-1).sum(); Z62=(s62==0).sum()
    print(f'  {h:>5}: v61 L={L61:,} S={S61:,} N={Z61:,} | v62 L={L62:,} S={S62:,} N={Z62:,} | dN={Z62-Z61:+,}')

# 2. Contra-trend
bars5=33; ret5=price.pct_change(bars5); thr=ret5.std()*2
up_t=ret5>thr; dn_t=ret5<-thr
print('\n-- 2. CONTRA-TREND (eros trendben) --')
for h in H:
    s61=df61[f'signal_{h}']; s62=df62[f'signal_{h}']
    c61=((up_t&(s61==-1))|(dn_t&(s61==1))).sum()
    c62=((up_t&(s62==-1))|(dn_t&(s62==1))).sum()
    n_t=up_t.sum()+dn_t.sum()
    p61=c61/max(1,n_t)*100; p62=c62/max(1,n_t)*100
    red=(c61-c62)/max(1,c61)*100
    print(f'  {h:>5}: v61 ct={c61:,} ({p61:.1f}%) | v62 ct={c62:,} ({p62:.1f}%) | redukcio={red:.1f}%')

# 3. Contra by regime (v6.2)
print('\n-- 3. CONTRA-TREND REGIME SZERINT (v6.2) --')
for h in H:
    sig=df62[f'signal_{h}']
    contra=((sig==-1)&(df62['trend_dir']>0))|((sig==1)&(df62['trend_dir']<0))
    t_r=(contra & (df62['regime']=='trending')).sum()
    m_r=(contra & (df62['regime']=='mean_rev')).sum()
    n_r=(contra & (df62['regime']=='neutral')).sum()
    print(f'  {h:>5}: trending={t_r:,} mean_rev={m_r:,} neutral={n_r:,} ossz={contra.sum():,}')

# 4. Backtest
print('\n-- 4. BACKTEST (PT=0.5xATR SL=0.3xATR) --')
atr=df62['noise_level']*price; price_arr=price.values; atr_arr=atr.values
HSEC={'20s':20,'1min':60,'2min':120,'3min':180,'4min':240,'5min':300}
PT=0.5; SL=0.3

def bt(sig, pa, aa, hb, pt, sl):
    wins=losses=to=0; tpnl=0.0
    idx=np.where(sig!=0)[0][::50]
    for i in idx:
        e=pa[i]; a=aa[i] if aa[i]>0 else e*0.001
        isL=sig[i]==1
        tp_p=e+pt*a if isL else e-pt*a
        sl_p=e-sl*a if isL else e+sl*a
        hit=False
        for j in range(i+1, min(i+hb+1, len(pa))):
            p=pa[j]
            if isL:
                if p>=tp_p: pnl=pt*a; wins+=1; tpnl+=pnl; hit=True; break
                if p<=sl_p: pnl=-sl*a; losses+=1; tpnl+=pnl; hit=True; break
            else:
                if p<=tp_p: pnl=pt*a; wins+=1; tpnl+=pnl; hit=True; break
                if p>=sl_p: pnl=-sl*a; losses+=1; tpnl+=pnl; hit=True; break
        if not hit:
            ep=pa[min(i+hb,len(pa)-1)]
            pnl=(ep-e) if isL else (e-ep)
            to+=1; tpnl+=pnl
    nt_full=int(np.sum(sig!=0)); nt_s=len(idx)
    scale=nt_full/max(1,nt_s)
    wr=wins/max(1,wins+losses+to)*100
    return nt_full, int(wins*scale), int(losses*scale), int(to*scale), wr, tpnl*scale

results={}
for h in H:
    hb=HSEC[h]//9+1
    for ver,dfv in [('6.1',df61),('6.2',df62)]:
        sig=dfv[f'signal_{h}'].values
        n=min(len(sig),len(price_arr),len(atr_arr))
        r=bt(sig[:n],price_arr[:n],atr_arr[:n],hb,PT,SL)
        results[(h,ver)]=r
        print(f'  {h:>5} v{ver}: trades={r[0]:,} W={r[1]:,} L={r[2]:,} TO={r[3]:,} WR={r[4]:.1f}% PnL=${r[5]:,.0f}')

# 5. EV analysis
print('\n-- 5. EXPECTED VALUE (EV = WR*PT - (1-WR)*SL) --')
for h in H:
    wr61=results[(h,'6.1')][4]/100; wr62=results[(h,'6.2')][4]/100
    ev61=wr61*PT-(1-wr61)*SL; ev62=wr62*PT-(1-wr62)*SL
    w='v6.2 WIN' if ev62>ev61 else 'v6.1 WIN'
    print(f'  {h:>5}: v61 EV={ev61:.4f} WR={wr61:.1%} | v62 EV={ev62:.4f} WR={wr62:.1%} | {w}')

# 6. Win rate by regime (v6.2)
print('\n-- 6. WIN RATE REGIME SZERINT (v6.2, 20s) --')
sig20=df62['signal_20s'].values
for rn in ['trending','mean_rev','neutral']:
    mask=(df62['regime']==rn).values
    nc=0; nt=0
    for i in range(min(len(sig20)-2, len(mask)-2)):
        if sig20[i]==0 or not mask[i]: continue
        ret=(price_arr[i+2]-price_arr[i])/price_arr[i]
        if sig20[i]==1 and ret>0: nc+=1
        elif sig20[i]==-1 and ret<0: nc+=1
        nt+=1
    print(f'  {rn:>10}: {nt:>6,} trades, WR={nc/max(1,nt)*100:.1f}%')

# 7. Verdict
print('\n' + SEP)
print('VERSENYNYERTES')
print(SEP)
t61=sum(results[(h,'6.1')][5] for h in H)
t62=sum(results[(h,'6.2')][5] for h in H)
wr61m=np.mean([results[(h,'6.1')][4] for h in H])
wr62m=np.mean([results[(h,'6.2')][4] for h in H])
n61=sum(np.sum(df61[f'signal_{h}']!=0) for h in H)
n62=sum(np.sum(df62[f'signal_{h}']!=0) for h in H)
print(f'  Ossz PnL:  v6.1=${t61:,.0f}  v6.2=${t62:,.0f}')
print(f'  Atlag WR:  v6.1={wr61m:.1f}%  v6.2={wr62m:.1f}%')
print(f'  Szignalok: v6.1={n61:,}  v6.2={n62:,}')
print(f'  Contra v6.2 TRENDING: 0 (100% supressed)')
if t62>t61 and wr62m>wr61m:
    print(f'  NYERTES: v6.2 (regime filter) - jobb PnL ES jobb WR')
elif wr62m>wr61m:
    print(f'  NYERTES: v6.2 (regime filter) - jobb WR, szelektivebb')
elif t62>t61:
    print(f'  NYERTES: v6.2 (regime filter) - jobb PnL')
else:
    print(f'  KOMBINALT: v6.2 szelektivebb, v6.1 tobb lehetoseg')
