#!/usr/bin/env python3
"""v6.2 horizon-ranking: melyik horizon áll a legjobban?"""
import numpy as np, pandas as pd
from pathlib import Path

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
v62f = sorted(MODEL_DIR.glob('BTCUSD_v6_preds_20261018_141912.csv'))
print("Loading v6.2..."); df = pd.read_csv(v62f[-1], index_col=0, parse_dates=True)
price = df['price'].values
H = ['20s','1min','2min','3min','4min','5min']
HSEC = {'20s':20,'1min':60,'2min':120,'3min':180,'4min':240,'5min':300}
BAR = 9; atr = (df['noise_level'] * df['price']).values
SEP = '=' * 90; metrics = {}

for h in H:
    sig = df[f'signal_{h}'].values
    pL = df[f'p_long_{h}'].fillna(0).values
    pS = df[f'p_short_{h}'].fillna(0).values
    hsec = HSEC[h]; hb = hsec // BAR + 1
    nL = int(np.sum(sig==1)); nS = int(np.sum(sig==-1)); n0 = int(np.sum(sig==0))
    n_total = nL + nS; noTrade_pct = n0/len(sig)*100

    # Direction accuracy
    dir_correct = 0; dir_total = 0
    dir2_correct = 0; dir2_total = 0
    for i in range(len(sig) - hb - 1):
        if sig[i] == 0: continue
        ret_h = (price[i+hb] - price[i]) / price[i]
        ret_2 = (price[i+2] - price[i]) / price[i]
        if sig[i]==1:
            if ret_h>0: dir_correct+=1
            if ret_2>0: dir2_correct+=1
        else:
            if ret_h<0: dir_correct+=1
            if ret_2<0: dir2_correct+=1
        dir_total+=1; dir2_total+=1
    dir_acc = dir_correct/max(1,dir_total)*100
    dir2_acc = dir2_correct/max(1,dir2_total)*100

    # Contra-trend
    td = df['trend_dir'].values
    contra = ((sig==-1)&(td>0))|((sig==1)&(td<0))
    n_contra = int(np.sum(contra)); contra_pct = n_contra/max(1,n_total)*100
    ret5 = pd.Series(price).pct_change(33); thr2=ret5.std()*2
    up_t=(ret5>thr2).values; dn_t=(ret5<-thr2).values
    strong_contra = int(np.sum((up_t&(sig==-1))|(dn_t&(sig==1))))
    n_strong = int(np.sum(up_t|dn_t))
    strong_contra_pct = strong_contra/max(1,n_strong)*100
    regime = df['regime'].values
    contra_trending = int(np.sum(contra&(regime=='trending')))
    contra_mr = int(np.sum(contra&(regime=='mean_rev')))
    contra_neutral = int(np.sum(contra&(regime=='neutral')))

    metrics[h] = dict(nL=nL,nS=nS,n0=n0,n_total=n_total,noTrade_pct=noTrade_pct,
        dir_acc=dir_acc,dir2_acc=dir2_acc,n_contra=n_contra,contra_pct=contra_pct,
        strong_contra=strong_contra,strong_contra_pct=strong_contra_pct,
        contra_trending=contra_trending,contra_mr=contra_mr,contra_neutral=contra_neutral)

    # Backtest
    PT, SL = 0.5, 0.3
    wins=losses=timeouts=0; tpnl=0.0
    indices = np.where(sig!=0)[0][::30]
    for i in indices:
        e=price[i]; a=atr[i] if atr[i]>0 else e*0.001; isL=sig[i]==1
        tp_p=e+PT*a if isL else e-PT*a; sl_p=e-SL*a if isL else e+SL*a; hit=False
        for j in range(i+1, min(i+hb+1, len(price))):
            p=price[j]
            if isL:
                if p>=tp_p: pnl=PT*a; wins+=1; tpnl+=pnl; hit=True; break
                if p<=sl_p: pnl=-SL*a; losses+=1; tpnl+=pnl; hit=True; break
            else:
                if p<=tp_p: pnl=PT*a; wins+=1; tpnl+=pnl; hit=True; break
                if p>=sl_p: pnl=-SL*a; losses+=1; tpnl+=pnl; hit=True; break
        if not hit:
            ep=price[min(i+hb,len(price)-1)]; pnl=(ep-e) if isL else (e-ep); timeouts+=1; tpnl+=pnl
    scale=n_total/max(1,len(indices))
    wr=wins/max(1,wins+losses+timeouts)*100; ev=(wr/100)*PT-(1-wr/100)*SL
    pnl_total=tpnl*scale; avg_pnl=tpnl/max(1,len(indices))
    pf_approx=(wins*PT)/max(1,losses*SL)

    # Avg confidence
    sig_conf=[]
    for i in range(len(sig)):
        if sig[i]==1: sig_conf.append(pL[i])
        elif sig[i]==-1: sig_conf.append(pS[i])
    avg_conf=np.mean(sig_conf) if sig_conf else 0

    # Sharpe
    pnl_list=[]
    for i in indices[:2000]:
        e=price[i]; a2=atr[i] if atr[i]>0 else e*0.001; isL=sig[i]==1
        ep=price[min(i+hb,len(price)-1)]; pnl_list.append((ep-e) if isL else (e-ep))
    sharpe=np.mean(pnl_list)/max(1e-10,np.std(pnl_list))*np.sqrt(252*24*3600/hsec)

    # Regime WR
    regime_wr={}
    for rn in ['trending','mean_rev','neutral']:
        mask=regime==rn; nc=0; nt=0
        for i in range(min(len(sig)-2, len(mask)-2)):
            if sig[i]==0 or not mask[i]: continue
            ret=(price[i+2]-price[i])/price[i]
            if sig[i]==1 and ret>0: nc+=1
            elif sig[i]==-1 and ret<0: nc+=1
            nt+=1
        regime_wr[rn]=(nc,nt,nc/max(1,nt)*100)

    metrics[h].update(dict(wr=wr,ev=ev,pnl_total=pnl_total,avg_pnl=avg_pnl,pf=pf_approx,
        avg_conf=avg_conf,regime_wr=regime_wr,sharpe=sharpe))

# ── PRINT RESULTS ──
print(SEP)
print('v6.2 HORIZON RANGSOR — RÉSZLETES ELEMZÉS')
print(SEP)

print('\n── 1. IRANY PONTOSAG ──')
print(f'{"Hor":>5} | {"DirAcc%":>8} | {"2bar%":>6} | {"Contra%":>8} | {"StrongCt%":>10} | {"CT_trend":>9} | {"CT_MR":>7} | {"CT_neut":>8}')
print('-'*80)
for h in H:
    m=metrics[h]
    print(f'{h:>5} | {m["dir_acc"]:>7.1f}% | {m["dir2_acc"]:>5.1f}% | {m["contra_pct"]:>7.1f}% | {m["strong_contra_pct"]:>9.1f}% | {m["contra_trending"]:>9,} | {m["contra_mr"]:>7,} | {m["contra_neutral"]:>8,}')

print('\n── 2. BACKTEST ──')
print(f'{"Hor":>5} | {"WR%":>6} | {"EV":>7} | {"PF":>6} | {"Sharpe":>8} | {"PnL$":>10} | {"AvgPnL$":>8} | {"Conf":>6}')
print('-'*65)
for h in H:
    m=metrics[h]
    print(f'{h:>5} | {m["wr"]:>5.1f}% | {m["ev"]:>6.4f} | {m["pf"]:>5.2f} | {m["sharpe"]:>7.2f} | ${m["pnl_total"]:>9,.0f} | ${m["avg_pnl"]:>6.2f} | {m["avg_conf"]:>5.3f}')

print('\n── 3. SZIGNAL SURUSEG ──')
print(f'{"Hor":>5} | {"Long":>8} | {"Short":>8} | {"NoTrade":>8} | {"NT%":>5} | {"L/S":>6}')
print('-'*50)
for h in H:
    m=metrics[h]; ls_r=m['nL']/max(1,m['nS'])
    print(f'{h:>5} | {m["nL"]:>8,} | {m["nS"]:>8,} | {m["n0"]:>8,} | {m["noTrade_pct"]:>4.1f}% | {ls_r:>5.2f}')

print('\n── 4. REGIME WIN RATE ──')
print(f'{"Hor":>5} | {"T_WR%":>6} {"T_n":>7} | {"MR_WR%":>7} {"MR_n":>8} | {"N_WR%":>6} {"N_n":>7}')
print('-'*55)
for h in H:
    m=metrics[h]; twr=m['regime_wr']['trending']; mwr=m['regime_wr']['mean_rev']; nwr=m['regime_wr']['neutral']
    print(f'{h:>5} | {twr[2]:>5.1f}% {twr[1]:>7,} | {mwr[2]:>6.1f}% {mwr[1]:>8,} | {nwr[2]:>5.1f}% {nwr[1]:>7,}')

# ── COMPOSITE RANKING ──
print('\n' + SEP)
print('KOMPOZIT PONTZAS & RANGSOR')
print(SEP)

def norm(val, vals, higher_better=True):
    mn,mx=min(vals),max(vals)
    if mx==mn: return 0.5
    n=(val-mn)/(mx-mn)
    return n if higher_better else 1-n

dir_accs=[metrics[h]['dir_acc'] for h in H]; wrs=[metrics[h]['wr'] for h in H]
evs=[metrics[h]['ev'] for h in H]; sharpes=[metrics[h]['sharpe'] for h in H]
contra_pcts=[metrics[h]['contra_pct'] for h in H]; strong_cts=[metrics[h]['strong_contra_pct'] for h in H]
notrades=[metrics[h]['noTrade_pct'] for h in H]; confs=[metrics[h]['avg_conf'] for h in H]
pfs=[metrics[h]['pf'] for h in H]

print(f'\n{"Hor":>5} | {"DirA":>5} | {"WR":>5} | {"EV":>5} | {"Shrp":>5} | {"Cntr":>5} | {"SCt":>5} | {"Szel":>5} | {"Conf":>5} | {"PF":>5} | {"OSSZ":>6}')
print('-'*65)
final={}
for h in H:
    m=metrics[h]
    s=norm(m['dir_acc'],dir_accs)*20 + norm(m['wr'],wrs)*15 + norm(m['ev'],evs)*15 + norm(m['sharpe'],sharpes)*10 + norm(m['contra_pct'],contra_pcts,False)*15 + norm(m['strong_contra_pct'],strong_cts,False)*10 + norm(m['noTrade_pct'],notrades,False)*5 + norm(m['avg_conf'],confs)*5 + norm(m['pf'],pfs)*5
    final[h]=s
    sd=norm(m['dir_acc'],dir_accs)*20; sw=norm(m['wr'],wrs)*15; se=norm(m['ev'],evs)*15
    ssh=norm(m['sharpe'],sharpes)*10; sc=norm(m['contra_pct'],contra_pcts,False)*15
    sct=norm(m['strong_contra_pct'],strong_cts,False)*10; snt=norm(m['noTrade_pct'],notrades,False)*5
    scf=norm(m['avg_conf'],confs)*5; spf=norm(m['pf'],pfs)*5
    print(f'{h:>5} | {sd:>4.1f} | {sw:>4.1f} | {se:>4.1f} | {ssh:>4.1f} | {sc:>4.1f} | {sct:>4.1f} | {snt:>4.1f} | {scf:>4.1f} | {spf:>4.1f} | {s:>5.1f}')

ranked=sorted(H, key=lambda h: final[h], reverse=True)
medal=['🥇','🥈','🥉','4.','5.','6.']
print(f'\n{"Rang":>4} | {"Horizon":>7} | {"Pont":>6} | {"DirAcc":>7} | {"WR":>5} | {"EV":>7} | {"Contra%":>8} | {"Sharpe":>7}')
print('-'*60)
for i,h in enumerate(ranked):
    m=metrics[h]
    print(f'{medal[i]:>4} | {h:>7} | {final[h]:>5.1f} | {m["dir_acc"]:>6.1f}% | {m["wr"]:>4.1f}% | {m["ev"]:>6.4f} | {m["contra_pct"]:>7.1f}% | {m["sharpe"]:>6.2f}')

print('\n'+SEP)
bm=metrics[ranked[0]]; wm=metrics[ranked[-1]]
print(f'LEGJOBB: {ranked[0]} — DirAcc={bm["dir_acc"]:.1f}% WR={bm["wr"]:.1f}% EV={bm["ev"]:.4f} Contra={bm["contra_pct"]:.1f}%')
print(f'LEGENGEBB: {ranked[-1]} — DirAcc={wm["dir_acc"]:.1f}% WR={wm["wr"]:.1f}% EV={wm["ev"]:.4f} Contra={wm["contra_pct"]:.1f}%')
print('Sulyozas: DirAcc=20% WR=15% EV=15% Contra=15% Sharpe=10% StrongCt=10% Szelekt=5% Conf=5% PF=5%')
